from __future__ import annotations

import sys
import re
import io
import csv
import time
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
from t2s.logging.query_log import log_event, list_events, get_event, clear_events


st.set_page_config(page_title="Text to SQL (v2)", layout="wide")

st.title("Text to SQL (v2)")
st.caption("Safe (SELECT-only), schema-aware, with provider switching (Ollama/Groq).")


def _prepare_for_execute(sql: str) -> str:
    """Normalize for sqlite3.execute(): remove trailing semicolons and block internal semicolons."""
    s = (sql or "").strip()
    s = re.sub(r";+\s*$", "", s)  # strip trailing semicolons
    if ";" in s:
        raise ValueError("Multiple statements detected (semicolon in the middle).")
    return s


def _current_model() -> str:
    if SETTINGS.provider == "groq":
        return SETTINGS.groq_model
    return SETTINGS.ollama_model


# --- Sidebar: runtime + options + history ---
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

    st.subheader("History")
    events = list_events(limit=SETTINGS.history_limit)
    labels = []
    ids = []
    for e in events:
        status = "❌" if e.get("error") else "✅"
        ms = f"{int(e['exec_ms'])}ms" if e.get("exec_ms") is not None else ""
        rc = f"{e['row_count']} rows" if e.get("row_count") is not None else ""
        q = (e.get("question") or "").strip().replace("\n", " ")
        q_short = (q[:50] + "…") if len(q) > 50 else q
        labels.append(f"{status} #{e['id']} • {q_short} • {rc} {ms}")
        ids.append(e["id"])

    if labels:
        chosen = st.selectbox("Recent queries", options=list(range(len(labels))), format_func=lambda i: labels[i])
        chosen_id = ids[chosen]
        detail = get_event(chosen_id)
        with st.expander("Selected details", expanded=False):
            st.write(f"ID: {detail['id']}")
            st.write(f"Time (UTC): {detail['created_at']}")
            st.write(f"Provider/Model: {detail['provider']} / {detail['model']}")
            if detail.get("error"):
                st.error(detail["error"])
            if st.button("Use this question"):
                st.session_state["question"] = detail["question"]
                st.rerun()
    else:
        st.caption("No history yet.")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Clear history"):
            clear_events()
            st.rerun()
    with col_b:
        pass

    st.divider()
    st.subheader("Tips")
    st.markdown(
        "- Ask specific questions.\n"
        "- Mention filters (e.g., class, section).\n"
        "- Results are auto-limited."
    )


# --- Main input ---
question = st.text_input(
    "Ask a question about the database",
    placeholder="e.g., Show all students in class 10",
    key="question",
)

run = st.button("Run", type="primary", disabled=not (question or "").strip())

if run and (question or "").strip():
    q = question.strip()

    provider = get_provider()
    raw_sql = ""
    cleaned_sql = ""
    safe_sql = ""
    limit_added = False

    row_count = None
    exec_ms = None
    error_msg = None

    start = time.perf_counter()

    try:
        schema = get_sqlite_schema(SETTINGS.db_path)
        user_prompt = build_user_prompt(q, schema, SETTINGS.db_dialect)

        if stream_only:
            st.subheader("Streaming SQL (raw)")
            box = st.empty()
            buf = ""
            for chunk in provider.generate_sql_stream(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt):
                buf += chunk
                box.code(buf, language="sql")
            # log stream-only as a record (no execution)
            exec_ms = (time.perf_counter() - start) * 1000.0
            log_event(
                provider=SETTINGS.provider,
                model=_current_model(),
                db_path=SETTINGS.db_path,
                dialect=SETTINGS.db_dialect,
                question=q,
                raw_sql=buf,
                cleaned_sql=extract_sql_candidate(buf),
                safe_sql="",
                limit_added=False,
                row_count=None,
                exec_ms=exec_ms,
                error=None,
            )
            st.stop()

        raw_sql = provider.generate_sql(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
        cleaned_sql = extract_sql_candidate(raw_sql)

        safe = validate_and_rewrite_select(raw_sql, dialect=SETTINGS.db_dialect, default_limit=100)
        safe_sql = safe.sql
        limit_added = safe.limit_added

        if show_sql:
            st.subheader("Generated SQL (raw)")
            st.code(raw_sql, language="sql")

            st.subheader("Cleaned SQL")
            st.code(cleaned_sql, language="sql")

            st.subheader("Executed SQL (safe)")
            if limit_added:
                st.info("LIMIT was added automatically for safety/performance.")
            st.code(safe_sql, language="sql")

        exec_sql = _prepare_for_execute(safe_sql)
        cols, rows = run_query(SETTINGS.db_path, exec_sql, read_only=True)

        row_count = len(rows)
        exec_ms = (time.perf_counter() - start) * 1000.0

        st.subheader("Results")
        if cols:
            records = [{c: row[i] for i, c in enumerate(cols)} for row in rows]
            st.dataframe(records, use_container_width=True)

            # CSV export (Phase 3)
            csv_buf = io.StringIO()
            writer = csv.DictWriter(csv_buf, fieldnames=cols)
            writer.writeheader()
            for r in records:
                writer.writerow(r)
            st.download_button(
                label="Download results as CSV",
                data=csv_buf.getvalue().encode("utf-8"),
                file_name="results.csv",
                mime="text/csv",
            )
        else:
            st.write("No results.")

    except SQLSafetyError as e:
        error_msg = f"Blocked by safety gate: {e}"
        st.error(error_msg)

    except Exception as e:
        error_msg = f"{e}"
        st.error(f"Error: {e}")
        if show_sql:
            st.subheader("Generated SQL (raw)")
            st.code(raw_sql, language="sql")
            st.subheader("Cleaned SQL")
            st.code(cleaned_sql, language="sql")
            st.subheader("Executed SQL (safe)")
            st.code(safe_sql, language="sql")

    finally:
        if exec_ms is None:
            exec_ms = (time.perf_counter() - start) * 1000.0

        # Always log the attempt (success or error)
        log_event(
            provider=SETTINGS.provider,
            model=_current_model(),
            db_path=SETTINGS.db_path,
            dialect=SETTINGS.db_dialect,
            question=q,
            raw_sql=raw_sql,
            cleaned_sql=cleaned_sql,
            safe_sql=safe_sql,
            limit_added=limit_added,
            row_count=row_count,
            exec_ms=exec_ms,
            error=error_msg,
        )
