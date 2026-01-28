from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Optional

class LLMProvider(ABC):
    @abstractmethod
    def generate_sql(self, *, system_prompt: str, user_prompt: str) -> str:
        """Return a SQL string (not executed)."""

    def generate_sql_stream(self, *, system_prompt: str, user_prompt: str) -> Iterable[str]:
        """Yield text chunks (optional). Default: no streaming."""
        yield self.generate_sql(system_prompt=system_prompt, user_prompt=user_prompt)
