from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# Try to load from Streamlit secrets first
def get_env(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key])
    except:
        pass
    return os.getenv(key, default)

@dataclass(frozen=True)
class Settings:
    provider: str = get_env("T2S_PROVIDER", "ollama").strip().lower()
    db_path: str = get_env("T2S_DB_PATH", "./data/student.db")
    db_dialect: str = get_env("T2S_DB_DIALECT", "sqlite").strip().lower()

    # Logs - use /tmp for Streamlit Cloud
    log_db_path: str = get_env("T2S_LOG_DB_PATH", "/tmp/t2s_log.db")
    history_limit: int = int(get_env("T2S_HISTORY_LIMIT", "20"))

    # Guardrails
    max_output_tokens: int = int(get_env("T2S_MAX_OUTPUT_TOKENS", "256"))
    max_input_chars: int = int(get_env("T2S_MAX_INPUT_CHARS", "500"))
    rate_limit_max_requests: int = int(get_env("T2S_RATE_LIMIT_MAX_REQUESTS", "15"))
    rate_limit_window_sec: int = int(get_env("T2S_RATE_LIMIT_WINDOW_SEC", "60"))

    # Groq
    groq_api_key: str = get_env("GROQ_API_KEY", "")
    groq_model: str = get_env("GROQ_MODEL", "llama-3.3-70b-versatile")
    groq_base_url: str = get_env("GROQ_BASE_URL", "https://api.groq.com")

    # Ollama
    ollama_base_url: str = get_env("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = get_env("OLLAMA_MODEL", "llama3.1:8b-instruct")

SETTINGS = Settings()