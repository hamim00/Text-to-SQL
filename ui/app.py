from __future__ import annotations

import sys
import re
from pathlib import Path
import streamlit as st

# Ensure project root is on sys.path even if launched from ui/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from t2s.config import SETTINGS
from t2s.providers import get_provider
from t2s.sql.schema import get_sqlite_schema
from t2s.sql.prompting import SYSTEM_PROMPT, build_user_prompt
from t2s.sql.safety import validate_and_rewrite_select, extract_sql_candidate, SQLSafetyError
from t2s.db.runner import run_query

st.set_page_config(page_title="Text to SQL (v2)", layout="wide")

st.title("Text to SQL (v2)")
st.caption("Safe (SELECT-only), schema-aware, with provider switching (Ollama/Groq).")

def _prepare_for_execute(sql: str) -> str:
    """
    sqlite3 cursor.execute() supports a trailing semicolon, but to avoid
    weird cases (e.g., semicolon in the middle), we normalize:
      - remove trailing semicolons
      - block any remaining internal semicolons
    """
    s = (sql or "").strip()
    s = re.sub(r";+\s*$", "", s)  # strip trailing semicolons
    if ";" in s:
        raise ValueError("Multiple statements detected (semicolon in the middle).")
    return s

with st.sidebar:
    st.subheader("Runtime")
    st.write(f"Provider: `{SETTINGS.provider}`")
    st.write(f"DB: `{SETTINGS.db_path}`")
    st.write(f"Dialect: `{SETTINGS.db_dialect}`")
    st.divider()

    st.subheader("Options")
    show_sql = st.toggle("Show SQL panels", value=True)
    stream_only = st.toggle("Stream SQL only (debug)", value=False)
    st.divider()

    st.subheader("Tips")
    st.markdown(
        "- Ask specific questions.\n"
        "- Mention filters (e.g., class, section).\n"
        "- Results are auto-limited."
    )

question = st.text_input(
    "Ask a question about the database",
    placeholder="e.g., Show all students in class 10",
)

run = st.button("Run", type="primary", disabled=not question.strip())

if run and question.strip():
    q = question.strip()

    provider = get_provider()

    # Stream-only mode: just show the raw SQL tokens
    if stream_only:
        st.subheader("Streaming SQL (raw)")
        box = st.empty()
        buf = ""
        try:
            for chunk in provider.generate_sql_stream(system_prompt=SYSTEM_PROMPT, user_prompt=q):
                buf += chunk
                box.code(buf, language="sql")
        except Exception as e:
            st.error(f"Streaming error: {e}")
        st.stop()

    # Normal mode: schema -> prompt -> generate -> clean -> safety -> execute
    raw_sql = ""
    cleaned_sql = ""
    safe_sql = ""

    try:
        schema = get_sqlite_schema(SETTINGS.db_path)
        user_prompt = build_user_prompt(q, schema, SETTINGS.db_dialect)

        raw_sql = provider.generate_sql(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
        cleaned_sql = extract_sql_candidate(raw_sql)

        safe = validate_and_rewrite_select(raw_sql, dialect=SETTINGS.db_dialect, default_limit=100)
        safe_sql = safe.sql

        if show_sql:
            st.subheader("Generated SQL (raw)")
            st.code(raw_sql, language="sql")

            st.subheader("Cleaned SQL")
            st.code(cleaned_sql, language="sql")

            st.subheader("Executed SQL (safe)")
            if safe.limit_added:
                st.info("LIMIT was added automatically for safety/performance.")
            st.code(safe_sql, language="sql")

        # Execute (with normalization to avoid semicolon-in-middle issues)
        exec_sql = _prepare_for_execute(safe_sql)
        cols, rows = run_query(SETTINGS.db_path, exec_sql, read_only=True)

        st.subheader("Results")
        if cols:
            st.dataframe(
                [{c: row[i] for i, c in enumerate(cols)} for row in rows],
                use_container_width=True,
            )
        else:
            st.write("No results.")

    except SQLSafetyError as e:
        st.error(f"Blocked by safety gate: {e}")
        if show_sql:
            st.subheader("Generated SQL (raw)")
            st.code(raw_sql, language="sql")
            st.subheader("Cleaned SQL")
            st.code(cleaned_sql, language="sql")

    except Exception as e:
        st.error(f"Error: {e}")
        if show_sql:
            st.subheader("Generated SQL (raw)")
            st.code(raw_sql, language="sql")
            st.subheader("Cleaned SQL")
            st.code(cleaned_sql, language="sql")
            st.subheader("Executed SQL (safe)")
            st.code(safe_sql, language="sql")
