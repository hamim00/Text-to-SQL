from __future__ import annotations

from dataclasses import dataclass
import re

import sqlglot
from sqlglot import exp


@dataclass(frozen=True)
class SafeSQLResult:
    sql: str
    limit_added: bool


class SQLSafetyError(ValueError):
    pass


def extract_sql_candidate(text: str) -> str:
    """Extract SQL from common LLM response formats."""
    if not text:
        return ""
    t = text.strip()

    # Strip ```sql ... ```
    if t.startswith("```"):
        t = re.sub(r"^```(?:sql)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
        t = t.strip()

    # Strip "SQL:" / "Query:"
    t = re.sub(r"^(sql\s*:|query\s*:)", "", t, flags=re.IGNORECASE).strip()

    # Jump to first SELECT/WITH if there's leading explanation
    m = re.search(r"\b(SELECT|WITH)\b", t, flags=re.IGNORECASE)
    if m and m.start() > 0:
        t = t[m.start():].strip()

    # Keep only first statement if semicolon exists
    semi = t.find(";")
    if semi != -1:
        t = t[: semi + 1].strip()

    return t


def _is_select_statement(tree: exp.Expression) -> bool:
    if isinstance(tree, exp.Select):
        return True
    if isinstance(tree, exp.With):
        return isinstance(tree.this, (exp.Select, exp.Union, exp.Intersect, exp.Except))
    if isinstance(tree, (exp.Union, exp.Intersect, exp.Except)):
        return True
    return False


def _strip_trailing_semicolons(sql: str) -> str:
    return re.sub(r";+\s*$", "", sql.strip())


def _has_top_level_limit(sql_no_sc: str) -> bool:
    # LIMIT at the end (optionally OFFSET)
    return bool(
        re.search(r"\bLIMIT\b\s+\d+\s*(?:\bOFFSET\b\s+\d+\s*)?$", sql_no_sc, flags=re.IGNORECASE)
    )


def validate_and_rewrite_select(sql: str, *, dialect: str = "sqlite", default_limit: int = 100) -> SafeSQLResult:
    candidate = extract_sql_candidate(sql)
    if not candidate:
        raise SQLSafetyError("Empty SQL produced by provider.")

    # Validate: parse & single statement
    try:
        statements = sqlglot.parse(candidate, read=dialect)
    except Exception as e:
        raise SQLSafetyError(f"SQL parse error: {e}") from e

    if len(statements) != 1:
        raise SQLSafetyError("Only a single SQL statement is allowed.")

    tree = statements[0]
    if tree is None:
        raise SQLSafetyError("SQL parse produced no statement.")

    if not _is_select_statement(tree):
        raise SQLSafetyError("Only SELECT queries are allowed.")

    # Enforce LIMIT by string editing (avoid sqlglot AST serialization quirks)
    s = _strip_trailing_semicolons(candidate)
    limit_added = False

    # Repair common truncation: query ends with LIMIT (no number)
    if re.search(r"\bLIMIT\b\s*$", s, flags=re.IGNORECASE):
        s = re.sub(r"\bLIMIT\b\s*$", f"LIMIT {default_limit}", s, flags=re.IGNORECASE)
        limit_added = True

    # If no top-level LIMIT, append one
    if not _has_top_level_limit(s) and not re.search(r"\bLIMIT\b\s+\d+", s, flags=re.IGNORECASE):
        s = f"{s} LIMIT {default_limit}"
        limit_added = True

    safe_sql = s.strip()
    if not safe_sql.endswith(";"):
        safe_sql += ";"

    return SafeSQLResult(sql=safe_sql, limit_added=limit_added)
