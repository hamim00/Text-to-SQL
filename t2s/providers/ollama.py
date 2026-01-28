from __future__ import annotations

from typing import Iterable, Dict, Any, Optional
import httpx

from .base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, *, base_url: str, model: str, timeout_s: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def _payload(self, system_prompt: str, user_prompt: str, stream: bool) -> Dict[str, Any]:
        return {
            "model": self.model,
            "stream": stream,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # keep deterministic-ish for SQL generation
            "options": {"temperature": 0.1},
        }

    def generate_sql(self, *, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = self._payload(system_prompt, user_prompt, stream=False)
        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        content = data.get("message", {}).get("content", "")
        return content.strip()

    def generate_sql_stream(self, *, system_prompt: str, user_prompt: str) -> Iterable[str]:
        url = f"{self.base_url}/api/chat"
        payload = self._payload(system_prompt, user_prompt, stream=True)
        with httpx.Client(timeout=self.timeout_s) as client:
            with client.stream("POST", url, json=payload) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    # Ollama streams JSON per line
                    try:
                        obj = httpx.Response(200, content=line).json()
                    except Exception:
                        continue
                    if obj.get("done"):
                        break
                    chunk = obj.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
