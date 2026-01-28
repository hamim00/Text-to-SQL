from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple, Iterable

from t2s.config import SETTINGS
from t2s.providers import get_provider
from t2s.db.runner import run_query
from .schema import get_sqlite_schema
from .prompting import SYSTEM_PROMPT, build_user_prompt
from .safety import validate_and_rewrite_select, SQLSafetyError, extract_sql_candidate, SafeSQLResult


class QueryValidationError(RuntimeError):
    def __init__(self, message: str, *, raw_sql: str, cleaned_sql: str):
        super().__init__(message)
        self.raw_sql = raw_sql
        self.cleaned_sql = cleaned_sql


@dataclass(frozen=True)
class TextToSQLResponse:
    raw_sql: str
    cleaned_sql: str
    safe_sql: str
    columns: List[str]
    rows: List[Tuple[Any, ...]]
    limit_added: bool


def text_to_sql(question: str) -> TextToSQLResponse:
    schema = get_sqlite_schema(SETTINGS.db_path)
    user_prompt = build_user_prompt(question, schema, SETTINGS.db_dialect)

    provider = get_provider()
    raw_sql = provider.generate_sql(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    cleaned_sql = extract_sql_candidate(raw_sql)

    try:
        safe: SafeSQLResult = validate_and_rewrite_select(raw_sql, dialect=SETTINGS.db_dialect)
    except SQLSafetyError as e:
        raise QueryValidationError(str(e), raw_sql=raw_sql, cleaned_sql=cleaned_sql) from e

    cols, rows = run_query(SETTINGS.db_path, safe.sql, read_only=True)

    return TextToSQLResponse(
        raw_sql=raw_sql,
        cleaned_sql=cleaned_sql,
        safe_sql=safe.sql,
        columns=cols,
        rows=rows,
        limit_added=safe.limit_added,
    )


def text_to_sql_stream(question: str) -> Iterable[str]:
    schema = get_sqlite_schema(SETTINGS.db_path)
    user_prompt = build_user_prompt(question, schema, SETTINGS.db_dialect)
    provider = get_provider()
    yield from provider.generate_sql_stream(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
