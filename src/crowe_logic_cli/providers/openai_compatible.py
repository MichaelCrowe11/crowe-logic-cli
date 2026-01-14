from __future__ import annotations

import httpx

from crowe_logic_cli.config import OpenAICompatibleConfig
from crowe_logic_cli.providers.base import ChatProvider, ChatResponse, Message


class OpenAICompatibleProvider(ChatProvider):
    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self._config = config

    def name(self) -> str:
        return "openai_compatible"

    def chat(self, messages: list[Message]) -> ChatResponse:
        base = self._config.base_url.rstrip("/")
        url = f"{base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._config.model,
            "messages": messages,
            "temperature": 0.2,
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choice0 = (data.get("choices") or [{}])[0]
        message = choice0.get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            content = ""
        return ChatResponse(content=content)

    def healthcheck(self) -> None:
        self.chat([
            {"role": "system", "content": "You are a healthcheck."},
            {"role": "user", "content": "Respond with: OK"},
        ])
