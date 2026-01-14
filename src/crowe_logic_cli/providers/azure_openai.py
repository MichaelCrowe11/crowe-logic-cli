from __future__ import annotations

import httpx

from crowe_logic_cli.config import AzureConfig
from crowe_logic_cli.providers.base import ChatProvider, ChatResponse, Message


class AzureOpenAIProvider(ChatProvider):
    def __init__(self, config: AzureConfig) -> None:
        self._config = config

    def name(self) -> str:
        return "azure"

    def _chat_completions_url(self) -> str:
        endpoint = self._config.endpoint.rstrip("/")
        return (
            f"{endpoint}/openai/deployments/{self._config.deployment}/chat/completions"
        )

    def chat(self, messages: list[Message]) -> ChatResponse:
        url = self._chat_completions_url()
        params = {"api-version": self._config.api_version}
        headers = {
            "api-key": self._config.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "messages": messages,
            "temperature": 0.2,
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, params=params, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # OpenAI Chat Completions response shape
        choice0 = (data.get("choices") or [{}])[0]
        message = choice0.get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            content = ""
        return ChatResponse(content=content)

    def healthcheck(self) -> None:
        # Minimal validation: do a 1-token style prompt.
        self.chat([
            {"role": "system", "content": "You are a healthcheck."},
            {"role": "user", "content": "Respond with: OK"},
        ])
