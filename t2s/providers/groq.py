from __future__ import annotations

from typing import Iterable, Dict, Any
import httpx

from .base import LLMProvider


class GroqProvider(LLMProvider):
    """Calls Groq's OpenAI-compatible Chat Completions endpoint.

    Works with GROQ_BASE_URL set to either:
      - https://api.groq.com
      - https://api.groq.com/openai/v1
    """

    def __init__(self, *, api_key: str, base_url: str, model: str, timeout_s: float = 60.0):
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing. Set it in .env.")
        self.api_key = api_key.strip()
        self.base_url = (base_url or "https://api.groq.com").strip().rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _endpoint(self, path: str) -> str:
        """Return a full endpoint URL for OpenAI-compatible routes."""
        # Normalize whether base_url includes /openai/v1 or not
        if self.base_url.endswith("/openai/v1"):
            return f"{self.base_url}{path}"
        return f"{self.base_url}/openai/v1{path}"

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
        url = self._endpoint("/chat/completions")
        payload = self._payload(system_prompt, user_prompt, stream=False)

        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.post(url, headers=self._headers(), json=payload)

        # Better error message (shows Groq JSON error details)
        if r.status_code >= 400:
            raise RuntimeError(f"Groq API error {r.status_code}: {r.text}")

        data = r.json()
        return (data["choices"][0]["message"]["content"] or "").strip()

    def generate_sql_stream(self, *, system_prompt: str, user_prompt: str) -> Iterable[str]:
        url = self._endpoint("/chat/completions")
        payload = self._payload(system_prompt, user_prompt, stream=True)

        with httpx.Client(timeout=self.timeout_s) as client:
            with client.stream("POST", url, headers=self._headers(), json=payload) as r:
                if r.status_code >= 400:
                    body = r.read().decode("utf-8", errors="replace")
                    raise RuntimeError(f"Groq API error {r.status_code}: {body}")

                for line in r.iter_lines():
                    if not line:
                        continue
                    # decode bytes to str for startswith and further processing
                    if isinstance(line, bytes):
                        line_str = line.decode("utf-8", errors="replace")
                    else:
                        line_str = line
                    if line_str.startswith("data:"):
                        line_str = line_str[len("data:"):].strip()
                    if line_str == "[DONE]":
                        break
                    try:
                        obj = httpx.Response(200, content=line_str.encode("utf-8")).json()
                    except Exception:
                        continue
                    delta = obj.get("choices", [{}])[0].get("delta", {})
                    chunk = delta.get("content", "")
                    if chunk:
                        yield chunk
