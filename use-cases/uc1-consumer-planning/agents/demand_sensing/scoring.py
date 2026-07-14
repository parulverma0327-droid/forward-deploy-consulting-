"""Intent scoring and recommendation envelope builder."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from .config import DEFAULT_INTENT_TO_UNITS_FACTOR, INTENT_WEIGHTS, TABLES
from .models import (
    BaselineForecastRow,
    ClickstreamAggRow,
    IntentDriver,
    MemberContext,
    RecommendationEnvelope,
    TraceabilityItem,
    WeekRecommendation,
)


def compute_weighted_intent(row: ClickstreamAggRow) -> tuple[float, list[IntentDriver]]:
    """Recompute weighted intent from event counts using glossary weights."""
    event_counts = {
        "search": row.search_count,
        "pdp_view": row.pdp_view_count,
        "wishlist_add": row.wishlist_add_count,
        "cart_add": row.cart_add_count,
    }
    drivers: list[IntentDriver] = []
    total = 0.0
    for event_type, count in event_counts.items():
        weight = INTENT_WEIGHTS[event_type]
        weighted = count * weight
        total += weighted
        drivers.append(
            IntentDriver(
                signal="clickstream_intent",
                event_type=event_type,
                count=count,
                weight=weight,
                weighted_score=weighted,
                share_pct=0.0,
            )
        )
    if total > 0:
        for driver in drivers:
            driver.share_pct = round(driver.weighted_score / total * 100, 1)
    return total, drivers


def compute_intent_to_units_factor(
    baseline_rows: list[BaselineForecastRow],
    clickstream_rows: list[ClickstreamAggRow],
) -> float:
    baseline_by_key = {(r.product_cd, r.region, r.week): r for r in baseline_rows}
    ratios: list[float] = []
    for cs in clickstream_rows:
        key = (cs.product_cd, cs.region, cs.week)
        baseline = baseline_by_key.get(key)
        if not baseline:
            continue
        weighted, _ = compute_weighted_intent(cs)
        if weighted > 0:
            ratios.append(baseline.units_forecast / weighted)
    if not ratios:
        return DEFAULT_INTENT_TO_UNITS_FACTOR
    return sum(ratios) / len(ratios)


def compute_confidence(
    weighted_intent_score: float,
    member_intent_count: int,
    guest_intent_count: int,
) -> float:
    total_intent = member_intent_count + guest_intent_count
    guest_share = guest_intent_count / total_intent if total_intent else 0.5
    score = (weighted_intent_score / 1000.0) * (1.0 - guest_share)
    return round(min(1.0, max(0.0, score)), 2)


def build_week_recommendations(
    baseline_rows: list[BaselineForecastRow],
    clickstream_rows: list[ClickstreamAggRow],
    region_canonical: str,
    intent_to_units_factor: float,
) -> list[WeekRecommendation]:
    cs_by_week = {r.week: r for r in clickstream_rows}
    recommendations: list[WeekRecommendation] = []

    for baseline in baseline_rows:
        cs = cs_by_week.get(baseline.week)
        if not cs:
            weighted_intent = 0.0
            drivers: list[IntentDriver] = []
            member_intent = 0
            guest_intent = 0
            top_query = None
        else:
            weighted_intent, drivers = compute_weighted_intent(cs)
            member_intent = cs.member_intent_count
            guest_intent = cs.guest_intent_count
            top_query = cs.top_search_query

        intent_lift = int(round(weighted_intent * intent_to_units_factor))
        adjusted = baseline.units_forecast + intent_lift
        confidence = compute_confidence(weighted_intent, member_intent, guest_intent)

        recommendations.append(
            WeekRecommendation(
                week=baseline.week,
                product_cd=baseline.product_cd,
                sku_id=baseline.sku_id,
                region=baseline.region,
                region_canonical=region_canonical,
                units_historical=baseline.units_forecast,
                weighted_intent_score=round(weighted_intent, 2),
                intent_units_lift=intent_lift,
                units_intent_adjusted=adjusted,
                confidence_score=confidence,
                drivers=drivers,
                top_search_query=top_query,
            )
        )
    return recommendations


def build_envelope(
    week_recs: list[WeekRecommendation],
    product_cd: str,
    region_canonical: str,
    member_context: MemberContext,
    run_id: str | None = None,
) -> RecommendationEnvelope:
    if not week_recs:
        raise ValueError("No week recommendations to envelope")

    baseline_total = sum(w.units_historical for w in week_recs)
    adjusted_total = sum(w.units_intent_adjusted for w in week_recs)
    intent_lift_total = sum(w.intent_units_lift for w in week_recs)
    avg_confidence = round(
        sum(w.confidence_score for w in week_recs) / len(week_recs),
        2,
    )

    weeks_sorted = sorted(w.week for w in week_recs)
    first_week = week_recs[0]
    valid_from = first_week.week_start_dt or date.today().isoformat()
    valid_to = (date.fromisoformat(valid_from) + timedelta(days=6)).isoformat() if first_week.week_start_dt else valid_from

    driver_weights: dict[str, float] = {}
    for week in week_recs:
        for driver in week.drivers:
            driver_weights[driver.event_type] = driver_weights.get(driver.event_type, 0.0) + driver.weighted_score
    total_driver_score = sum(driver_weights.values()) or 1.0

    traceability = [
        TraceabilityItem(
            signal="clickstream_intent",
            weight=round(sum(driver_weights.values()) / total_driver_score, 2),
            source_table=TABLES["clickstream_agg"],
            detail="Intent weights: search=0.2, pdp_view=0.4, wishlist=0.8, cart_add=1.0",
        ),
        TraceabilityItem(
            signal="member_context",
            weight=round(member_context.high_value_member_count / max(member_context.member_count, 1), 2),
            source_table=TABLES["member_hub"],
            detail=f"{member_context.high_value_member_count} high-value members in scope",
        ),
    ]

    sku = week_recs[0].sku_id.replace("SKU-", "STY-") if week_recs[0].sku_id.startswith("SKU-") else week_recs[0].sku_id

    return RecommendationEnvelope(
        recommendation_id=f"rec-{uuid.uuid4()}",
        run_id=run_id or f"run_ds_{uuid.uuid4().hex[:8]}",
        geo_scope={"region": region_canonical, "enterprise_region": week_recs[0].region},
        sku=sku,
        product_cd=product_cd,
        signal_window={
            "weeks": weeks_sorted,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "decay_days": 5,
        },
        baseline_forecast=baseline_total,
        adjusted_forecast=adjusted_total,
        delta_units=adjusted_total - baseline_total,
        intent_units_lift=intent_lift_total,
        confidence=avg_confidence,
        traceability=traceability,
        week_details=week_recs,
    )
