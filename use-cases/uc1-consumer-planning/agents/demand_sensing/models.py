"""Pydantic models for Demand Sensing inputs and recommendation envelope."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RunScope(BaseModel):
    """Grain scope for a demand sensing run."""

    product_cd: str | None = None
    style_name_pattern: str | None = None
    region: str = "Pacific NW"
    weeks: tuple[str, ...] = Field(default_factory=tuple)


class ClickstreamAggRow(BaseModel):
    product_cd: str
    region: str
    week: str
    week_start_dt: str | None = None
    search_count: int = 0
    pdp_view_count: int = 0
    wishlist_add_count: int = 0
    cart_add_count: int = 0
    weighted_intent_score: float = 0.0
    member_intent_count: int = 0
    guest_intent_count: int = 0
    top_search_query: str | None = None


class BaselineForecastRow(BaseModel):
    product_cd: str
    sku_id: str
    region: str
    week: str
    week_start_dt: str | None = None
    season_code: str | None = None
    category: str | None = None
    units_forecast: int


class MemberContext(BaseModel):
    member_count: int = 0
    high_value_member_count: int = 0
    avg_member_intent_share: float = 0.5


class IntentDriver(BaseModel):
    signal: str
    event_type: str
    count: int
    weight: float
    weighted_score: float
    share_pct: float


class TraceabilityItem(BaseModel):
    signal: str
    weight: float
    source_table: str
    detail: str | None = None


class WeekRecommendation(BaseModel):
    week: str
    product_cd: str
    sku_id: str
    region: str
    region_canonical: str
    units_historical: int
    weighted_intent_score: float
    intent_units_lift: int
    units_intent_adjusted: int
    confidence_score: float
    drivers: list[IntentDriver]
    top_search_query: str | None = None


class RecommendationEnvelope(BaseModel):
    recommendation_type: str = "forecast_adjustment"
    recommendation_id: str
    agent: str = "DemandSensingAgent"
    run_id: str
    geo_scope: dict[str, Any]
    sku: str
    product_cd: str
    signal_window: dict[str, Any]
    baseline_forecast: int
    adjusted_forecast: int
    delta_units: int
    intent_units_lift: int
    confidence: float
    traceability: list[TraceabilityItem]
    week_details: list[WeekRecommendation]
    status: str = "pending"
