"""InventoryPolicyAgent pipeline — demand + on-hand → safety stock / reorder."""

from __future__ import annotations

import math
import uuid

from google.cloud import bigquery

from . import bq_io
from .config import DEMAND_UPLIFT_EXCEPTION_RATIO, POLICY_RULE_VERSION, SAFETY_STOCK_FACTOR
from .models import DemandRow, InventoryPolicyResult, InventoryRecRow


def _compute_safety_stock(
    demand: DemandRow,
    location_type: str,
    lead_time_days: int,
) -> int:
    factor = SAFETY_STOCK_FACTOR.get(location_type, 0.15)
    weekly = max(demand.units_intent_adjusted, 0)
    confidence = min(max(demand.confidence_score, 0.0), 1.0)
    lead_weeks = max(lead_time_days, 1) / 7.0
    raw = weekly * confidence * factor * (1 + lead_weeks)
    return max(int(math.ceil(raw)), 1)


def _compute_reorder(
    safety_stock: int,
    units_intent_adjusted: int,
    units_on_hand: int,
    units_in_transit: int,
) -> int:
    horizon_demand = max(int(math.ceil(units_intent_adjusted / 4)), 0)
    need = safety_stock + horizon_demand - units_on_hand - units_in_transit
    return max(need, 0)


def _build_recommendations(
    run_id: str,
    demand_rows: list[DemandRow],
    client: bigquery.Client,
) -> list[InventoryRecRow]:
    recs: list[InventoryRecRow] = []
    seen: set[tuple[str, str]] = set()

    for demand in demand_rows:
        locations = bq_io.fetch_locations(client, demand.region_canonical)
        if not locations:
            continue

        for loc in locations:
            location_id = loc["location_id"]
            location_type = (loc.get("location_type") or "store").lower()
            key = (demand.sku_id, location_id)
            if key in seen:
                continue
            seen.add(key)

            inv = bq_io.fetch_inventory_position(client, demand.sku_id, location_id)
            units_on_hand = int(inv.get("units_on_hand") or 0)
            units_in_transit = int(inv.get("units_in_transit") or 0)
            lead_time_days = int(inv.get("lead_time_days") or 2)

            safety_stock = _compute_safety_stock(demand, location_type, lead_time_days)
            reorder_qty = _compute_reorder(
                safety_stock,
                demand.units_intent_adjusted,
                units_on_hand,
                units_in_transit,
            )
            uplift = (
                demand.units_historical > 0
                and demand.units_intent_adjusted
                > demand.units_historical * DEMAND_UPLIFT_EXCEPTION_RATIO
            )
            exception = units_on_hand < safety_stock or uplift

            inputs_used = {
                "product_cd": demand.product_cd,
                "week": demand.week,
                "region_canonical": demand.region_canonical,
                "location_type": location_type,
                "units_intent_adjusted": demand.units_intent_adjusted,
                "units_historical": demand.units_historical,
                "units_on_hand": units_on_hand,
                "units_in_transit": units_in_transit,
                "lead_time_days": lead_time_days,
                "confidence_score": demand.confidence_score,
            }

            recs.append(
                InventoryRecRow(
                    inventory_rec_id=f"inv_{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    sku_id=demand.sku_id,
                    location_id=location_id,
                    safety_stock_units=safety_stock,
                    exception_priority_flag=exception,
                    reorder_qty=reorder_qty,
                    policy_rule_version=POLICY_RULE_VERSION,
                    inputs_used=inputs_used,
                )
            )

    return recs


def run_inventory_policy(
    run_id: str | None = None,
    client: bigquery.Client | None = None,
) -> InventoryPolicyResult:
    """Read DS output (or scope fallback), apply policy, write inventory_recommendation."""
    client = client or bq_io.get_client()

    if run_id:
        run_row = bq_io.fetch_run_by_id(client, run_id)
        if not run_row:
            return InventoryPolicyResult(
                run_id=run_id,
                run_status="skipped",
                message=f"No agent_run_history row for run_id={run_id}.",
            )
        if run_row.get("run_status") != "completed" or not run_row.get("gates_passed"):
            return InventoryPolicyResult(
                run_id=run_id,
                run_status="skipped",
                message="Run not completed or gates failed — IP waits for successful Orch run.",
            )
    else:
        run_row = bq_io.fetch_latest_completed_run(client)
        if not run_row:
            return InventoryPolicyResult(
                run_id="",
                run_status="skipped",
                message="No completed Orchestrator run found.",
            )
        run_id = run_row["run_id"]

    demand_rows = bq_io.fetch_demand_for_run(client, run_id)
    if not demand_rows:
        return InventoryPolicyResult(
            run_id=run_id,
            run_status="skipped",
            message="No demand rows for run — need scope_json or demand_forecast_recommendation.",
        )

    recs = _build_recommendations(run_id, demand_rows, client)
    if not recs:
        return InventoryPolicyResult(
            run_id=run_id,
            run_status="skipped",
            message="No locations found for demand regions — run bq_inventory_policy_tables.sql.",
        )

    bq_io.insert_inventory_recommendations(client, recs)
    exceptions = sum(1 for r in recs if r.exception_priority_flag)
    return InventoryPolicyResult(
        run_id=run_id,
        run_status="completed",
        rows_written=len(recs),
        message=f"Wrote {len(recs)} inventory row(s); {exceptions} exception(s).",
    )
