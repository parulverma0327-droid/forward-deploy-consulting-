"""BigQuery reads/writes for OrchestratorAgent."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery

from .config import FRESHNESS_MAX_HOURS, TABLES
from .models import ScopeItem


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


def fetch_signal_deltas_since(
    client: bigquery.Client,
    since: datetime | None,
) -> list[dict[str, Any]]:
    if since:
        query = f"""
            SELECT product_cd, region, region_canonical, week, delta_type, detected_at, source_table
            FROM `{TABLES["signal_delta"]}`
            WHERE detected_at > @since
            ORDER BY detected_at DESC
        """
        params = [bigquery.ScalarQueryParameter("since", "TIMESTAMP", since)]
    else:
        query = f"""
            SELECT product_cd, region, region_canonical, week, delta_type, detected_at, source_table
            FROM `{TABLES["signal_delta"]}`
            WHERE detected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
            ORDER BY detected_at DESC
        """
        params = []
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(query_parameters=params) if params else None,
    )
    return [dict(row.items()) for row in job.result()]


def fetch_sku_for_product(
    client: bigquery.Client,
    product_cd: str,
    region: str,
    week: str,
) -> str | None:
    query = f"""
        SELECT sku_id
        FROM `{TABLES["demand_forecast_base"]}`
        WHERE product_cd = @product_cd
          AND region = @region
          AND week = @week
        LIMIT 1
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("product_cd", "STRING", product_cd),
                bigquery.ScalarQueryParameter("region", "STRING", region),
                bigquery.ScalarQueryParameter("week", "STRING", week),
            ]
        ),
    )
    rows = list(job.result())
    if rows:
        return rows[0]["sku_id"]
    return f"SKU-{product_cd}"


def check_freshness_gates(client: bigquery.Client) -> tuple[bool, dict[str, bool], list[str]]:
    checks: dict[str, bool] = {}
    messages: list[str] = []

    cs_query = f"""
        SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(last_updated_dt), HOUR) AS hours_stale
        FROM `{TABLES["clickstream_agg"]}`
    """
    df_query = f"""
        SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(last_updated_dt), HOUR) AS hours_stale
        FROM `{TABLES["demand_forecast_base"]}`
    """
    mh_query = f"""
        SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ds_model_refresh_dt), HOUR) AS hours_stale
        FROM `{TABLES["member_hub"]}`
    """

    for name, query in [
        ("clickstream_agg", cs_query),
        ("demand_forecast_base", df_query),
        ("member_hub", mh_query),
    ]:
        try:
            hours = list(client.query(query).result())[0]["hours_stale"]
            ok = hours is not None and hours <= FRESHNESS_MAX_HOURS
        except Exception as exc:
            ok = False
            messages.append(f"{name}: check failed ({exc})")
            checks[name] = ok
            continue
        checks[name] = ok
        if not ok:
            messages.append(f"{name}: stale ({hours}h > {FRESHNESS_MAX_HOURS}h)")

    passed = all(checks.values()) if checks else False
    return passed, checks, messages


def build_scope_from_deltas(
    client: bigquery.Client,
    delta_rows: list[dict[str, Any]],
) -> list[ScopeItem]:
    seen: set[tuple[str, str, str]] = set()
    scope: list[ScopeItem] = []
    for row in delta_rows:
        key = (row["product_cd"], row["region"], row["week"])
        if key in seen:
            continue
        seen.add(key)
        sku_id = fetch_sku_for_product(client, row["product_cd"], row["region"], row["week"])
        scope.append(
            ScopeItem(
                product_cd=row["product_cd"],
                sku_id=sku_id or f"SKU-{row['product_cd']}",
                region=row["region"],
                region_canonical=row.get("region_canonical") or row["region"],
                week=row["week"],
            )
        )
    return scope


def insert_run_history(
    client: bigquery.Client,
    run_id: str,
    run_status: str,
    gates_passed: bool,
    scope: list[ScopeItem],
    agents_executed: list[str],
    started_at: datetime,
    completed_at: datetime | None,
) -> None:
    scope_json = json.dumps([s.model_dump() for s in scope])
    agents_json = json.dumps(agents_executed)
    row = {
        "run_id": run_id,
        "run_status": run_status,
        "gates_passed": gates_passed,
        "scope_json": scope_json,
        "agents_executed": agents_json,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat() if completed_at else None,
    }
    errors = client.insert_rows_json(TABLES["agent_run_history"], [row])
    if errors:
        raise RuntimeError(f"agent_run_history insert errors: {errors}")
