from pathlib import Path

import pytest

from bq_cost_guard.linter import lint

FIX = Path(__file__).parent / "fixtures"


def rules(sql: str, ignore=None) -> list[str]:
    return [i.rule for i in lint(sql, ignore)]


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("good.sql", []),
        ("select_star.sql", ["BQ001"]),
        ("order_by_no_limit.sql", ["BQ002"]),
        ("cross_join.sql", ["BQ003"]),
        ("implicit_join.sql", ["BQ003"]),
        ("wildcard_no_suffix.sql", ["BQ004"]),
        ("cte_reused.sql", ["BQ005"]),
        ("limit_no_where.sql", ["BQ006"]),
    ],
)
def test_fixtures(fixture, expected):
    assert rules((FIX / fixture).read_text()) == expected


def test_count_star_is_fine():
    assert rules("SELECT COUNT(*) FROM t") == []


def test_top_level_order_by_ok_and_limit_ok():
    assert rules("SELECT a FROM t ORDER BY a") == []
    assert rules("SELECT a FROM (SELECT a FROM t ORDER BY a LIMIT 5)") == []


def test_window_order_by_ok():
    assert rules("SELECT ROW_NUMBER() OVER (ORDER BY a) FROM t") == []


def test_cross_join_with_where_or_unnest_ok():
    assert rules("SELECT 1 FROM a CROSS JOIN b WHERE a.x = b.x") == []
    assert rules("SELECT 1 FROM t, UNNEST(t.arr) AS x") == []
    assert rules("SELECT 1 FROM t CROSS JOIN UNNEST(t.arr) AS x") == []
    assert rules("SELECT 1 FROM a LEFT JOIN b ON a.x = b.x") == []


def test_ignore_and_syntax_error():
    assert rules("SELECT * FROM t", ["BQ001"]) == []
    assert rules("SELEC FROM FROM (") == []


def test_new_rules_negative_cases():
    assert rules("SELECT a FROM `p.d.e_*` WHERE _TABLE_SUFFIX BETWEEN '1' AND '2'") == []
    assert rules("WITH c AS (SELECT a FROM t) SELECT a FROM c") == []
    assert rules("WITH c AS (SELECT 1 AS a) SELECT x.a FROM c AS x JOIN c AS y ON x.a = y.a") == []
    assert rules("SELECT a FROM t WHERE d = '1' LIMIT 10") == []
    assert rules("SELECT a FROM (SELECT a FROM t LIMIT 5) ORDER BY a") == []
