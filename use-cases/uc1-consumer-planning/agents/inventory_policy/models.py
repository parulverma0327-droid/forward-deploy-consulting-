"""Pydantic models for InventoryPolicyAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DemandRow(BaseModel):
    run_id: str
    product_cd: str
    sku_id: str
    region_canonical: str
    week: str
    units_historical: int = 0
    units_intent_adjusted: int = 0
    confidence_score: float = 0.5


class InventoryRecRow(BaseModel):
    inventory_rec_id: str
    run_id: str
    sku_id: str
    location_id: str
    safety_stock_units: int
    exception_priority_flag: bool
    reorder_qty: int
    policy_rule_version: str
    inputs_used: dict


class InventoryPolicyResult(BaseModel):
    agent: str = "InventoryPolicyAgent"
    run_id: str
    run_status: str
    rows_written: int = 0
    message: str = ""
