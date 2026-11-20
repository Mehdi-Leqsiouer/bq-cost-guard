from google.api_core.exceptions import GoogleAPICallError
from google.auth.exceptions import GoogleAuthError
from google.cloud import bigquery
from pydantic import BaseModel

TIB = 2**40


class Estimate(BaseModel):
    bytes_processed: int | None = None
    cost_usd: float | None = None
    error: str | None = None


def estimate(client: bigquery.Client, sql: str, price_per_tib: float) -> Estimate:
    """Dry-run `sql` and price it on-demand. Never raises on GCP/auth/syntax errors."""
    config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    try:
        job = client.query(sql, job_config=config)
    except (GoogleAPICallError, GoogleAuthError) as e:
        return Estimate(error=getattr(e, "message", None) or str(e))
    n = job.total_bytes_processed or 0
    return Estimate(bytes_processed=n, cost_usd=n / TIB * price_per_tib)
