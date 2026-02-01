from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

def _get_setting(key: str, default: str = "") -> str:
    """Get setting from Streamlit secrets first, then env vars."""
    # Try Streamlit secrets first
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    # Fall back to environment variable
    return os.getenv(key, default)

class Settings:
    @property
    def provider(self) -> str:
        return _get_setting("T2S_PROVIDER", "ollama").strip().lower()
    
    @property
    def db_path(self) -> str:
        return _get_setting("T2S_DB_PATH", "./data/student.db")
    
    @property
    def db_dialect(self) -> str:
        return _get_setting("T2S_DB_DIALECT", "sqlite").strip().lower()
    
    @property
    def log_db_path(self) -> str:
        return _get_setting("T2S_LOG_DB_PATH", "/tmp/t2s_log.db")
    
    @property
    def history_limit(self) -> int:
        return int(_get_setting("T2S_HISTORY_LIMIT", "20"))
    
    @property
    def max_output_tokens(self) -> int:
        return int(_get_setting("T2S_MAX_OUTPUT_TOKENS", "256"))
    
    @property
    def max_input_chars(self) -> int:
        return int(_get_setting("T2S_MAX_INPUT_CHARS", "500"))
    
    @property
    def rate_limit_max_requests(self) -> int:
        return int(_get_setting("T2S_RATE_LIMIT_MAX_REQUESTS", "15"))
    
    @property
    def rate_limit_window_sec(self) -> int:
        return int(_get_setting("T2S_RATE_LIMIT_WINDOW_SEC", "60"))
    
    @property
    def groq_api_key(self) -> str:
        return _get_setting("GROQ_API_KEY", "")
    
    @property
    def groq_model(self) -> str:
        return _get_setting("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    @property
    def groq_base_url(self) -> str:
        return _get_setting("GROQ_BASE_URL", "https://api.groq.com")
    
    @property
    def ollama_base_url(self) -> str:
        return _get_setting("OLLAMA_BASE_URL", "http://localhost:11434")
    
    @property
    def ollama_model(self) -> str:
        return _get_setting("OLLAMA_MODEL", "llama3.1:8b-instruct")

SETTINGS = Settings()