"""ADK Orchestrator agent — gates, scope routing, agent_run_history."""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .pipeline import run_orchestrator


def run_hourly_orchestration() -> dict:
    """Run OrchestratorAgent: read signal_delta, pass gates, write agent_run_history."""
    result = run_orchestrator()
    return result.model_dump(mode="json")


root_agent = Agent(
    name="orchestrator_agent",
    model="gemini-2.0-flash",
    description=(
        "UC1 Orchestrator agent — reads signal_delta, runs freshness gates, "
        "builds scope_json, writes agent_run_history, routes specialist agents."
    ),
    instruction="""You are the Orchestrator agent for UC1.

Your job:
1. Run freshness gates on Clickstream Agg, DemandForecast_Base, Member Hub.
2. Read signal_delta written by ForecastSignalBQAgent.
3. Build scope_json and write agent_run_history with run_id.

When asked to orchestrate or run the hourly loop, call run_hourly_orchestration.

You do NOT detect signal deltas (ForecastSignalBQAgent) or invoke DS/RC/IP.
""",
    tools=[FunctionTool(run_hourly_orchestration)],
)
