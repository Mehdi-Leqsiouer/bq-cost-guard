import sqlglot
from pydantic import BaseModel
from sqlglot import exp
from sqlglot.errors import SqlglotError

MESSAGES = {
    "BQ001": "SELECT * scans every column; list only the columns you need.",
    "BQ002": "ORDER BY without LIMIT in a subquery/CTE is wasted work.",
    "BQ003": "Cross join without a WHERE filter can explode row counts.",
    "BQ004": "Wildcard table without a _TABLE_SUFFIX filter scans every shard.",
    "BQ005": "A CTE referenced more than once may be computed (and its tables scanned) once per reference.",
    "BQ006": "LIMIT does not reduce bytes billed; add a WHERE on a partition column instead.",
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


def _tree_rules(tree: exp.Expression) -> set[str]:
    rules: set[str] = set()
    tables = list(tree.find_all(exp.Table))
    if any(t.name.endswith("*") for t in tables) and not any(
        c.name.upper() == "_TABLE_SUFFIX" for c in tree.find_all(exp.Column)
    ):
        rules.add("BQ004")
    for cte in tree.find_all(exp.CTE):
        refs = [t for t in tables if t.name == cte.alias and not t.db]
        if len(refs) > 1 and cte.this.find(exp.Table):
            rules.add("BQ005")
    from_ = tree.args.get("from_") or tree.args.get("from")  # key renamed across sqlglot versions
    if isinstance(tree, exp.Select) and tree.args.get("limit") and from_ and isinstance(from_.this, exp.Table):
        if not any(tree.args.get(k) for k in ("where", "group", "having", "qualify", "order", "joins")):
            rules.add("BQ006")
    return rules


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
        rules |= _tree_rules(tree)
    return [Issue(rule=r, message=MESSAGES[r]) for r in sorted(rules - set(ignore or []))]
