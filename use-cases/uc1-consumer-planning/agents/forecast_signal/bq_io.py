"""BigQuery reads/writes for ForecastSignalBQAgent."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery

from .config import FIRST_RUN_LOOKBACK_HOURS, TABLES
from .models import MetricRow, SignalDeltaRow


def get_client(project: str | None = None) -> bigquery.Client:
    from .config import GCP_PROJECT

    return bigquery.Client(project=project or GCP_PROJECT)


def fetch_last_completed_at(client: bigquery.Client) -> datetime | None:
    query = f"""
        SELECT MAX(completed_at) AS last_completed_at
        FROM `{TABLES["agent_run_history"]}`
        WHERE run_status = 'completed'
          AND completed_at IS NOT NULL
    """
    try:
        rows = list(client.query(query).result())
    except Exception:
        return None
    if not rows or rows[0]["last_completed_at"] is None:
        return None
    return rows[0]["last_completed_at"]


def fetch_current_metrics(client: bigquery.Client) -> list[MetricRow]:
    query = f"""
        SELECT
          cs.product_cd,
          cs.region,
          cs.week,
          COALESCE(cs.weighted_intent_score, 0) AS weighted_intent_score,
          COALESCE(df.units_forecast, 0) AS units_forecast,
          gr.region_canonical
        FROM `{TABLES["clickstream_agg"]}` AS cs
        LEFT JOIN `{TABLES["demand_forecast_base"]}` AS df
          ON cs.product_cd = df.product_cd
         AND cs.region = df.region
         AND cs.week = df.week
        LEFT JOIN `{TABLES["geo_region"]}` AS gr
          ON cs.region = gr.enterprise_region
         AND gr.source_system = 'OMS'
    """
    rows: list[MetricRow] = []
    for row in client.query(query).result():
        rows.append(
            MetricRow(
                product_cd=row["product_cd"],
                region=row["region"],
                week=row["week"],
                weighted_intent_score=float(row["weighted_intent_score"] or 0),
                units_forecast=float(row["units_forecast"] or 0),
                region_canonical=row.get("region_canonical") or row["region"],
            )
        )
    return rows


def fetch_snapshot_metrics(client: bigquery.Client) -> dict[tuple[str, str, str], MetricRow]:
    query = f"""
        SELECT product_cd, region, week, weighted_intent_score, units_forecast
        FROM `{TABLES["signal_delta_snapshot"]}`
    """
    try:
        job = client.query(query)
    except Exception:
        return {}
    out: dict[tuple[str, str, str], MetricRow] = {}
    for row in job.result():
        key = (row["product_cd"], row["region"], row["week"])
        out[key] = MetricRow(
            product_cd=row["product_cd"],
            region=row["region"],
            week=row["week"],
            weighted_intent_score=float(row["weighted_intent_score"] or 0),
            units_forecast=float(row["units_forecast"] or 0),
        )
    return out


def insert_signal_deltas(client: bigquery.Client, deltas: list[SignalDeltaRow]) -> int:
    if not deltas:
        return 0
    table_id = TABLES["signal_delta"]
    rows: list[dict[str, Any]] = []
    for d in deltas:
        rows.append(
            {
                "signal_delta_id": d.signal_delta_id,
                "product_cd": d.product_cd,
                "region": d.region,
                "region_canonical": d.region_canonical,
                "week": d.week,
                "delta_type": d.delta_type,
                "delta_magnitude": d.delta_magnitude,
                "source_table": d.source_table,
                "prior_value": d.prior_value,
                "current_value": d.current_value,
                "detected_at": d.detected_at,
            }
        )
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(f"signal_delta insert errors: {errors}")
    return len(rows)


def replace_snapshot(client: bigquery.Client, metrics: list[MetricRow]) -> int:
    if not metrics:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    snapshot_table = TABLES["signal_delta_snapshot"]
    client.query(f"TRUNCATE TABLE `{snapshot_table}`").result()
    rows = [
        {
            "product_cd": m.product_cd,
            "region": m.region,
            "week": m.week,
            "weighted_intent_score": m.weighted_intent_score,
            "units_forecast": m.units_forecast,
            "snapshot_at": now,
        }
        for m in metrics
    ]
    errors = client.insert_rows_json(snapshot_table, rows)
    if errors:
        raise RuntimeError(f"signal_delta_snapshot insert errors: {errors}")
    return len(rows)


def seed_snapshot_if_empty(client: bigquery.Client, metrics: list[MetricRow]) -> bool:
    """Return True if snapshot was empty and seeded (first run — no deltas expected)."""
    query = f"SELECT COUNT(*) AS n FROM `{TABLES['signal_delta_snapshot']}`"
    try:
        n = list(client.query(query).result())[0]["n"]
    except Exception:
        n = 0
    if n == 0 and metrics:
        replace_snapshot(client, metrics)
        return True
    return False
