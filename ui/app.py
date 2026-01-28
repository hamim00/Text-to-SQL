from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import streamlit as st

from t2s.sql.service import text_to_sql, text_to_sql_stream
from t2s.sql.safety import SQLSafetyError
from t2s.config import SETTINGS

st.set_page_config(page_title="Text to SQL (v2)", layout="wide")

st.title("Text to SQL (v2)")
st.caption("Safe (SELECT-only), schema-aware, with provider switching (Ollama/Groq).")

with st.sidebar:
    st.subheader("Runtime")
    st.write(f"Provider: `{SETTINGS.provider}`")
    st.write(f"DB: `{SETTINGS.db_path}`")
    st.write(f"Dialect: `{SETTINGS.db_dialect}`")
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

col1, col2 = st.columns([1, 1])
with col1:
    run = st.button("Run", type="primary")
with col2:
    stream_only = st.checkbox("Stream SQL only (debug)", value=False)

if run and question.strip():
    if stream_only:
        st.subheader("Streaming SQL (raw)")
        box = st.empty()
        buf = ""
        try:
            for chunk in text_to_sql_stream(question):
                buf += chunk
                box.code(buf, language="sql")
        except Exception as e:
            st.error(f"Streaming error: {e}")
    else:
        try:
            resp = text_to_sql(question)
        except SQLSafetyError as e:
            st.error(f"Blocked by safety gate: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
        else:
            st.subheader("Generated SQL (raw)")
            st.code(resp.raw_sql, language="sql")

            st.subheader("Executed SQL (safe)")
            if resp.limit_added:
                st.info("LIMIT was added automatically for safety/performance.")
            st.code(resp.safe_sql, language="sql")

            st.subheader("Results")
            if resp.columns:
                st.dataframe(
                    [
                        {"_row": i, **{c: r[j] for j, c in enumerate(resp.columns)}}
                        for i, r in enumerate(resp.rows)
                    ],
                    use_container_width=True,
                )
            else:
                st.write("No results.")
