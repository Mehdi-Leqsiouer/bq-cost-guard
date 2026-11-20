# bq-cost-guard

Know what a query will cost **before** it is merged. `bq-cost-guard` runs a BigQuery dry run on your SQL
(raw files or compiled dbt models), flags costly anti-patterns, and comments the result on your pull request.

```text
## BigQuery cost report

| Status | File | Processed | Est. cost |
|---|---|---|---|
| ❌ | `models/marts/events.sql` | 2.4 TiB | $15.2461 |
| ✅ | `models/marts/users.sql` | 4.9 MiB | $0.0000 |

**Total estimated cost: $15.2461**

### Warnings
- `models/marts/events.sql` **BQ001**: SELECT * scans every column; list only the columns you need.
```

## Install

```bash
pip install bq-cost-guard   # or: uvx bq-cost-guard
```

## Usage

```bash
bq-cost-guard query.sql --project my-gcp-project
bq-cost-guard ./dbt_project --git-diff origin/main --format markdown   # run `dbt compile` first
bq-cost-guard ./sql --skip-estimate                                    # lint only, no GCP call
```

| Option | Description |
|---|---|
| `--format table\|markdown\|json` | Output format (default `table`) |
| `--git-diff <base>` | Only analyze files changed vs. `<base>` |
| `--project` | GCP project used for the dry run |
| `--config` | Path to `.bqcostguard.yaml` |
| `--skip-estimate` | Lint only |

Exit codes: `0` ok, `1` a query exceeds `fail_cost_usd`, `2` an estimation failed (auth, syntax, no project).
Dry runs are free and scan no data.

## GitHub Action

```yaml
name: bq-cost-guard
on: pull_request
permissions:
  contents: read
  id-token: write
  pull-requests: write
jobs:
  cost:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ vars.WIF_PROVIDER }}
          service_account: ${{ vars.WIF_SERVICE_ACCOUNT }}
      - uses: Mehdi-Leqsiouer/bq-cost-guard@v0.1.0
        with:
          path: .
          base: origin/${{ github.base_ref }}
          project: my-gcp-project
```

The service account needs `roles/bigquery.jobUser` and `roles/bigquery.dataViewer` on the queried datasets.

## Configuration

Copy `.bqcostguard.yaml.example` to `.bqcostguard.yaml`:

```yaml
price_per_tib: 6.25   # USD per TiB (on-demand)
warn_cost_usd: 1.0
fail_cost_usd: 10.0
ignore_rules: []      # e.g. [BQ002]
```

## Rules

| Rule | Detects |
|---|---|
| `BQ001` | `SELECT *` |
| `BQ002` | `ORDER BY` without `LIMIT` in a subquery or CTE |
| `BQ003` | `CROSS JOIN` / implicit comma join without a `WHERE` |
| `BQ004` | Wildcard table (`events_*`) without a `_TABLE_SUFFIX` filter |
| `BQ005` | CTE referenced more than once that reads a table |
| `BQ006` | `LIMIT` without `WHERE` (does not reduce bytes billed) |

## Development

```bash
uv sync
uv run pytest
pre-commit install
```

MIT licensed.
