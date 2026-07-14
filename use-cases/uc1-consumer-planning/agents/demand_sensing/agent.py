"""ADK Demand Sensing agent — reads Gold BQ tables, outputs recommendation envelope."""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .config import HERO_REGION, HERO_WEEKS
from .models import RunScope
from .pipeline import run_demand_sensing


def score_demand_scope(
    region: str = HERO_REGION,
    weeks: tuple[str, ...] = HERO_WEEKS,
    style_name_pattern: str = "%targhee%",
    product_cd: str | None = None,
) -> dict:
    """Run Demand Sensing for a SKU × region × week scope.

    Reads clickstream_agg, member_hub, and demand_forecast_base from BigQuery,
    applies glossary intent weights, and returns a recommendation envelope JSON.

    Args:
        region: Enterprise region name (e.g. Pacific NW).
        weeks: Retail weeks to score (e.g. 2026-W42 through 2026-W48).
        style_name_pattern: SQL LIKE pattern to resolve hero SKU when product_cd omitted.
        product_cd: Optional explicit product code; skips style lookup when set.

    Returns:
        Recommendation envelope with baseline vs adjusted forecast, drivers, and traceability.
    """
    scope = RunScope(
        product_cd=product_cd,
        style_name_pattern=style_name_pattern,
        region=region,
        weeks=weeks,
    )
    envelope = run_demand_sensing(scope=scope)
    return envelope.model_dump(mode="json")


root_agent = Agent(
    name="demand_sensing_agent",
    model="gemini-2.0-flash",
    description=(
        "UC1 Demand Sensing agent — reads clickstream_agg, member_hub, and "
        "demand_forecast_base; outputs intent_units_lift and recommendation envelope."
    ),
    instruction="""You are the Demand Sensing agent for UC1 demand planning.

Your job:
1. Read Gold tables (clickstream_agg, member_hub, demand_forecast_base) for a scope.
2. Apply intent scoring with glossary weights: search=0.2, pdp_view=0.4, wishlist=0.8, cart_add=1.0.
3. Return a recommendation envelope with intent_units_lift, units_intent_adjusted, drivers, and confidence_score.

When the user asks to score demand or run demand sensing, call score_demand_scope with the requested region and weeks.
Default hero demo scope: Targhee IV style, Pacific NW, weeks 2026-W42 through 2026-W48.

You do NOT build baseline forecasts, auto-apply adjustments, or answer free-form planner chat.
""",
    tools=[FunctionTool(score_demand_scope)],
)
