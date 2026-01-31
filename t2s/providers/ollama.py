from __future__ import annotations

from typing import Iterable, Dict, Any
import httpx

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, *, base_url: str, model: str, max_output_tokens: int = 256, timeout_s: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_output_tokens = int(max_output_tokens) if max_output_tokens else 0
        self.timeout_s = timeout_s

    def _payload(self, system_prompt: str, user_prompt: str, stream: bool) -> Dict[str, Any]:
        options: Dict[str, Any] = {"temperature": 0.1}
        if self.max_output_tokens and self.max_output_tokens > 0:
            options["num_predict"] = self.max_output_tokens

        return {
            "model": self.model,
            "stream": stream,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": options,
        }

    def generate_sql(self, *, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = self._payload(system_prompt, user_prompt, stream=False)
        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        return (data.get("message", {}).get("content", "") or "").strip()

    def generate_sql_stream(self, *, system_prompt: str, user_prompt: str) -> Iterable[str]:
        url = f"{self.base_url}/api/chat"
        payload = self._payload(system_prompt, user_prompt, stream=True)
        with httpx.Client(timeout=self.timeout_s) as client:
            with client.stream("POST", url, json=payload) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        obj = httpx.Response(200, content=line).json()
                    except Exception:
                        continue
                    if obj.get("done"):
                        break
                    chunk = obj.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
