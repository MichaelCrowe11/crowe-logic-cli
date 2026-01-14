# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""
Multi-Model Client

Unified interface for communicating with multiple AI providers.
Supports Anthropic (Claude) and OpenAI (GPT) with streaming.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional

import httpx

from ..aicl import AICLMessage, AICLRole, AICLIntent


class Provider(str, Enum):
    """Supported AI providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    AZURE_ANTHROPIC = "azure_anthropic"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    model_id: str
    provider: Provider
    display_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 8192
    temperature: float = 0.7
    capabilities: list[str] = field(default_factory=lambda: ["chat", "code", "reasoning"])

    # Provider-specific settings
    api_version: Optional[str] = None  # For Azure
    deployment_name: Optional[str] = None  # For Azure

    def __post_init__(self) -> None:
        """Load API keys from environment if not provided."""
        if self.api_key is None:
            if self.provider == Provider.ANTHROPIC:
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
            elif self.provider == Provider.OPENAI:
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == Provider.AZURE_OPENAI:
                self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
            elif self.provider == Provider.AZURE_ANTHROPIC:
                self.api_key = os.getenv("AZURE_ANTHROPIC_API_KEY")


# Pre-configured models
CLAUDE_OPUS_45 = ModelConfig(
    model_id="claude-opus-4-5-20251101",
    provider=Provider.ANTHROPIC,
    display_name="Claude Opus 4.5",
    max_tokens=16384,
    capabilities=["chat", "code", "reasoning", "vision", "deep-analysis"],
)

GPT_51_CODEX = ModelConfig(
    model_id="gpt-5.1-codex",
    provider=Provider.OPENAI,
    display_name="GPT-5.1 Codex",
    max_tokens=32768,
    capabilities=["chat", "code", "reasoning", "execution"],
)

GPT_5_TURBO = ModelConfig(
    model_id="gpt-5-turbo",
    provider=Provider.OPENAI,
    display_name="GPT-5 Turbo",
    max_tokens=16384,
    capabilities=["chat", "code", "reasoning", "fast"],
)


class MultiModelClient:
    """
    Unified client for multiple AI providers.
    Handles API differences transparently.
    """

    def __init__(self) -> None:
        self.http_client = httpx.AsyncClient(timeout=120.0)
        self.models: dict[str, ModelConfig] = {}

    def register_model(self, config: ModelConfig) -> None:
        """Register a model configuration."""
        self.models[config.model_id] = config

    def get_model(self, model_id: str) -> ModelConfig:
        """Get a registered model configuration."""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not registered")
        return self.models[model_id]

    async def complete(
        self,
        model_id: str,
        messages: list[dict[str, str]],
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Get a completion from the specified model.
        Returns the full response text.
        """
        config = self.get_model(model_id)

        if config.provider in (Provider.ANTHROPIC, Provider.AZURE_ANTHROPIC):
            return await self._complete_anthropic(config, messages, system, **kwargs)
        elif config.provider in (Provider.OPENAI, Provider.AZURE_OPENAI):
            return await self._complete_openai(config, messages, system, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    async def stream(
        self,
        model_id: str,
        messages: list[dict[str, str]],
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream a completion from the specified model.
        Yields text chunks as they arrive.
        """
        config = self.get_model(model_id)

        if config.provider in (Provider.ANTHROPIC, Provider.AZURE_ANTHROPIC):
            async for chunk in self._stream_anthropic(config, messages, system, **kwargs):
                yield chunk
        elif config.provider in (Provider.OPENAI, Provider.AZURE_OPENAI):
            async for chunk in self._stream_openai(config, messages, system, **kwargs):
                yield chunk
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    async def _complete_anthropic(
        self,
        config: ModelConfig,
        messages: list[dict[str, str]],
        system: Optional[str],
        **kwargs: Any,
    ) -> str:
        """Complete using Anthropic API."""
        url = config.base_url or "https://api.anthropic.com/v1/messages"

        headers = {
            "x-api-key": config.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": config.model_id,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "messages": messages,
        }

        if system:
            payload["system"] = system

        response = await self.http_client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        return data["content"][0]["text"]

    async def _stream_anthropic(
        self,
        config: ModelConfig,
        messages: list[dict[str, str]],
        system: Optional[str],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream using Anthropic API."""
        url = config.base_url or "https://api.anthropic.com/v1/messages"

        headers = {
            "x-api-key": config.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": config.model_id,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "messages": messages,
            "stream": True,
        }

        if system:
            payload["system"] = system

        async with self.http_client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    import json
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if text := delta.get("text"):
                                yield text
                    except json.JSONDecodeError:
                        continue

    async def _complete_openai(
        self,
        config: ModelConfig,
        messages: list[dict[str, str]],
        system: Optional[str],
        **kwargs: Any,
    ) -> str:
        """Complete using OpenAI API."""
        if config.provider == Provider.AZURE_OPENAI:
            url = f"{config.base_url}/openai/deployments/{config.deployment_name}/chat/completions?api-version={config.api_version}"
            headers = {"api-key": config.api_key or ""}
        else:
            url = config.base_url or "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {config.api_key}"}

        headers["content-type"] = "application/json"

        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        openai_messages.extend(messages)

        payload = {
            "model": config.model_id,
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
        }

        response = await self.http_client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    async def _stream_openai(
        self,
        config: ModelConfig,
        messages: list[dict[str, str]],
        system: Optional[str],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream using OpenAI API."""
        if config.provider == Provider.AZURE_OPENAI:
            url = f"{config.base_url}/openai/deployments/{config.deployment_name}/chat/completions?api-version={config.api_version}"
            headers = {"api-key": config.api_key or ""}
        else:
            url = config.base_url or "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {config.api_key}"}

        headers["content-type"] = "application/json"

        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        openai_messages.extend(messages)

        payload = {
            "model": config.model_id,
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
            "stream": True,
        }

        async with self.http_client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    import json
                    try:
                        data = json.loads(line[6:])
                        if choices := data.get("choices"):
                            if delta := choices[0].get("delta"):
                                if content := delta.get("content"):
                                    yield content
                    except json.JSONDecodeError:
                        continue

    async def aicl_exchange(
        self,
        from_model: str,
        to_model: str,
        message: AICLMessage,
        context: str,
    ) -> AICLMessage:
        """
        Send an AICL message from one model to another.
        Returns the receiving model's AICL response.
        """
        system_prompt = f"""You are participating in an AICL (AI Communication Language) conversation.
You are: {to_model}
You are receiving a message from: {from_model}

Respond using AICL format. Structure your response as:
1. State your INTENT (one of: response, critique, revision, validation, code_review, etc.)
2. Provide your CONFIDENCE (0-100%)
3. Give your REASONING
4. Provide your CONTENT

Be direct, precise, and constructive. Focus on advancing the conversation toward the objective."""

        messages = [
            {"role": "user", "content": f"{context}\n\n{message.to_prompt()}"}
        ]

        response_text = await self.complete(to_model, messages, system=system_prompt)

        # Parse AICL response
        return AICLMessage(
            sender_model=to_model,
            sender_role=AICLRole.RESPONDER,
            intent=AICLIntent.RESPONSE,
            content=response_text,
            confidence=0.8,  # TODO: Parse from response
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.http_client.aclose()
