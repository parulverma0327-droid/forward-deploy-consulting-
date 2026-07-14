"""ADK Forecast & Signal BQ agent — detects changes, writes signal_delta."""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .pipeline import run_forecast_signal


def detect_signal_deltas() -> dict:
    """Run ForecastSignalBQAgent: compare Gold metrics vs snapshot, write signal_delta."""
    result = run_forecast_signal()
    return result.model_dump(mode="json")


root_agent = Agent(
    name="forecast_signal_bq_agent",
    model="gemini-2.0-flash",
    description=(
        "UC1 Forecast & Signal BQ agent — detects intent and baseline changes on Gold "
        "tables and writes signal_delta for OrchestratorAgent."
    ),
    instruction="""You are the Forecast & Signal BQ agent for UC1.

Your job:
1. Compare current Clickstream Agg and DemandForecast_Base metrics to the prior snapshot.
2. Write changed scopes to signal_delta (intent_spike, intent_drop, baseline_shift).
3. Update signal_delta_snapshot for the next run.

When asked to detect signals or refresh signal_delta, call detect_signal_deltas.

You do NOT issue run_id, route specialists, or publish recommendations.
""",
    tools=[FunctionTool(detect_signal_deltas)],
)
