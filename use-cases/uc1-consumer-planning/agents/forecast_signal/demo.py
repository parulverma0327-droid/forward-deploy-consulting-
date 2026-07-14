"""Demo helper — perturb snapshot so next run detects intent_spike on hero SKU."""

from __future__ import annotations

from google.cloud import bigquery

from .config import TABLES


def perturb_snapshot_for_demo(
    client: bigquery.Client,
    product_cd: str,
    factor: float = 0.75,
) -> int:
    """Lower snapshot weighted_intent for product_cd so current Gold reads as a spike."""
    query = f"""
        UPDATE `{TABLES["signal_delta_snapshot"]}`
        SET weighted_intent_score = weighted_intent_score * @factor
        WHERE product_cd = @product_cd
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("factor", "FLOAT64", factor),
                bigquery.ScalarQueryParameter("product_cd", "STRING", product_cd),
            ]
        ),
    )
    job.result()
    return job.num_dml_affected_rows or 0
