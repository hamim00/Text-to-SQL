from __future__ import annotations

import sqlite3
from typing import Any, List, Tuple, Optional

def connect_sqlite(db_path: str, *, read_only: bool = True) -> sqlite3.Connection:
    if read_only:
        # SQLite read-only URI mode
        uri = f"file:{db_path}?mode=ro"
        return sqlite3.connect(uri, uri=True)
    return sqlite3.connect(db_path)

def run_query(db_path: str, sql: str, params: Optional[Tuple[Any, ...]] = None, *, read_only: bool = True) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    """Executes a single SELECT query and returns (columns, rows)."""
    conn = connect_sqlite(db_path, read_only=read_only)
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cols = [d[0] for d in (cur.description or [])]
        return cols, rows
    finally:
        conn.close()
