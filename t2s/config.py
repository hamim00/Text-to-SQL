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

    # Groq (OpenAI-compatible)
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")

SETTINGS = Settings()
