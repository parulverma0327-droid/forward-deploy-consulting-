"""Pydantic models for ForecastSignalBQAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MetricRow(BaseModel):
    product_cd: str
    region: str
    week: str
    weighted_intent_score: float = 0.0
    units_forecast: float = 0.0
    region_canonical: str | None = None


class SignalDeltaRow(BaseModel):
    signal_delta_id: str
    product_cd: str
    region: str
    region_canonical: str
    week: str
    delta_type: str
    delta_magnitude: float
    source_table: str
    prior_value: float
    current_value: float
    detected_at: str


class ForecastSignalResult(BaseModel):
    agent: str = "ForecastSignalBQAgent"
    deltas_written: int = 0
    deltas: list[SignalDeltaRow] = Field(default_factory=list)
    snapshot_rows_updated: int = 0
    message: str = ""
