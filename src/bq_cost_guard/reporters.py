import json
from typing import Literal

from pydantic import BaseModel
from rich.table import Table

from .linter import Issue

Status = Literal["ok", "warn", "fail", "error"]
EMOJI = {"ok": "✅", "warn": "⚠️", "fail": "❌", "error": "❌"}


class FileResult(BaseModel):
    path: str
    status: Status = "ok"
    bytes_processed: int | None = None
    cost_usd: float | None = None
    issues: list[Issue] = []
    error: str | None = None


def human_bytes(n: int | None) -> str:
    if n is None:
        return "-"
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    raise AssertionError("unreachable")


def _cost(c: float | None) -> str:
    return "-" if c is None else f"${c:,.4f}"


def total_cost(results: list[FileResult]) -> float:
    return sum(r.cost_usd or 0.0 for r in results)


def render_table(results: list[FileResult]) -> Table:
    table = Table(title="bq-cost-guard", caption=f"Total estimated cost: {_cost(total_cost(results))}")
    for col in ("", "File", "Processed", "Est. cost", "Notes"):
        table.add_column(col)
    for r in results:
        notes = [f"{i.rule}: {i.message}" for i in r.issues] + ([r.error] if r.error else [])
        table.add_row(
            EMOJI[r.status], r.path, human_bytes(r.bytes_processed), _cost(r.cost_usd),
            "\n".join(notes),
        )  # fmt: skip
    return table


def render_markdown(results: list[FileResult]) -> str:
    lines = [
        "## BigQuery cost report",
        "",
        "| Status | File | Processed | Est. cost |",
        "|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {EMOJI[r.status]} | `{r.path}` | {human_bytes(r.bytes_processed)} | {_cost(r.cost_usd)} |")
    lines += ["", f"**Total estimated cost: {_cost(total_cost(results))}**"]
    warnings = [f"- `{r.path}` **{i.rule}**: {i.message}" for r in results for i in r.issues]
    warnings += [f"- `{r.path}` error: {r.error}" for r in results if r.error]
    if warnings:
        lines += ["", "### Warnings", *warnings]
    return "\n".join(lines) + "\n"


def render_json(results: list[FileResult]) -> str:
    return json.dumps(
        {"total_cost_usd": total_cost(results), "files": [r.model_dump() for r in results]},
        indent=2,
    )
