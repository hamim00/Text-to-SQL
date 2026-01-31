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
    """Extract SQL from common LLM response formats (no multi-statement truncation)."""
    if not text:
        return ""
    t = text.strip()

    if t.startswith("```"):
        t = re.sub(r"^```(?:sql)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
        t = t.strip()

    t = re.sub(r"^(sql\s*:|query\s*:)", "", t, flags=re.IGNORECASE).strip()

    m = re.search(r"\b(SELECT|WITH)\b", t, flags=re.IGNORECASE)
    if m and m.start() > 0:
        t = t[m.start():].strip()

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
    return bool(
        re.search(r"\bLIMIT\b\s+\d+\s*(?:\bOFFSET\b\s+\d+\s*)?$", sql_no_sc, flags=re.IGNORECASE)
    )


def validate_and_rewrite_select(sql: str, *, dialect: str = "sqlite", default_limit: int = 100) -> SafeSQLResult:
    candidate = extract_sql_candidate(sql)
    if not candidate:
        raise SQLSafetyError("Empty SQL produced by provider.")

    s = candidate.strip()
    s_no_trailing = _strip_trailing_semicolons(s)
    if ";" in s_no_trailing:
        raise SQLSafetyError("Multiple statements detected (semicolon in the middle).")

    try:
        statements = sqlglot.parse(s_no_trailing, read=dialect)
    except Exception as e:
        raise SQLSafetyError(f"SQL parse error: {e}") from e

    if len(statements) != 1:
        raise SQLSafetyError("Only a single SQL statement is allowed.")

    tree = statements[0]
    if tree is None:
        raise SQLSafetyError("SQL parse produced no statement.")

    if not _is_select_statement(tree):
        raise SQLSafetyError("Only SELECT queries are allowed.")

    limit_added = False
    s_work = s_no_trailing.strip()

    if re.search(r"\bLIMIT\b\s*$", s_work, flags=re.IGNORECASE):
        s_work = re.sub(r"\bLIMIT\b\s*$", f"LIMIT {default_limit}", s_work, flags=re.IGNORECASE)
        limit_added = True

    if not _has_top_level_limit(s_work) and not re.search(r"\bLIMIT\b\s+\d+", s_work, flags=re.IGNORECASE):
        s_work = f"{s_work} LIMIT {default_limit}"
        limit_added = True

    safe_sql = s_work.strip()
    if not safe_sql.endswith(";"):
        safe_sql += ";"

    return SafeSQLResult(sql=safe_sql, limit_added=limit_added)
