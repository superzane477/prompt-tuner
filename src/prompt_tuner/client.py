from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "https://api.example.com/v1"
DEFAULT_TIMEOUT = 60.0


@dataclass
class Model:
    id: str
    name: str
    provider: str


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class AIClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = DEFAULT_TIMEOUT):
        self.api_key = api_key or os.getenv("API_KEY", "")
        self.base_url = (base_url or os.getenv("API_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=timeout,
        )

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def fetch_models(self) -> list[Model]:
        resp = self._http.get("/models")
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []
        return [
            Model(
                id=m["id"],
                name=m.get("display_name") or m.get("name") or m["id"],
                provider=m.get("owned_by") or m.get("provider") or "",
            )
            for m in items
        ]

    def chat(self, model: str, messages: list[ChatMessage]) -> ChatResponse:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        resp = self._http.post("/chat/completions", json=payload)
        resp.raise_for_status()
        body = resp.json()
        usage = body.get("usage", {})
        return ChatResponse(
            content=body["choices"][0]["message"]["content"],
            model=body.get("model", model),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
