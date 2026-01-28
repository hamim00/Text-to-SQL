from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Iterable, Optional

from t2s.config import SETTINGS
from t2s.providers import get_provider
from t2s.db.runner import run_query
from .schema import get_sqlite_schema
from .prompting import SYSTEM_PROMPT, build_user_prompt
from .safety import validate_and_rewrite_select, SQLSafetyError, SafeSQLResult

@dataclass(frozen=True)
class TextToSQLResponse:
    raw_sql: str
    safe_sql: str
    columns: List[str]
    rows: List[Tuple[Any, ...]]
    limit_added: bool

def text_to_sql(question: str) -> TextToSQLResponse:
    schema = get_sqlite_schema(SETTINGS.db_path)
    user_prompt = build_user_prompt(question, schema, SETTINGS.db_dialect)

    provider = get_provider()
    raw_sql = provider.generate_sql(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    safe: SafeSQLResult = validate_and_rewrite_select(raw_sql, dialect=SETTINGS.db_dialect)
    cols, rows = run_query(SETTINGS.db_path, safe.sql, read_only=True)

    return TextToSQLResponse(
        raw_sql=raw_sql,
        safe_sql=safe.sql,
        columns=cols,
        rows=rows,
        limit_added=safe.limit_added,
    )

def text_to_sql_stream(question: str) -> Iterable[str]:
    """Stream *raw* SQL tokens from the provider (Phase 1 basic streaming)."""
    schema = get_sqlite_schema(SETTINGS.db_path)
    user_prompt = build_user_prompt(question, schema, SETTINGS.db_dialect)
    provider = get_provider()
    yield from provider.generate_sql_stream(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
