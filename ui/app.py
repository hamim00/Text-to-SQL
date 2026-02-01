"""
Text to SQL - Modern UI
A safe, schema-aware natural language to SQL converter
"""
from __future__ import annotations

import sys
import re
import io
import csv
import time
from uuid import uuid4
from pathlib import Path
import streamlit as st

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
from t2s.security.rate_limit import check_rate_limit

# Page configuration
st.set_page_config(
    page_title="Text to SQL",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, appealing design
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Global Styles */
.stApp {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main container */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Hero Section */
.hero-container {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px;
    padding: 2.5rem;
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.hero-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.5rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em;
}

.hero-subtitle {
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 0;
}

.hero-badge {
    display: inline-block;
    background: linear-gradient(135deg, #e94560, #f72585);
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    margin-left: 0.75rem;
    vertical-align: middle;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Feature Pills */
.feature-pills {
    display: flex;
    gap: 0.75rem;
    margin-top: 1.5rem;
    flex-wrap: wrap;
}

.pill {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    color: rgba(255, 255, 255, 0.9);
    padding: 0.5rem 1rem;
    border-radius: 50px;
    font-size: 0.85rem;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.15);
    transition: all 0.2s ease;
}

.pill:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: translateY(-1px);
}

/* Query Input Section */
.query-section {
    background: #1e1e2e;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.section-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.5);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.75rem;
}

/* SQL Display Boxes */
.sql-container {
    background: #0d1117;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    border: 1px solid #30363d;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    overflow-x: auto;
}

.sql-keyword {
    color: #ff79c6;
    font-weight: 500;
}

.sql-function {
    color: #8be9fd;
}

.sql-string {
    color: #f1fa8c;
}

.sql-number {
    color: #bd93f9;
}

/* Results Table */
.results-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
}

.results-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #ffffff;
}

.row-count-badge {
    background: linear-gradient(135deg, #00d9ff, #00b4d8);
    color: #0d1117;
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Info/Warning/Error Boxes */
.info-box {
    background: linear-gradient(135deg, rgba(0, 180, 216, 0.15), rgba(0, 217, 255, 0.1));
    border-left: 4px solid #00d9ff;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem;
    margin: 1rem 0;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.9rem;
}

.warning-box {
    background: linear-gradient(135deg, rgba(255, 183, 3, 0.15), rgba(255, 214, 10, 0.1));
    border-left: 4px solid #ffb703;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem;
    margin: 1rem 0;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.9rem;
}

.error-box {
    background: linear-gradient(135deg, rgba(233, 69, 96, 0.15), rgba(247, 37, 133, 0.1));
    border-left: 4px solid #e94560;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem;
    margin: 1rem 0;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.9rem;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

.sidebar-header {
    font-size: 0.75rem;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.4);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.config-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.config-label {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.6);
}

.config-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #00d9ff;
    background: rgba(0, 217, 255, 0.1);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
}

/* History Item */
.history-item {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: all 0.2s ease;
    cursor: pointer;
}

.history-item:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.15);
}

/* Buttons */
.stButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 600;
    border-radius: 8px;
    padding: 0.6rem 1.5rem;
    transition: all 0.2s ease;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #e94560, #f72585);
    border: none;
    color: white;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #f72585, #e94560);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(233, 69, 96, 0.4);
}

/* Input Fields */
.stTextInput > div > div > input {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1rem;
    border-radius: 10px;
    border: 2px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.05);
    padding: 0.75rem 1rem;
    transition: all 0.2s ease;
}

.stTextInput > div > div > input:focus {
    border-color: #00d9ff;
    box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.15);
}

/* Dataframe */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
}

/* Download Button */
.stDownloadButton > button {
    background: transparent;
    border: 2px solid rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.8);
    font-weight: 500;
}

.stDownloadButton > button:hover {
    border-color: #00d9ff;
    color: #00d9ff;
    background: rgba(0, 217, 255, 0.1);
}

/* Toggle */
.stCheckbox {
    font-size: 0.9rem;
}

/* Expander */
.streamlit-expanderHeader {
    font-size: 0.9rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.8);
}

/* Code blocks */
.stCodeBlock {
    border-radius: 10px;
}

/* Tips Section */
.tips-container {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    padding: 1rem;
    margin-top: 1rem;
}

.tip-item {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.6);
}

.tip-icon {
    color: #00d9ff;
}

/* Animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.animate-in {
    animation: fadeIn 0.4s ease-out forwards;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
}
</style>
""", unsafe_allow_html=True)


def _prepare_for_execute(sql: str) -> str:
    s = (sql or "").strip()
    s = re.sub(r";+\s*$", "", s)
    if ";" in s:
        raise ValueError("Multiple statements detected (semicolon in the middle).")
    return s


def _current_model() -> str:
    return SETTINGS.groq_model if SETTINGS.provider == "groq" else SETTINGS.ollama_model


def _get_client_key() -> str:
    if "_t2s_session_id" not in st.session_state:
        st.session_state["_t2s_session_id"] = uuid4().hex

    ip = None
    try:
        headers = dict(st.context.headers)
        xff = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
        xri = headers.get("x-real-ip") or headers.get("X-Real-Ip")
        ip = (xff or xri)
        if ip:
            ip = ip.split(",")[0].strip()
    except Exception:
        ip = None

    return ip or st.session_state["_t2s_session_id"]


def highlight_sql(sql: str) -> str:
    """Apply syntax highlighting to SQL."""
    keywords = ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER BY', 'GROUP BY', 
                'HAVING', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 
                'AS', 'DISTINCT', 'LIMIT', 'OFFSET', 'IN', 'NOT', 'NULL',
                'IS', 'LIKE', 'BETWEEN', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
                'ASC', 'DESC', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'WITH']
    
    result = sql
    for kw in keywords:
        pattern = re.compile(r'\b(' + kw + r')\b', re.IGNORECASE)
        result = pattern.sub(r'<span class="sql-keyword">\1</span>', result)
    
    return result


# Sidebar
with st.sidebar:
    # Logo/Brand
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 1.5rem 0;">
        <span style="font-size: 2rem;">🔍</span>
        <h2 style="margin: 0.5rem 0 0 0; font-size: 1.25rem; font-weight: 700; color: #fff;">Text to SQL</h2>
        <span style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">v2.0</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    
    # Configuration display
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"""
        <div style="font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-bottom: 0.25rem;">Provider</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #00d9ff;">{SETTINGS.provider.upper()}</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-bottom: 0.25rem;">Dialect</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #00d9ff;">{SETTINGS.db_dialect.upper()}</div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="margin-top: 1rem; font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-bottom: 0.25rem;">Model</div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #bd93f9; background: rgba(189,147,249,0.1); padding: 0.4rem 0.6rem; border-radius: 6px; word-break: break-all;">{_current_model()}</div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Guardrails
    st.markdown('<div class="sidebar-header">🛡️ Guardrails</div>', unsafe_allow_html=True)
    
    guardrails_data = [
        ("Rate Limit", f"{SETTINGS.rate_limit_max_requests} req / {SETTINGS.rate_limit_window_sec}s"),
        ("Max Tokens", str(SETTINGS.max_output_tokens)),
        ("Max Input", f"{SETTINGS.max_input_chars} chars"),
    ]
    
    for label, value in guardrails_data:
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <span style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">{label}</span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #f1fa8c;">{value}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Options
    st.markdown('<div class="sidebar-header">🎛️ Options</div>', unsafe_allow_html=True)
    show_sql = st.toggle("Show SQL panels", value=True, help="Display raw, cleaned, and safe SQL")
    stream_only = st.toggle("Stream mode (debug)", value=False, help="Stream SQL without execution")
    
    st.markdown("---")
    
    # History
    st.markdown('<div class="sidebar-header">📜 History</div>', unsafe_allow_html=True)
    events = list_events(limit=SETTINGS.history_limit)
    
    if events:
        labels, ids = [], []
        for e in events:
            status = "❌" if e.get("error") else "✅"
            ms = f"{int(e['exec_ms'])}ms" if e.get("exec_ms") is not None else ""
            rc = f"{e['row_count']} rows" if e.get("row_count") is not None else ""
            q = (e.get("question") or "").strip().replace("\n", " ")
            q_short = (q[:30] + "…") if len(q) > 30 else q
            labels.append(f"{status} #{e['id']} • {q_short}")
            ids.append(e["id"])

        chosen = st.selectbox(
            "Recent queries",
            options=list(range(len(labels))),
            format_func=lambda i: labels[i],
            label_visibility="collapsed"
        )
        chosen_id = ids[chosen]
        detail = get_event(chosen_id)
        
        with st.expander("📋 Details", expanded=False):
            if not detail:
                st.warning("Event not found.")
            else:
                st.markdown(f"""
                <div style="font-size: 0.8rem;">
                    <div style="color: rgba(255,255,255,0.5); margin-bottom: 0.5rem;">ID: <span style="color: #fff;">#{detail.get('id')}</span></div>
                    <div style="color: rgba(255,255,255,0.5); margin-bottom: 0.5rem;">Time: <span style="color: #fff;">{detail.get('created_at', '')[:19]}</span></div>
                    <div style="color: rgba(255,255,255,0.5); margin-bottom: 0.5rem;">Provider: <span style="color: #00d9ff;">{detail.get('provider') or 'N/A'}</span></div>
                </div>
                """, unsafe_allow_html=True)
                
                if detail.get("error"):
                    st.error(detail["error"])
                
                if st.button("🔄 Reuse Query", use_container_width=True):
                    st.session_state["question"] = detail.get("question", "")
                    st.rerun()
        
        if st.button("🗑️ Clear History", use_container_width=True):
            clear_events()
            st.rerun()
    else:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: rgba(255,255,255,0.4); font-size: 0.85rem;">
            No queries yet
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tips
    st.markdown('<div class="sidebar-header">💡 Tips</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6); line-height: 1.6;">
        <div style="margin-bottom: 0.5rem;">✨ Be specific in your questions</div>
        <div style="margin-bottom: 0.5rem;">🎯 Mention filters like class, section</div>
        <div style="margin-bottom: 0.5rem;">📊 Results are auto-limited to 100</div>
        <div>🔒 Only SELECT queries allowed</div>
    </div>
    """, unsafe_allow_html=True)


# Main Content
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">Text to SQL<span class="hero-badge">v2</span></h1>
    <p class="hero-subtitle">Transform natural language into safe, optimized SQL queries</p>
    <div class="feature-pills">
        <span class="pill">🔒 SELECT Only</span>
        <span class="pill">📊 Schema Aware</span>
        <span class="pill">⚡ Rate Limited</span>
        <span class="pill">🤖 Multi-Provider</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Query input
st.markdown('<p style="font-size: 0.85rem; font-weight: 600; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Ask a Question</p>', unsafe_allow_html=True)

question = st.text_input(
    "Query",
    placeholder="e.g., Show all students in class 10 with marks above 80",
    key="question",
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    run = st.button("🚀 Run Query", type="primary", disabled=not (question or "").strip(), use_container_width=True)
with col2:
    if st.button("🔄 Clear", use_container_width=True):
        st.session_state["question"] = ""
        st.rerun()

# Query execution
if run and (question or "").strip():
    q = question.strip()

    # Input length check
    if SETTINGS.max_input_chars and len(q) > SETTINGS.max_input_chars:
        st.markdown(f'<div class="error-box">❌ Question too long. Maximum {SETTINGS.max_input_chars} characters allowed.</div>', unsafe_allow_html=True)
        log_event(
            provider=SETTINGS.provider,
            model=_current_model(),
            db_path=SETTINGS.db_path,
            dialect=SETTINGS.db_dialect,
            question=q,
            raw_sql="",
            cleaned_sql="",
            safe_sql="",
            limit_added=False,
            row_count=None,
            exec_ms=0.0,
            error=f"Input too long (> {SETTINGS.max_input_chars} chars)",
        )
        st.stop()

    # Rate limit check
    client_key = _get_client_key()
    allowed, retry_after = check_rate_limit(
        client_key,
        max_requests=SETTINGS.rate_limit_max_requests,
        window_sec=SETTINGS.rate_limit_window_sec,
    )
    if not allowed:
        msg = f"Rate limit exceeded. Try again in ~{int(retry_after)+1} seconds."
        st.markdown(f'<div class="warning-box">⏳ {msg}</div>', unsafe_allow_html=True)
        log_event(
            provider=SETTINGS.provider,
            model=_current_model(),
            db_path=SETTINGS.db_path,
            dialect=SETTINGS.db_dialect,
            question=q,
            raw_sql="",
            cleaned_sql="",
            safe_sql="",
            limit_added=False,
            row_count=None,
            exec_ms=0.0,
            error=msg,
        )
        st.stop()

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

        # Stream mode
        if stream_only:
            st.markdown("### 🔄 Streaming SQL")
            box = st.empty()
            buf = ""
            for chunk in provider.generate_sql_stream(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt):
                buf += chunk
                box.code(buf, language="sql")

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

        # Generate SQL
        with st.spinner("🤖 Generating SQL..."):
            raw_sql = provider.generate_sql(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
        
        cleaned_sql = extract_sql_candidate(raw_sql)
        safe = validate_and_rewrite_select(raw_sql, dialect=SETTINGS.db_dialect, default_limit=100)
        safe_sql = safe.sql
        limit_added = safe.limit_added

        # Display SQL panels
        if show_sql:
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📝 Generated SQL (Raw)")
                st.code(raw_sql, language="sql")
            
            with col2:
                st.markdown("#### 🧹 Cleaned SQL")
                st.code(cleaned_sql, language="sql")
            
            st.markdown("#### 🔒 Executed SQL (Safe)")
            if limit_added:
                st.markdown('<div class="info-box">ℹ️ <strong>LIMIT 100</strong> was added automatically for safety and performance.</div>', unsafe_allow_html=True)
            st.code(safe_sql, language="sql")

        # Execute query
        exec_sql = _prepare_for_execute(safe_sql)
        cols, rows = run_query(SETTINGS.db_path, exec_sql, read_only=True)

        row_count = len(rows)
        exec_ms = (time.perf_counter() - start) * 1000.0

        # Results section
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("### 📊 Results")
        with col2:
            st.markdown(f"""
            <div style="text-align: right; padding-top: 0.5rem;">
                <span style="background: linear-gradient(135deg, #00d9ff, #00b4d8); color: #0d1117; padding: 0.35rem 0.85rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{row_count} rows</span>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="text-align: right; padding-top: 0.5rem;">
                <span style="background: rgba(189,147,249,0.2); color: #bd93f9; padding: 0.35rem 0.85rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{int(exec_ms)}ms</span>
            </div>
            """, unsafe_allow_html=True)

        if cols:
            records = [{c: row[i] for i, c in enumerate(cols)} for row in rows]
            st.dataframe(records, use_container_width=True, hide_index=True)

            # Download button
            csv_buf = io.StringIO()
            writer = csv.DictWriter(csv_buf, fieldnames=cols)
            writer.writeheader()
            for r in records:
                writer.writerow(r)

            st.download_button(
                label="📥 Download CSV",
                data=csv_buf.getvalue().encode("utf-8"),
                file_name="query_results.csv",
                mime="text/csv",
            )
        else:
            st.markdown('<div class="info-box">ℹ️ Query executed successfully but returned no results.</div>', unsafe_allow_html=True)

    except SQLSafetyError as e:
        error_msg = f"Blocked by safety gate: {e}"
        st.markdown(f'<div class="error-box">🚫 <strong>Safety Block:</strong> {e}</div>', unsafe_allow_html=True)

    except Exception as e:
        error_msg = f"{e}"
        st.markdown(f'<div class="error-box">❌ <strong>Error:</strong> {e}</div>', unsafe_allow_html=True)
        
        if show_sql and (raw_sql or cleaned_sql):
            with st.expander("🔍 Debug: View Generated SQL"):
                if raw_sql:
                    st.markdown("**Raw SQL:**")
                    st.code(raw_sql, language="sql")
                if cleaned_sql:
                    st.markdown("**Cleaned SQL:**")
                    st.code(cleaned_sql, language="sql")

    finally:
        if exec_ms is None:
            exec_ms = (time.perf_counter() - start) * 1000.0

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

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: rgba(255,255,255,0.4); font-size: 0.8rem;">
    Built using Streamlit • Powered by LLMs (Ollama / Groq)
</div>
""", unsafe_allow_html=True)