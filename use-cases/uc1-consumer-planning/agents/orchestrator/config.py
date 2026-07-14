"""Configuration for OrchestratorAgent."""

from __future__ import annotations

GCP_PROJECT = "demandsensinglayer"
BQ_DATASET = "dsl_dataset"

FRESHNESS_MAX_HOURS = 2

AGENTS_EXECUTED = ["BQ", "ORCH"]

TABLES = {
    "clickstream_agg": f"{GCP_PROJECT}.{BQ_DATASET}.clickstream_agg",
    "demand_forecast_base": f"{GCP_PROJECT}.{BQ_DATASET}.demand_forecast_base",
    "member_hub": f"{GCP_PROJECT}.{BQ_DATASET}.member_hub",
    "geo_region": f"{GCP_PROJECT}.{BQ_DATASET}.geo_region",
    "signal_delta": f"{GCP_PROJECT}.{BQ_DATASET}.signal_delta",
    "agent_run_history": f"{GCP_PROJECT}.{BQ_DATASET}.agent_run_history",
}
