from __future__ import annotations

from typing import Dict, List
from .schema import format_schema

SYSTEM_PROMPT = """You are an expert data analyst who writes correct SQL.
Rules:
- Only output SQL, no backticks, no explanations.
- Only generate a single SELECT query.
- Use only tables/columns that exist in the provided schema.
- Prefer simple SQL.
"""

def build_user_prompt(question: str, schema: Dict[str, List[str]], dialect: str) -> str:
    schema_txt = format_schema(schema)
    return f"""Database dialect: {dialect}

Schema:
{schema_txt}

Task:
Write a single SELECT query that answers:
{question}

Return ONLY the SQL.
"""
