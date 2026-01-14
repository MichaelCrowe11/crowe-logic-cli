from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from crowe_logic_cli.config_file import get_config_value


ProviderName = Literal["azure", "azure_ai_inference", "openai_compatible"]


@dataclass(frozen=True)
class AzureConfig:
    endpoint: str
    api_key: str
    deployment: str
    api_version: str = "2024-02-15-preview"


@dataclass(frozen=True)
class AzureAIInferenceConfig:
    endpoint: str
    api_key: str
    model: str
    api_version: str = "2024-05-01-preview"


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    model: str


@dataclass(frozen=True)
class AppConfig:
    provider: ProviderName
    azure: Optional[AzureConfig] = None
    azure_ai_inference: Optional[AzureAIInferenceConfig] = None
    openai_compatible: Optional[OpenAICompatibleConfig] = None


def load_config() -> AppConfig:
    """
    Load config with precedence: env vars > .crowelogic.toml > defaults.
    """
    provider = (get_config_value("provider", "CROWE_PROVIDER") or "azure").lower()
    if provider not in ("azure", "azure_ai_inference", "openai_compatible"):
        raise ValueError(
            "Unsupported provider. Use 'azure', 'azure_ai_inference', or 'openai_compatible'."
        )

    if provider == "azure":
        endpoint = get_config_value("azure.endpoint", "CROWE_AZURE_ENDPOINT")
        deployment = get_config_value("azure.deployment", "CROWE_AZURE_DEPLOYMENT")
        # api_key supports keyvault:// URLs via resolve_secret in get_config_value
        api_key = get_config_value("azure.api_key", "CROWE_AZURE_API_KEY")
        api_version = get_config_value("azure.api_version", "CROWE_AZURE_API_VERSION", "2024-02-15-preview")

        missing = [
            name
            for name, value in (
                ("azure.endpoint / CROWE_AZURE_ENDPOINT", endpoint),
                ("azure.deployment / CROWE_AZURE_DEPLOYMENT", deployment),
                ("azure.api_key / CROWE_AZURE_API_KEY", api_key),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "Missing required config for Azure provider: " + ", ".join(missing)
            )

        return AppConfig(
            provider="azure",
            azure=AzureConfig(
                endpoint=endpoint,  # type: ignore
                api_key=api_key,  # type: ignore
                deployment=deployment,  # type: ignore
                api_version=api_version,  # type: ignore
            ),
        )

    if provider == "azure_ai_inference":
        endpoint = get_config_value("azure_ai_inference.endpoint", "CROWE_AZURE_AI_ENDPOINT")
        model = get_config_value("azure_ai_inference.model", "CROWE_AZURE_AI_MODEL")
        api_key = get_config_value("azure_ai_inference.api_key", "CROWE_AZURE_AI_API_KEY")
        api_version = get_config_value("azure_ai_inference.api_version", "CROWE_AZURE_AI_API_VERSION", "2024-05-01-preview")

        missing = [
            name
            for name, value in (
                ("azure_ai_inference.endpoint / CROWE_AZURE_AI_ENDPOINT", endpoint),
                ("azure_ai_inference.model / CROWE_AZURE_AI_MODEL", model),
                ("azure_ai_inference.api_key / CROWE_AZURE_AI_API_KEY", api_key),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "Missing required config for Azure AI inference provider: " + ", ".join(missing)
            )

        return AppConfig(
            provider="azure_ai_inference",
            azure_ai_inference=AzureAIInferenceConfig(
                endpoint=endpoint,  # type: ignore
                api_key=api_key,  # type: ignore
                model=model,  # type: ignore
                api_version=api_version,  # type: ignore
            ),
        )

    base_url = get_config_value("openai_compatible.base_url", "CROWE_OPENAI_BASE_URL")
    api_key = get_config_value("openai_compatible.api_key", "CROWE_OPENAI_API_KEY")
    model = get_config_value("openai_compatible.model", "CROWE_OPENAI_MODEL")

    missing = [
        name
        for name, value in (
            ("openai_compatible.base_url / CROWE_OPENAI_BASE_URL", base_url),
            ("openai_compatible.api_key / CROWE_OPENAI_API_KEY", api_key),
            ("openai_compatible.model / CROWE_OPENAI_MODEL", model),
        )
        if not value
    ]
    if missing:
        raise ValueError(
            "Missing required config for openai_compatible provider: "
            + ", ".join(missing)
        )

    return AppConfig(
        provider="openai_compatible",
        openai_compatible=OpenAICompatibleConfig(
            base_url=base_url,  # type: ignore
            api_key=api_key,  # type: ignore
            model=model,  # type: ignore
        ),
    )
