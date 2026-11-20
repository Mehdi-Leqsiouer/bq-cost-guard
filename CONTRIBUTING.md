# Contributing

Thanks for helping out! Issues and pull requests are welcome.

## Setup

```bash
uv sync
pre-commit install   # ruff, ruff-format and pytest on commit
uv run pytest
```

All BigQuery calls must be mocked in unit tests (no network, no credentials).

## Adding a lint rule

1. Add the message to `MESSAGES` and the check to `lint()` in `src/bq_cost_guard/linter.py`.
2. Add a fixture in `tests/fixtures/` and cases (positive and negative) in `tests/test_linter.py`.
3. Document the rule in the README table.

## Pull requests

- Keep them small and focused; one change per PR.
- Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).
- Code, comments and commit messages in English.
- CI (`ruff` + `pytest`) must pass.
