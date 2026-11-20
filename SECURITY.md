# Security Policy

## Supported versions

Only the latest release receives security fixes.

## Reporting a vulnerability

Please do **not** open a public issue. Use GitHub's private reporting instead:
[Report a vulnerability](https://github.com/Mehdi-Leqsiouer/bq-cost-guard/security/advisories/new).

Expect an acknowledgement within a few days.

## Scope notes

`bq-cost-guard` only performs BigQuery **dry runs** (no data is read or written) and only needs
`roles/bigquery.jobUser` and `roles/bigquery.dataViewer`. Never grant it broader permissions, and never
commit service account keys; prefer Workload Identity Federation in CI.
