"""BigQuery reads for Demand Sensing agent inputs."""

from __future__ import annotations

from typing import Any

from google.cloud import bigquery

from .config import GCP_PROJECT, HERO_STYLE_PATTERN, TABLES
from .models import BaselineForecastRow, ClickstreamAggRow, MemberContext, RunScope


def get_client(project: str = GCP_PROJECT) -> bigquery.Client:
    return bigquery.Client(project=project)


def _rows_to_dicts(job: bigquery.table.RowIterator) -> list[dict[str, Any]]:
    return [dict(row.items()) for row in job]


def resolve_product_cd(
    client: bigquery.Client,
    scope: RunScope,
) -> str:
    if scope.product_cd:
        return scope.product_cd
    pattern = scope.style_name_pattern or HERO_STYLE_PATTERN
    query = f"""
        SELECT product_code AS product_cd
        FROM `{TABLES["product_global_line_plan"]}`
        WHERE LOWER(style_name) LIKE LOWER(@pattern)
        LIMIT 1
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("pattern", "STRING", pattern)]
        ),
    )
    rows = list(job.result())
    if not rows:
        raise ValueError(f"No product found for style pattern: {pattern}")
    return rows[0]["product_cd"]


def fetch_clickstream_agg(
    client: bigquery.Client,
    product_cd: str,
    region: str,
    weeks: tuple[str, ...],
) -> list[ClickstreamAggRow]:
    query = f"""
        SELECT
          product_cd,
          region,
          week,
          CAST(week_start_dt AS STRING) AS week_start_dt,
          search_count,
          pdp_view_count,
          wishlist_add_count,
          cart_add_count,
          weighted_intent_score,
          member_intent_count,
          guest_intent_count,
          top_search_query
        FROM `{TABLES["clickstream_agg"]}`
        WHERE product_cd = @product_cd
          AND region = @region
          AND week IN UNNEST(@weeks)
        ORDER BY week
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("product_cd", "STRING", product_cd),
                bigquery.ScalarQueryParameter("region", "STRING", region),
                bigquery.ArrayQueryParameter("weeks", "STRING", list(weeks)),
            ]
        ),
    )
    return [ClickstreamAggRow.model_validate(row) for row in _rows_to_dicts(job)]


def fetch_baseline_forecast(
    client: bigquery.Client,
    product_cd: str,
    region: str,
    weeks: tuple[str, ...],
) -> list[BaselineForecastRow]:
    query = f"""
        SELECT
          product_cd,
          sku_id,
          region,
          week,
          CAST(week_start_dt AS STRING) AS week_start_dt,
          season_code,
          category,
          units_forecast
        FROM `{TABLES["demand_forecast_base"]}`
        WHERE product_cd = @product_cd
          AND region = @region
          AND week IN UNNEST(@weeks)
        ORDER BY week
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("product_cd", "STRING", product_cd),
                bigquery.ScalarQueryParameter("region", "STRING", region),
                bigquery.ArrayQueryParameter("weeks", "STRING", list(weeks)),
            ]
        ),
    )
    return [BaselineForecastRow.model_validate(row) for row in _rows_to_dicts(job)]


def fetch_member_context(
    client: bigquery.Client,
    region: str,
) -> MemberContext:
    query = f"""
        SELECT
          COUNT(*) AS member_count,
          COUNTIF(membership_tier = 'High Value') AS high_value_member_count,
          AVG(
            SAFE_DIVIDE(
              visit_count_12m,
              NULLIF(visit_count_12m + 1, 0)
            )
          ) AS avg_member_intent_share
        FROM `{TABLES["member_hub"]}`
        WHERE region = @region OR preferred_retail_geo = @region
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("region", "STRING", region)]
        ),
    )
    rows = list(job.result())
    if not rows:
        return MemberContext()
    row = rows[0]
    return MemberContext(
        member_count=int(row.get("member_count") or 0),
        high_value_member_count=int(row.get("high_value_member_count") or 0),
        avg_member_intent_share=float(row.get("avg_member_intent_share") or 0.5),
    )


def fetch_region_canonical(client: bigquery.Client, enterprise_region: str) -> str:
    query = f"""
        SELECT region_canonical
        FROM `{TABLES["geo_region"]}`
        WHERE enterprise_region = @region
          AND source_system = 'OMS'
        LIMIT 1
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("region", "STRING", enterprise_region)]
        ),
    )
    rows = list(job.result())
    if not rows:
        return enterprise_region
    return rows[0]["region_canonical"]
