from __future__ import annotations

from typing import Iterable, Dict, Any
import httpx

from .base import LLMProvider

class GroqProvider(LLMProvider):
    """Calls Groq's OpenAI-compatible Chat Completions endpoint."""

    def __init__(self, *, api_key: str, base_url: str, model: str, timeout_s: float = 60.0):
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing. Set it in .env.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _payload(self, system_prompt: str, user_prompt: str, stream: bool) -> Dict[str, Any]:
        return {
            "model": self.model,
            "stream": stream,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

    def generate_sql(self, *, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = self._payload(system_prompt, user_prompt, stream=False)
        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.post(url, headers=self._headers(), json=payload)
            r.raise_for_status()
            data = r.json()
        return (data["choices"][0]["message"]["content"] or "").strip()

    def generate_sql_stream(self, *, system_prompt: str, user_prompt: str) -> Iterable[str]:
        url = f"{self.base_url}/chat/completions"
        payload = self._payload(system_prompt, user_prompt, stream=True)
        with httpx.Client(timeout=self.timeout_s) as client:
            with client.stream("POST", url, headers=self._headers(), json=payload) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    # OpenAI-style SSE-ish lines: "data: {...}"
                    if line.startswith(b"data:"):
                        line = line[len(b"data:"):].strip()
                    if line == b"[DONE]":
                        break
                    try:
                        obj = httpx.Response(200, content=line).json()
                    except Exception:
                        continue
                    delta = obj.get("choices", [{}])[0].get("delta", {})
                    chunk = delta.get("content", "")
                    if chunk:
                        yield chunk
