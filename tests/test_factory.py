"""Tests for provider factory."""
from __future__ import annotations

import pytest

from crowe_logic_cli.config import (
    AppConfig,
    AzureConfig,
    AzureAIInferenceConfig,
    OpenAICompatibleConfig,
)
from crowe_logic_cli.providers.factory import create_provider, _is_claude_deployment
from crowe_logic_cli.providers.azure_openai import AzureOpenAIProvider
from crowe_logic_cli.providers.azure_anthropic import AzureAnthropicProvider
from crowe_logic_cli.providers.azure_ai_inference import AzureAIInferenceProvider
from crowe_logic_cli.providers.openai_compatible import OpenAICompatibleProvider


class TestClaudeDetection:
    """Test Claude model detection logic."""

    @pytest.mark.parametrize(
        "deployment,expected",
        [
            ("claude-3-5-sonnet", True),
            ("claude-3-opus", True),
            ("claude-3-haiku", True),
            ("anthropic-claude", True),
            ("CLAUDE-SONNET", True),  # case insensitive
            ("my-opus-deployment", True),
            ("gpt-4", False),
            ("gpt-4-turbo", False),
            ("text-embedding-ada", False),
            ("llama-3", False),
            ("claude-wrong", True),  # contains "claude"
        ],
    )
    def test_is_claude_deployment(self, deployment: str, expected: bool) -> None:
        """Test Claude deployment detection."""
        assert _is_claude_deployment(deployment) == expected


class TestAzureProviderFactory:
    """Test Azure provider creation."""

    def test_creates_azure_openai_for_gpt(self) -> None:
        """Test that GPT deployments use Azure OpenAI provider."""
        azure_config = AzureConfig(
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4",
            api_key="test-key",
        )
        config = AppConfig(provider="azure", azure=azure_config)

        provider = create_provider(config)

        assert isinstance(provider, AzureOpenAIProvider)

    def test_creates_azure_anthropic_for_claude(self) -> None:
        """Test that Claude deployments use Azure Anthropic provider."""
        azure_config = AzureConfig(
            endpoint="https://test.openai.azure.com",
            deployment="claude-3-5-sonnet",
            api_key="test-key",
        )
        config = AppConfig(provider="azure", azure=azure_config)

        provider = create_provider(config)

        assert isinstance(provider, AzureAnthropicProvider)

    def test_creates_azure_anthropic_for_opus(self) -> None:
        """Test that Opus deployments use Azure Anthropic provider."""
        azure_config = AzureConfig(
            endpoint="https://test.openai.azure.com",
            deployment="opus-deployment",
            api_key="test-key",
        )
        config = AppConfig(provider="azure", azure=azure_config)

        provider = create_provider(config)

        assert isinstance(provider, AzureAnthropicProvider)

    def test_azure_provider_missing_config_raises(self) -> None:
        """Test error when Azure config is missing."""
        config = AppConfig(provider="azure", azure=None)

        with pytest.raises(ValueError, match="Azure config missing"):
            create_provider(config)


class TestAzureAnthropicProviderFactory:
    """Test explicit Azure Anthropic provider creation."""

    def test_creates_azure_anthropic_explicitly(self) -> None:
        """Test explicit azure_anthropic provider type."""
        azure_config = AzureConfig(
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4",  # even GPT name uses Anthropic provider
            api_key="test-key",
        )
        config = AppConfig(provider="azure_anthropic", azure=azure_config)

        provider = create_provider(config)

        assert isinstance(provider, AzureAnthropicProvider)


class TestAzureAIInferenceProviderFactory:
    """Test Azure AI Inference provider creation."""

    def test_creates_azure_ai_inference_provider(self) -> None:
        """Test Azure AI Inference provider creation."""
        ai_config = AzureAIInferenceConfig(
            endpoint="https://test.models.ai.azure.com",
            model="claude-3-5-sonnet",
            api_key="test-key",
        )
        config = AppConfig(provider="azure_ai_inference", azure_ai_inference=ai_config)

        provider = create_provider(config)

        assert isinstance(provider, AzureAIInferenceProvider)

    def test_azure_ai_inference_missing_config_raises(self) -> None:
        """Test error when Azure AI Inference config is missing."""
        config = AppConfig(provider="azure_ai_inference", azure_ai_inference=None)

        with pytest.raises(ValueError, match="Azure AI inference config missing"):
            create_provider(config)


class TestOpenAICompatibleProviderFactory:
    """Test OpenAI-compatible provider creation."""

    def test_creates_openai_compatible_provider(self) -> None:
        """Test OpenAI-compatible provider creation."""
        openai_config = OpenAICompatibleConfig(
            base_url="https://api.openai.com/v1",
            model="gpt-4-turbo",
            api_key="sk-test",
        )
        config = AppConfig(provider="openai_compatible", openai_compatible=openai_config)

        provider = create_provider(config)

        assert isinstance(provider, OpenAICompatibleProvider)

    def test_openai_compatible_missing_config_raises(self) -> None:
        """Test error when OpenAI-compatible config is missing."""
        config = AppConfig(provider="openai_compatible", openai_compatible=None)

        with pytest.raises(ValueError, match="OpenAI-compatible config missing"):
            create_provider(config)


class TestUnsupportedProvider:
    """Test unsupported provider handling."""

    def test_unsupported_provider_raises(self) -> None:
        """Test that unsupported provider raises ValueError."""
        # Using type: ignore because we're testing invalid input
        config = AppConfig(provider="invalid_provider")  # type: ignore

        with pytest.raises(ValueError, match="Unsupported provider"):
            create_provider(config)
