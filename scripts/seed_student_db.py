from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "student.db"

def seed():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE STUDENT(
                NAME TEXT,
                CLASS TEXT,
                SECTION TEXT,
                MARKS INTEGER
            );"""
        )
        rows = [
            ("Rifa", "10", "A", 91),
            ("Nabil", "10", "A", 86),
            ("Tania", "9", "B", 79),
            ("Shihab", "8", "C", 73),
            ("Mim", "10", "B", 88),
            ("Hasan", "9", "A", 82),
        ]
        cur.executemany("INSERT INTO STUDENT VALUES (?, ?, ?, ?);", rows)
        conn.commit()
        print(f"Seeded DB at: {DB_PATH}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed()
