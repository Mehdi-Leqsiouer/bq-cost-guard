from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from google.auth.exceptions import GoogleAuthError
from google.cloud import bigquery
from rich.console import Console

from . import reporters
from .bq_estimator import estimate
from .config import Config, load_config
from .dbt_parser import compiled_models, is_dbt_project
from .git_utils import changed_files
from .linter import lint

app = typer.Typer(add_completion=False, help="Estimate BigQuery cost and lint SQL anti-patterns.")


class Format(StrEnum):
    table = "table"
    markdown = "markdown"
    json = "json"


def collect(path: Path, git_diff: str | None) -> dict[str, Path]:
    """Return {display_name: sql_file_to_analyze}."""
    if path.is_file():
        return {str(path): path}
    changed = changed_files(git_diff, path) if git_diff else None
    if is_dbt_project(path):
        files = compiled_models(path)  # {source: compiled}
    else:
        files = {p.resolve(): p for p in path.rglob("*.sql")}
    if changed is not None:
        files = {src: sql for src, sql in files.items() if src in changed}
    return {str(src.relative_to(path.resolve())) if src.is_relative_to(path.resolve()) else str(src): sql
            for src, sql in sorted(files.items())}  # fmt: skip


def classify(r: reporters.FileResult, cfg: Config) -> reporters.Status:
    if r.error:
        return "error"
    if r.cost_usd is not None and r.cost_usd > cfg.fail_cost_usd:
        return "fail"
    if r.issues or (r.cost_usd is not None and r.cost_usd > cfg.warn_cost_usd):
        return "warn"
    return "ok"


@app.command()
def main(
    path: Annotated[Path, typer.Argument(exists=True, help=".sql file, folder or dbt project")],
    fmt: Annotated[Format, typer.Option("--format", help="Output format")] = Format.table,
    git_diff: Annotated[str | None, typer.Option(help="Only analyze files changed vs this base branch")] = None,
    config: Annotated[Path | None, typer.Option(help="Path to .bqcostguard.yaml")] = None,
    project: Annotated[str | None, typer.Option(help="GCP project for the dry run")] = None,
    skip_estimate: Annotated[bool, typer.Option(help="Lint only, no BigQuery call")] = False,
) -> None:
    cfg = load_config(config)
    client, auth_error = None, None
    if not skip_estimate:
        try:
            client = bigquery.Client(project=project)
        except GoogleAuthError as e:
            auth_error = f"GCP authentication failed: {e}"

    results = []
    for name, file in collect(path, git_diff).items():
        sql = file.read_text()
        r = reporters.FileResult(path=name, issues=lint(sql, cfg.ignore_rules), error=auth_error)
        if client:
            est = estimate(client, sql, cfg.price_per_tib)
            r.bytes_processed, r.cost_usd, r.error = est.bytes_processed, est.cost_usd, est.error
        r.status = classify(r, cfg)
        results.append(r)

    match fmt:
        case Format.table:
            Console().print(reporters.render_table(results))
        case Format.markdown:
            typer.echo(reporters.render_markdown(results))
        case Format.json:
            typer.echo(reporters.render_json(results))
    raise typer.Exit(1 if any(r.status == "fail" for r in results) else 0)
