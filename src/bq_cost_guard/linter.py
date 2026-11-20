import sqlglot
from pydantic import BaseModel
from sqlglot import exp
from sqlglot.errors import SqlglotError

MESSAGES = {
    "BQ001": "SELECT * scans every column; list only the columns you need.",
    "BQ002": "ORDER BY without LIMIT in a subquery/CTE is wasted work.",
    "BQ003": "Cross join without a WHERE filter can explode row counts.",
}


class Issue(BaseModel):
    rule: str
    message: str


def _is_star(e: exp.Expression) -> bool:
    return isinstance(e, exp.Star) or (isinstance(e, exp.Column) and isinstance(e.this, exp.Star))


def _is_cross(j: exp.Join) -> bool:
    # `FROM a, b` parses as a join with no kind/condition; correlated UNNEST is legitimate.
    if isinstance(j.this, exp.Unnest) or j.args.get("on") or j.args.get("using"):
        return False
    return j.kind == "CROSS" or (not j.kind and not j.side and not j.method)


def lint(sql: str, ignore: list[str] | None = None) -> list[Issue]:
    """Static FinOps checks. Unparseable SQL yields no issues (the dry run reports syntax errors)."""
    try:
        trees = [t for t in sqlglot.parse(sql, dialect="bigquery") if t]
    except SqlglotError:
        return []
    rules: set[str] = set()
    for tree in trees:
        for select in tree.find_all(exp.Select):
            if any(_is_star(e) for e in select.expressions):
                rules.add("BQ001")
            if select.args.get("order") and not select.args.get("limit") and select.parent:
                rules.add("BQ002")
            if not select.args.get("where") and any(_is_cross(j) for j in select.args.get("joins") or []):
                rules.add("BQ003")
    return [Issue(rule=r, message=MESSAGES[r]) for r in sorted(rules - set(ignore or []))]
