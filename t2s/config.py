from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    provider: str = os.getenv("T2S_PROVIDER", "ollama").strip().lower()
    db_path: str = os.getenv("T2S_DB_PATH", "./data/student.db")
    db_dialect: str = os.getenv("T2S_DB_DIALECT", "sqlite").strip().lower()

    # Logs (Phase 3)
    log_db_path: str = os.getenv("T2S_LOG_DB_PATH", "./data/t2s_log.db")
    history_limit: int = int(os.getenv("T2S_HISTORY_LIMIT", "20"))

    # Guardrails (Phase 3.2)
    max_output_tokens: int = int(os.getenv("T2S_MAX_OUTPUT_TOKENS", "256"))
    max_input_chars: int = int(os.getenv("T2S_MAX_INPUT_CHARS", "500"))
    rate_limit_max_requests: int = int(os.getenv("T2S_RATE_LIMIT_MAX_REQUESTS", "15"))
    rate_limit_window_sec: int = int(os.getenv("T2S_RATE_LIMIT_WINDOW_SEC", "60"))

    # Groq (OpenAI-compatible)
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com")

    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")

SETTINGS = Settings()
