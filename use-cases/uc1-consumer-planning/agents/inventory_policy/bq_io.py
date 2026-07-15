"""BigQuery reads/writes for InventoryPolicyAgent."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery

from .config import TABLES
from .models import DemandRow, InventoryRecRow


def get_client(project: str | None = None) -> bigquery.Client:
    from .config import GCP_PROJECT

    return bigquery.Client(project=project or GCP_PROJECT)


def fetch_latest_completed_run(client: bigquery.Client) -> dict[str, Any] | None:
    query = f"""
        SELECT run_id, scope_json, gates_passed, completed_at
        FROM `{TABLES["agent_run_history"]}`
        WHERE run_status = 'completed'
          AND gates_passed = TRUE
          AND completed_at IS NOT NULL
        ORDER BY completed_at DESC
        LIMIT 1
    """
    try:
        rows = list(client.query(query).result())
    except Exception:
        return None
    return dict(rows[0]) if rows else None


def fetch_run_by_id(client: bigquery.Client, run_id: str) -> dict[str, Any] | None:
    query = f"""
        SELECT run_id, scope_json, gates_passed, run_status
        FROM `{TABLES["agent_run_history"]}`
        WHERE run_id = @run_id
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("run_id", "STRING", run_id)]
    )
    rows = list(client.query(query, job_config=job_config).result())
    return dict(rows[0]) if rows else None


def fetch_demand_for_run(client: bigquery.Client, run_id: str) -> list[DemandRow]:
    query = f"""
        SELECT
          run_id,
          product_cd,
          sku_id,
          region_canonical,
          week,
          units_historical,
          units_intent_adjusted,
          confidence_score
        FROM `{TABLES["demand_forecast_recommendation"]}`
        WHERE run_id = @run_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("run_id", "STRING", run_id)]
    )
    try:
        rows = list(client.query(query, job_config=job_config).result())
    except Exception:
        rows = []

    if rows:
        return [_row_to_demand(dict(r)) for r in rows]

    return fetch_demand_from_scope(client, run_id)


def fetch_demand_from_scope(client: bigquery.Client, run_id: str) -> list[DemandRow]:
    """Fallback when DS has not written demand_forecast_recommendation yet."""
    run_row = fetch_run_by_id(client, run_id)
    if not run_row or not run_row.get("scope_json"):
        return []

    scope = json.loads(run_row["scope_json"])
    demand: list[DemandRow] = []
    for item in scope:
        product_cd = item.get("product_cd") or ""
        sku_id = item.get("sku_id") or f"SKU-{product_cd}"
        region_canonical = item.get("region_canonical") or item.get("region") or ""
        week = item.get("week") or ""
        baseline = fetch_baseline_units(
            client, product_cd=product_cd, region_canonical=region_canonical, week=week
        )
        demand.append(
            DemandRow(
                run_id=run_id,
                product_cd=product_cd,
                sku_id=sku_id,
                region_canonical=region_canonical,
                week=week,
                units_historical=baseline,
                units_intent_adjusted=baseline,
                confidence_score=0.5,
            )
        )
    return demand


def fetch_baseline_units(
    client: bigquery.Client,
    product_cd: str,
    region_canonical: str,
    week: str,
) -> int:
    query = f"""
        SELECT CAST(ROUND(AVG(df.units_forecast)) AS INT64) AS units
        FROM `{TABLES["demand_forecast_base"]}` AS df
        LEFT JOIN `{TABLES["geo_region"]}` AS gr
          ON df.region = gr.enterprise_region
        WHERE df.product_cd = @product_cd
          AND df.week = @week
          AND (
            gr.region_canonical = @region_canonical
            OR df.region = @region_canonical
          )
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("product_cd", "STRING", product_cd),
            bigquery.ScalarQueryParameter("region_canonical", "STRING", region_canonical),
            bigquery.ScalarQueryParameter("week", "STRING", week),
        ]
    )
    try:
        rows = list(client.query(query, job_config=job_config).result())
        if rows and rows[0]["units"] is not None:
            return int(rows[0]["units"])
    except Exception:
        pass
    return 0


def fetch_locations(client: bigquery.Client, region_canonical: str) -> list[dict[str, Any]]:
    query = f"""
        SELECT location_id, location_type, region_canonical, parent_dc_id
        FROM `{TABLES["location"]}`
        WHERE region_canonical = @region_canonical
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("region_canonical", "STRING", region_canonical)
        ]
    )
    try:
        return [dict(r) for r in client.query(query, job_config=job_config).result()]
    except Exception:
        return []


def fetch_inventory_position(
    client: bigquery.Client,
    sku_id: str,
    location_id: str,
) -> dict[str, Any]:
    query = f"""
        SELECT location_id, sku_id, units_on_hand, units_in_transit, lead_time_days
        FROM `{TABLES["inventory_position"]}`
        WHERE sku_id = @sku_id
          AND location_id = @location_id
        ORDER BY snapshot_dt DESC
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("sku_id", "STRING", sku_id),
            bigquery.ScalarQueryParameter("location_id", "STRING", location_id),
        ]
    )
    try:
        rows = list(client.query(query, job_config=job_config).result())
        if rows:
            return dict(rows[0])
    except Exception:
        pass
    loc_type = "store" if location_id.startswith("STORE") else "dc"
    return {
        "location_id": location_id,
        "sku_id": sku_id,
        "units_on_hand": 0,
        "units_in_transit": 0,
        "lead_time_days": 2 if loc_type == "store" else 5,
    }


def insert_inventory_recommendations(
    client: bigquery.Client,
    rows: list[InventoryRecRow],
) -> None:
    if not rows:
        return
    payload = []
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        payload.append(
            {
                "inventory_rec_id": row.inventory_rec_id,
                "run_id": row.run_id,
                "sku_id": row.sku_id,
                "location_id": row.location_id,
                "safety_stock_units": row.safety_stock_units,
                "exception_priority_flag": row.exception_priority_flag,
                "reorder_qty": row.reorder_qty,
                "policy_rule_version": row.policy_rule_version,
                "inputs_used": json.dumps(row.inputs_used),
                "last_updated_dt": now,
            }
        )
    errors = client.insert_rows_json(TABLES["inventory_recommendation"], payload)
    if errors:
        raise RuntimeError(f"inventory_recommendation insert errors: {errors}")


def _row_to_demand(row: dict[str, Any]) -> DemandRow:
    return DemandRow(
        run_id=row["run_id"],
        product_cd=row.get("product_cd") or "",
        sku_id=row.get("sku_id") or "",
        region_canonical=row.get("region_canonical") or "",
        week=row.get("week") or "",
        units_historical=int(row.get("units_historical") or 0),
        units_intent_adjusted=int(row.get("units_intent_adjusted") or 0),
        confidence_score=float(row.get("confidence_score") or 0.5),
    )
