from __future__ import annotations

from crowe_logic_cli.config import AppConfig
from crowe_logic_cli.providers.base import ChatProvider
from crowe_logic_cli.providers.azure_openai import AzureOpenAIProvider
from crowe_logic_cli.providers.azure_anthropic import AzureAnthropicProvider
from crowe_logic_cli.providers.azure_ai_inference import AzureAIInferenceProvider
from crowe_logic_cli.providers.openai_compatible import OpenAICompatibleProvider


def _is_claude_deployment(deployment: str) -> bool:
    """Check if deployment name indicates a Claude/Anthropic model."""
    deployment_lower = deployment.lower()
    return any(name in deployment_lower for name in ["claude", "anthropic", "opus", "sonnet", "haiku"])


def create_provider(config: AppConfig) -> ChatProvider:
    if config.provider == "azure":
        if not config.azure:
            raise ValueError("Azure config missing")
        # Auto-detect Claude models and use Anthropic provider
        if _is_claude_deployment(config.azure.deployment):
            return AzureAnthropicProvider(config.azure)
        return AzureOpenAIProvider(config.azure)

    if config.provider == "azure_anthropic":
        if not config.azure:
            raise ValueError("Azure config missing")
        return AzureAnthropicProvider(config.azure)

    if config.provider == "azure_ai_inference":
        if not config.azure_ai_inference:
            raise ValueError("Azure AI inference config missing")
        return AzureAIInferenceProvider(
            endpoint=config.azure_ai_inference.endpoint,
            api_key=config.azure_ai_inference.api_key,
            model=config.azure_ai_inference.model,
            api_version=config.azure_ai_inference.api_version,
        )

    if config.provider == "openai_compatible":
        if not config.openai_compatible:
            raise ValueError("OpenAI-compatible config missing")
        return OpenAICompatibleProvider(config.openai_compatible)

    raise ValueError(f"Unsupported provider: {config.provider}")
