"""Pydantic models for OrchestratorAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScopeItem(BaseModel):
    product_cd: str
    sku_id: str
    region: str
    region_canonical: str
    week: str


class GateResult(BaseModel):
    passed: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)


class OrchestratorResult(BaseModel):
    agent: str = "OrchestratorAgent"
    run_id: str
    run_status: str
    gates_passed: bool
    scope: list[ScopeItem] = Field(default_factory=list)
    agents_executed: list[str] = Field(default_factory=list)
    message: str = ""
