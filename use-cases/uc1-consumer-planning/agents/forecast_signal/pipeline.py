"""ForecastSignalBQAgent pipeline — detect deltas, write signal_delta."""

from __future__ import annotations

from google.cloud import bigquery

from . import bq_io, detection
from .models import ForecastSignalResult


def run_forecast_signal(
    client: bigquery.Client | None = None,
) -> ForecastSignalResult:
    client = client or bq_io.get_client()
    current = bq_io.fetch_current_metrics(client)

    if bq_io.seed_snapshot_if_empty(client, current):
        return ForecastSignalResult(
            deltas_written=0,
            snapshot_rows_updated=len(current),
            message="First run — snapshot seeded; no deltas until next run.",
        )

    prior_by_key = bq_io.fetch_snapshot_metrics(client)
    deltas = detection.detect_deltas(current, prior_by_key)
    written = bq_io.insert_signal_deltas(client, deltas)
    snapshot_count = bq_io.replace_snapshot(client, current)

    return ForecastSignalResult(
        deltas_written=written,
        deltas=deltas,
        snapshot_rows_updated=snapshot_count,
        message=f"Detected {written} signal delta(s).",
    )
