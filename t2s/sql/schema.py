from __future__ import annotations

import sqlite3
from typing import Dict, List

def get_sqlite_schema(db_path: str) -> Dict[str, List[str]]:
    """Return {table_name: [col1, col2, ...]} for SQLite."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cur.fetchall()]
        schema: Dict[str, List[str]] = {}
        for t in tables:
            cur.execute(f"PRAGMA table_info('{t}')")
            cols = [row[1] for row in cur.fetchall()]  # (cid, name, type, notnull, dflt_value, pk)
            schema[t] = cols
        return schema
    finally:
        conn.close()

def format_schema(schema: Dict[str, List[str]]) -> str:
    lines = []
    for table, cols in schema.items():
        lines.append(f"- {table}({', '.join(cols)})")
    return "\n".join(lines)