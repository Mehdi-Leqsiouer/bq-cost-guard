# bq-cost-guard

Estimate BigQuery query cost (dry run) and lint FinOps anti-patterns before merge.

```bash
uv sync
uv run bq-cost-guard path/to/query.sql
uv run bq-cost-guard ./dbt_project --git-diff origin/main --format markdown
```

- Input: a `.sql` file, a folder, or a dbt project (reads `target/manifest.json` / `target/compiled/`).
- `--format table|markdown|json`, `--skip-estimate` (lint only, no GCP call), `--project <gcp_project>`.
- Exit code `1` if any query exceeds `fail_cost_usd`. Config: see `.bqcostguard.yaml.example`.
- Rules: `BQ001` SELECT *, `BQ002` ORDER BY without LIMIT in subquery/CTE, `BQ003` cross join without filter.
