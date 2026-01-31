from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from t2s.config import SETTINGS


DDL = """CREATE TABLE IF NOT EXISTS query_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  db_path TEXT,
  dialect TEXT,
  question TEXT,
  raw_sql TEXT,
  cleaned_sql TEXT,
  safe_sql TEXT,
  limit_added INTEGER,
  row_count INTEGER,
  exec_ms REAL,
  error TEXT
);
"""


def _connect() -> sqlite3.Connection:
    # Separate DB for logs (default: ./data/t2s_log.db)
    # WAL improves concurrency; streamlit reruns can overlap.
    conn = sqlite3.connect(SETTINGS.log_db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def _init_db() -> None:
    conn = _connect()
    try:
        conn.execute(DDL)
        conn.commit()
    finally:
        conn.close()


def log_event(
    *,
    provider: str,
    model: str,
    db_path: str,
    dialect: str,
    question: str,
    raw_sql: str = "",
    cleaned_sql: str = "",
    safe_sql: str = "",
    limit_added: bool = False,
    row_count: Optional[int] = None,
    exec_ms: Optional[float] = None,
    error: Optional[str] = None,
) -> int:
    _init_db()
    created_at = datetime.now(timezone.utc).isoformat()

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO query_log (
                created_at, provider, model, db_path, dialect, question,
                raw_sql, cleaned_sql, safe_sql, limit_added, row_count, exec_ms, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                created_at,
                provider,
                model,
                db_path,
                dialect,
                question,
                raw_sql,
                cleaned_sql,
                safe_sql,
                1 if limit_added else 0,
                row_count,
                exec_ms,
                error,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_events(limit: int = 20) -> List[Dict[str, Any]]:
    _init_db()
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, created_at, question, provider, model, row_count, exec_ms, error
               FROM query_log
               ORDER BY id DESC
               LIMIT ?""",
            (int(limit),),
        )
        rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "id": r[0],
                    "created_at": r[1],
                    "question": r[2],
                    "provider": r[3],
                    "model": r[4],
                    "row_count": r[5],
                    "exec_ms": r[6],
                    "error": r[7],
                }
            )
        return out
    finally:
        conn.close()


def get_event(event_id: int) -> Optional[Dict[str, Any]]:
    _init_db()
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, created_at, provider, model, db_path, dialect, question,
                      raw_sql, cleaned_sql, safe_sql, limit_added, row_count, exec_ms, error
               FROM query_log
               WHERE id = ?""",
            (int(event_id),),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": r[0],
            "created_at": r[1],
            "provider": r[2],
            "model": r[3],
            "db_path": r[4],
            "dialect": r[5],
            "question": r[6],
            "raw_sql": r[7],
            "cleaned_sql": r[8],
            "safe_sql": r[9],
            "limit_added": bool(r[10]),
            "row_count": r[11],
            "exec_ms": r[12],
            "error": r[13],
        }
    finally:
        conn.close()


def clear_events() -> None:
    _init_db()
    conn = _connect()
    try:
        conn.execute("DELETE FROM query_log;")
        conn.commit()
    finally:
        conn.close()
