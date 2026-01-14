from __future__ import annotations

import json
from typing import Iterator

import httpx

from crowe_logic_cli.config import AzureConfig
from crowe_logic_cli.providers.base import ChatProvider, ChatResponse, Message


class AzureAnthropicProvider(ChatProvider):
    """Provider for Claude models deployed on Azure AI Foundry."""

    def __init__(self, config: AzureConfig) -> None:
        self._config = config

    def name(self) -> str:
        return "azure-anthropic"

    def _messages_url(self) -> str:
        # Convert cognitiveservices.azure.com to services.ai.azure.com
        endpoint = self._config.endpoint.rstrip("/")
        if "cognitiveservices.azure.com" in endpoint:
            endpoint = endpoint.replace("cognitiveservices.azure.com", "services.ai.azure.com")
        # Azure AI Foundry Anthropic endpoint format: /anthropic/v1/messages
        return f"{endpoint}/anthropic/v1/messages"

    def _build_headers(self) -> dict:
        return {
            "x-api-key": self._config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages: list[Message], stream: bool = False) -> dict:
        system_content = None
        anthropic_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_content = content
            else:
                anthropic_messages.append({"role": role, "content": content})

        payload = {
            "model": self._config.deployment,
            "messages": anthropic_messages,
            "max_tokens": 4096,
            "stream": stream,
        }
        if system_content:
            payload["system"] = system_content
        return payload

    def chat(self, messages: list[Message]) -> ChatResponse:
        url = self._messages_url()
        headers = self._build_headers()
        payload = self._build_payload(messages, stream=False)

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Anthropic response format
        content_blocks = data.get("content") or []
        text_parts = []
        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return ChatResponse(content="".join(text_parts))

    def chat_stream(self, messages: list[Message]) -> Iterator[str]:
        """Stream chat response chunks from Claude."""
        url = self._messages_url()
        headers = self._build_headers()
        payload = self._build_payload(messages, stream=True)

        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str == "[DONE]":
                        break
                    try:
                        event = json.loads(data_str)
                        event_type = event.get("type")
                        if event_type == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                    except json.JSONDecodeError:
                        continue

    def healthcheck(self) -> None:
        self.chat([
            {"role": "user", "content": "Respond with exactly: OK"},
        ])
