from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import sqlglot
from sqlglot import exp

@dataclass(frozen=True)
class SafeSQLResult:
    sql: str
    limit_added: bool

class SQLSafetyError(ValueError):
    pass

def _is_select_statement(tree: exp.Expression) -> bool:
    # Accept SELECT or WITH ... SELECT
    if isinstance(tree, exp.Select):
        return True
    if isinstance(tree, exp.With):
        # WITH ... followed by SELECT/UNION etc.
        return isinstance(tree.this, (exp.Select, exp.Union, exp.Intersect, exp.Except))
    if isinstance(tree, (exp.Union, exp.Intersect, exp.Except)):
        return True
    return False

def validate_and_rewrite_select(sql: str, *, dialect: str = "sqlite", default_limit: int = 100) -> SafeSQLResult:
    if not sql or not sql.strip():
        raise SQLSafetyError("Empty SQL produced by provider.")

    # Block multi-statement by parsing all statements.
    try:
        statements = sqlglot.parse(sql, read=dialect)
    except Exception as e:
        raise SQLSafetyError(f"SQL parse error: {e}") from e

    if len(statements) != 1:
        raise SQLSafetyError("Only a single SQL statement is allowed.")

    tree = statements[0]

    if not _is_select_statement(tree):
        raise SQLSafetyError("Only SELECT queries are allowed.")

    # Enforce LIMIT if absent at top level.
    limit_added = False
    top = tree
    # If WITH, apply limit to the final query
    if isinstance(top, exp.With):
        top_query = top.this
    else:
        top_query = top

    # Find existing LIMIT
    has_limit = bool(top_query.args.get("limit"))
    if not has_limit:
        top_query.set("limit", exp.Limit(this=exp.Literal.number(default_limit)))
        limit_added = True

    safe_sql = tree.sql(dialect=dialect)
    return SafeSQLResult(sql=safe_sql, limit_added=limit_added)
