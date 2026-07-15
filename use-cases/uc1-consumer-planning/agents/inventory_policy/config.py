"""Configuration for InventoryPolicyAgent."""

from __future__ import annotations

GCP_PROJECT = "demandsensinglayer"
BQ_DATASET = "dsl_dataset"

POLICY_RULE_VERSION = "inv_policy_v1"

# Demo: flag exception when adjusted demand exceeds baseline by this ratio
DEMAND_UPLIFT_EXCEPTION_RATIO = 1.15

# Location-type multipliers for safety stock buffer
SAFETY_STOCK_FACTOR = {
    "store": 0.15,
    "dc": 0.25,
}

TABLES = {
    "agent_run_history": f"{GCP_PROJECT}.{BQ_DATASET}.agent_run_history",
    "demand_forecast_recommendation": f"{GCP_PROJECT}.{BQ_DATASET}.demand_forecast_recommendation",
    "demand_forecast_base": f"{GCP_PROJECT}.{BQ_DATASET}.demand_forecast_base",
    "geo_region": f"{GCP_PROJECT}.{BQ_DATASET}.geo_region",
    "replacement_score": f"{GCP_PROJECT}.{BQ_DATASET}.replacement_score",
    "location": f"{GCP_PROJECT}.{BQ_DATASET}.location",
    "inventory_position": f"{GCP_PROJECT}.{BQ_DATASET}.inventory_position",
    "inventory_recommendation": f"{GCP_PROJECT}.{BQ_DATASET}.inventory_recommendation",
}
