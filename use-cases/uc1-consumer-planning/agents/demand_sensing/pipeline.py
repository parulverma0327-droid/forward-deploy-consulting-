"""Demand Sensing pipeline — read Gold tables, score, return envelope."""

from __future__ import annotations

from google.cloud import bigquery

from . import bq_reader, scoring
from .config import HERO_REGION, HERO_WEEKS
from .models import RecommendationEnvelope, RunScope


def run_demand_sensing(
    scope: RunScope | None = None,
    client: bigquery.Client | None = None,
    run_id: str | None = None,
) -> RecommendationEnvelope:
    """Execute Demand Sensing for a scope and return the recommendation envelope."""
    scope = scope or RunScope(region=HERO_REGION, weeks=HERO_WEEKS)
    client = client or bq_reader.get_client()

    product_cd = bq_reader.resolve_product_cd(client, scope)
    region = scope.region
    weeks = scope.weeks

    clickstream = bq_reader.fetch_clickstream_agg(client, product_cd, region, weeks)
    baseline = bq_reader.fetch_baseline_forecast(client, product_cd, region, weeks)
    member_context = bq_reader.fetch_member_context(client, region)
    region_canonical = bq_reader.fetch_region_canonical(client, region)

    if not baseline:
        raise ValueError(
            f"No baseline forecast rows for product_cd={product_cd}, region={region}, weeks={weeks}"
        )

    intent_factor = scoring.compute_intent_to_units_factor(baseline, clickstream)
    week_recs = scoring.build_week_recommendations(
        baseline,
        clickstream,
        region_canonical,
        intent_factor,
    )
    return scoring.build_envelope(
        week_recs,
        product_cd=product_cd,
        region_canonical=region_canonical,
        member_context=member_context,
        run_id=run_id,
    )
