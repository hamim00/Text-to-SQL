from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

def _get(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except:
        pass
    return os.getenv(key, default)

class Settings:
    @property
    def provider(self) -> str:
        return "groq"
    
    @property
    def db_path(self) -> str:
        return _get("T2S_DB_PATH", "./data/student.db")
    
    @property
    def db_dialect(self) -> str:
        return "sqlite"
    
    @property
    def log_db_path(self) -> str:
        return "/tmp/t2s_log.db"
    
    @property
    def history_limit(self) -> int:
        return int(_get("T2S_HISTORY_LIMIT", "20"))
    
    @property
    def max_output_tokens(self) -> int:
        return int(_get("T2S_MAX_OUTPUT_TOKENS", "256"))
    
    @property
    def max_input_chars(self) -> int:
        return int(_get("T2S_MAX_INPUT_CHARS", "500"))
    
    @property
    def rate_limit_max_requests(self) -> int:
        return int(_get("T2S_RATE_LIMIT_MAX_REQUESTS", "15"))
    
    @property
    def rate_limit_window_sec(self) -> int:
        return int(_get("T2S_RATE_LIMIT_WINDOW_SEC", "60"))
    
    @property
    def groq_api_key(self) -> str:
        return _get("GROQ_API_KEY", "")
    
    @property
    def groq_model(self) -> str:
        return _get("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    @property
    def groq_base_url(self) -> str:
        return _get("GROQ_BASE_URL", "https://api.groq.com")

SETTINGS = Settings()