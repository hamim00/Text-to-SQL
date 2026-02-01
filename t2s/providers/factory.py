from __future__ import annotations

from t2s.config import SETTINGS
from .groq import GroqProvider


def get_provider() -> GroqProvider:
    return GroqProvider(
        api_key=SETTINGS.groq_api_key,
        base_url=SETTINGS.groq_base_url,
        model=SETTINGS.groq_model,
    )