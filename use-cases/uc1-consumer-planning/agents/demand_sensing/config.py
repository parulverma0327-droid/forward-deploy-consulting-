"""Configuration for UC1 Demand Sensing agent."""

from __future__ import annotations

GCP_PROJECT = "demandsensinglayer"
BQ_DATASET = "dsl_dataset"

INTENT_WEIGHTS: dict[str, float] = {
    "search": 0.2,
    "pdp_view": 0.4,
    "wishlist_add": 0.8,
    "cart_add": 1.0,
    "category_browse": 0.3,
}

DEFAULT_INTENT_TO_UNITS_FACTOR = 0.019

HERO_STYLE_PATTERN = "%targhee%"
HERO_REGION = "Pacific NW"
HERO_REGION_CANONICAL = "US-PNW"
HERO_WEEKS = ("2026-W42", "2026-W43", "2026-W44", "2026-W45", "2026-W46", "2026-W47", "2026-W48")

TABLES = {
    "clickstream_agg": f"{GCP_PROJECT}.{BQ_DATASET}.clickstream_agg",
    "member_hub": f"{GCP_PROJECT}.{BQ_DATASET}.member_hub",
    "demand_forecast_base": f"{GCP_PROJECT}.{BQ_DATASET}.demand_forecast_base",
    "product_global_line_plan": f"{GCP_PROJECT}.{BQ_DATASET}.product_global_line_plan",
    "geo_region": f"{GCP_PROJECT}.{BQ_DATASET}.geo_region",
}
