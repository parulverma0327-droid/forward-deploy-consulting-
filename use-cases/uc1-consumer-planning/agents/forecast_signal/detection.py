"""Delta detection logic for ForecastSignalBQAgent."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .config import BASELINE_DELTA_THRESHOLD, INTENT_DELTA_THRESHOLD
from .models import MetricRow, SignalDeltaRow


def _pct_change(prior: float, current: float) -> float:
    if prior == 0:
        return 1.0 if current > 0 else 0.0
    return abs(current - prior) / abs(prior)


def _classify_intent_delta(prior: float, current: float) -> str | None:
    change = _pct_change(prior, current)
    if change < INTENT_DELTA_THRESHOLD:
        return None
    return "intent_spike" if current > prior else "intent_drop"


def _classify_baseline_delta(prior: float, current: float) -> str | None:
    change = _pct_change(prior, current)
    if change < BASELINE_DELTA_THRESHOLD:
        return None
    return "baseline_shift"


def detect_deltas(
    current: list[MetricRow],
    prior_by_key: dict[tuple[str, str, str], MetricRow],
    detected_at: datetime | None = None,
) -> list[SignalDeltaRow]:
    ts = (detected_at or datetime.now(timezone.utc)).isoformat()
    deltas: list[SignalDeltaRow] = []

    for row in current:
        key = (row.product_cd, row.region, row.week)
        prior = prior_by_key.get(key)
        if not prior:
            continue
        region_canonical = row.region_canonical or row.region

        intent_type = _classify_intent_delta(prior.weighted_intent_score, row.weighted_intent_score)
        if intent_type:
            deltas.append(
                SignalDeltaRow(
                    signal_delta_id=f"sd_{uuid.uuid4().hex[:12]}",
                    product_cd=row.product_cd,
                    region=row.region,
                    region_canonical=region_canonical,
                    week=row.week,
                    delta_type=intent_type,
                    delta_magnitude=round(
                        _pct_change(prior.weighted_intent_score, row.weighted_intent_score),
                        4,
                    ),
                    source_table="clickstream_agg",
                    prior_value=prior.weighted_intent_score,
                    current_value=row.weighted_intent_score,
                    detected_at=ts,
                )
            )

        baseline_type = _classify_baseline_delta(prior.units_forecast, row.units_forecast)
        if baseline_type:
            deltas.append(
                SignalDeltaRow(
                    signal_delta_id=f"sd_{uuid.uuid4().hex[:12]}",
                    product_cd=row.product_cd,
                    region=row.region,
                    region_canonical=region_canonical,
                    week=row.week,
                    delta_type=baseline_type,
                    delta_magnitude=round(
                        _pct_change(prior.units_forecast, row.units_forecast),
                        4,
                    ),
                    source_table="demand_forecast_base",
                    prior_value=prior.units_forecast,
                    current_value=row.units_forecast,
                    detected_at=ts,
                )
            )

    return deltas
