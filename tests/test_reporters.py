import json

from typer.testing import CliRunner

from bq_cost_guard import cli
from bq_cost_guard.bq_estimator import TIB, Estimate
from bq_cost_guard.linter import Issue
from bq_cost_guard.reporters import FileResult, render_json, render_markdown, render_table

RESULTS = [
    FileResult(path="a.sql", bytes_processed=2**30, cost_usd=0.5),
    FileResult(path="b.sql", status="warn", cost_usd=1.5, issues=[Issue(rule="BQ001", message="star")]),
    FileResult(path="c.sql", status="error", error="boom"),
]


def test_markdown():
    md = render_markdown(RESULTS)
    assert "✅" in md and "⚠️" in md and "❌" in md
    assert "**Total estimated cost: $2.0000**" in md
    assert "**BQ001**" in md and "boom" in md


def test_json():
    data = json.loads(render_json(RESULTS))
    assert data["total_cost_usd"] == 2.0 and len(data["files"]) == 3


def test_table():
    assert render_table(RESULTS).row_count == 3


def test_cli_exit_code(mocker, tmp_path):
    (tmp_path / "q.sql").write_text("SELECT a FROM t")
    mocker.patch.object(cli.bigquery, "Client")
    mock_est = mocker.patch.object(cli, "estimate")
    runner = CliRunner()

    mock_est.return_value = Estimate(bytes_processed=TIB, cost_usd=6.25)
    assert runner.invoke(cli.app, [str(tmp_path), "--format", "json"]).exit_code == 0

    mock_est.return_value = Estimate(bytes_processed=2 * TIB, cost_usd=12.5)
    assert runner.invoke(cli.app, [str(tmp_path), "--format", "json"]).exit_code == 1
