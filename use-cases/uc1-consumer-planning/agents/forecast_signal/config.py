"""Configuration for ForecastSignalBQAgent."""

from __future__ import annotations

GCP_PROJECT = "demandsensinglayer"
BQ_DATASET = "dsl_dataset"

INTENT_DELTA_THRESHOLD = 0.15
BASELINE_DELTA_THRESHOLD = 0.10
FIRST_RUN_LOOKBACK_HOURS = 24
FRESHNESS_MAX_HOURS = 2

TABLES = {
    "clickstream_agg": f"{GCP_PROJECT}.{BQ_DATASET}.clickstream_agg",
    "demand_forecast_base": f"{GCP_PROJECT}.{BQ_DATASET}.demand_forecast_base",
    "member_hub": f"{GCP_PROJECT}.{BQ_DATASET}.member_hub",
    "geo_region": f"{GCP_PROJECT}.{BQ_DATASET}.geo_region",
    "agent_run_history": f"{GCP_PROJECT}.{BQ_DATASET}.agent_run_history",
    "signal_delta": f"{GCP_PROJECT}.{BQ_DATASET}.signal_delta",
    "signal_delta_snapshot": f"{GCP_PROJECT}.{BQ_DATASET}.signal_delta_snapshot",
}
