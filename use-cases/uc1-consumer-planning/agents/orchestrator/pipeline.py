"""OrchestratorAgent pipeline — gates, read signal_delta, route scope."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from google.cloud import bigquery

from . import bq_io
from .config import AGENTS_EXECUTED
from .models import OrchestratorResult


def _new_run_id() -> str:
    now = datetime.now(timezone.utc)
    return f"run_{now.strftime('%Y%m%d_%H%M')}_{uuid.uuid4().hex[:8]}"


def run_orchestrator(client: bigquery.Client | None = None) -> OrchestratorResult:
    """Run Orchestrator: gates → signal_delta → scope_json → agent_run_history."""
    client = client or bq_io.get_client()
    run_id = _new_run_id()
    started_at = datetime.now(timezone.utc)
    agents_executed = list(AGENTS_EXECUTED)

    gates_passed, _, gate_messages = bq_io.check_freshness_gates(client)
    if not gates_passed:
        bq_io.insert_run_history(
            client,
            run_id=run_id,
            run_status="skipped",
            gates_passed=False,
            scope=[],
            agents_executed=agents_executed,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        return OrchestratorResult(
            run_id=run_id,
            run_status="skipped",
            gates_passed=False,
            message="; ".join(gate_messages) or "Freshness gates failed.",
        )

    last_completed = bq_io.fetch_last_completed_at(client)
    delta_rows = bq_io.fetch_signal_deltas_since(client, last_completed)
    scope = bq_io.build_scope_from_deltas(client, delta_rows)

    if not scope:
        bq_io.insert_run_history(
            client,
            run_id=run_id,
            run_status="skipped",
            gates_passed=True,
            scope=[],
            agents_executed=agents_executed,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        return OrchestratorResult(
            run_id=run_id,
            run_status="skipped",
            gates_passed=True,
            message="No signal_delta rows since last completed run.",
        )

    completed_at = datetime.now(timezone.utc)
    bq_io.insert_run_history(
        client,
        run_id=run_id,
        run_status="completed",
        gates_passed=True,
        scope=scope,
        agents_executed=agents_executed,
        started_at=started_at,
        completed_at=completed_at,
    )

    return OrchestratorResult(
        run_id=run_id,
        run_status="completed",
        gates_passed=True,
        scope=scope,
        agents_executed=agents_executed,
        message=f"Routed {len(scope)} scope(s).",
    )
