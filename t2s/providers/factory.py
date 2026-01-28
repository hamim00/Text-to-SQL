from __future__ import annotations

from t2s.config import SETTINGS
from .base import LLMProvider
from .ollama import OllamaProvider
from .groq import GroqProvider

def get_provider() -> LLMProvider:
    p = SETTINGS.provider
    if p == "ollama":
        return OllamaProvider(base_url=SETTINGS.ollama_base_url, model=SETTINGS.ollama_model)
    if p == "groq":
        return GroqProvider(
            api_key=SETTINGS.groq_api_key,
            base_url=SETTINGS.groq_base_url,
            model=SETTINGS.groq_model,
        )
    raise ValueError(f"Unknown provider '{SETTINGS.provider}'. Use 'ollama' or 'groq'.")
