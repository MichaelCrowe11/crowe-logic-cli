# Copyright 2024-2026 Michael Benjamin Crowe
# Licensed under the Apache License, Version 2.0

from __future__ import annotations

import json
import httpx

from crowe_logic_cli.providers.base import ChatProvider, ChatResponse, Message, UsageInfo


class AzureAIInferenceProvider(ChatProvider):
    """Provider for Azure AI Services with Claude models (Anthropic Messages API format)."""

    def __init__(self, endpoint: str, api_key: str, model: str, api_version: str = "2024-05-01-preview") -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._api_version = api_version

    def name(self) -> str:
        return "azure_ai_inference"

    def _chat_url(self) -> str:
        # Azure AI Services uses /anthropic/v1/messages for Claude models
        return f"{self._endpoint}/anthropic/v1/messages"

    def _headers(self) -> dict:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Convert messages to Anthropic format, extracting system prompt."""
        system = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        return system, anthropic_messages

    def chat(self, messages: list[Message]) -> ChatResponse:
        url = self._chat_url()
        params = {"api-version": self._api_version}
        headers = self._headers()

        system, anthropic_messages = self._convert_messages(messages)

        # Anthropic Messages API format
        payload = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": 4096,
        }

        if system:
            payload["system"] = system

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, params=params, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Anthropic response format
        content_blocks = data.get("content", [])
        content = ""
        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text", "")

        # Extract usage information
        usage_data = data.get("usage", {})
        usage = None
        if usage_data:
            usage = UsageInfo(
                input_tokens=usage_data.get("input_tokens", 0),
                output_tokens=usage_data.get("output_tokens", 0),
            )

        return ChatResponse(content=content, usage=usage)

    def healthcheck(self) -> None:
        self.chat([
            {"role": "user", "content": "Respond with: OK"},
        ])

    def chat_stream(self, messages: list[Message]):
        """Stream chat response chunks from Azure AI (Anthropic format)."""
        url = self._chat_url()
        params = {"api-version": self._api_version}
        headers = self._headers()

        system, anthropic_messages = self._convert_messages(messages)

        # Anthropic streaming format
        payload = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": 4096,
            "stream": True,
        }

        if system:
            payload["system"] = system

        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, params=params, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line.strip():
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("type", "")

                            # Anthropic streaming events
                            if event_type == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
