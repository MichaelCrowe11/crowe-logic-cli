"""Tests for config loading and validation."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from crowe_logic_cli.config import (
    AppConfig,
    AzureConfig,
    AzureAIInferenceConfig,
    OpenAICompatibleConfig,
    load_config,
)
from crowe_logic_cli.config_file import (
    get_config_value,
    load_config_file,
    _find_config_file,
)


class TestAzureConfig:
    """Test Azure provider configuration."""

    def test_load_azure_config_from_env(self, mock_env_clean: None) -> None:
        """Test loading Azure config from environment variables."""
        os.environ["CROWE_PROVIDER"] = "azure"
        os.environ["CROWE_AZURE_ENDPOINT"] = "https://test.openai.azure.com"
        os.environ["CROWE_AZURE_DEPLOYMENT"] = "gpt-4"
        os.environ["CROWE_AZURE_API_KEY"] = "test-key"

        config = load_config()

        assert config.provider == "azure"
        assert config.azure is not None
        assert config.azure.endpoint == "https://test.openai.azure.com"
        assert config.azure.deployment == "gpt-4"
        assert config.azure.api_key == "test-key"
        assert config.azure.api_version == "2024-02-15-preview"  # default

    def test_load_azure_config_with_custom_api_version(self, mock_env_clean: None) -> None:
        """Test Azure config with custom API version."""
        os.environ["CROWE_PROVIDER"] = "azure"
        os.environ["CROWE_AZURE_ENDPOINT"] = "https://test.openai.azure.com"
        os.environ["CROWE_AZURE_DEPLOYMENT"] = "gpt-4"
        os.environ["CROWE_AZURE_API_KEY"] = "test-key"
        os.environ["CROWE_AZURE_API_VERSION"] = "2024-06-01"

        config = load_config()

        assert config.azure is not None
        assert config.azure.api_version == "2024-06-01"

    def test_azure_config_missing_endpoint(self, mock_env_clean: None) -> None:
        """Test error when Azure endpoint is missing."""
        os.environ["CROWE_PROVIDER"] = "azure"
        os.environ["CROWE_AZURE_DEPLOYMENT"] = "gpt-4"
        os.environ["CROWE_AZURE_API_KEY"] = "test-key"

        with pytest.raises(ValueError, match="Missing required config for Azure"):
            load_config()

    def test_azure_config_missing_deployment(self, mock_env_clean: None) -> None:
        """Test error when Azure deployment is missing."""
        os.environ["CROWE_PROVIDER"] = "azure"
        os.environ["CROWE_AZURE_ENDPOINT"] = "https://test.openai.azure.com"
        os.environ["CROWE_AZURE_API_KEY"] = "test-key"

        with pytest.raises(ValueError, match="Missing required config for Azure"):
            load_config()

    def test_azure_config_missing_api_key(self, mock_env_clean: None) -> None:
        """Test error when Azure API key is missing."""
        os.environ["CROWE_PROVIDER"] = "azure"
        os.environ["CROWE_AZURE_ENDPOINT"] = "https://test.openai.azure.com"
        os.environ["CROWE_AZURE_DEPLOYMENT"] = "gpt-4"

        with pytest.raises(ValueError, match="Missing required config for Azure"):
            load_config()


class TestAzureAIInferenceConfig:
    """Test Azure AI Inference provider configuration."""

    def test_load_azure_ai_config_from_env(self, mock_env_clean: None) -> None:
        """Test loading Azure AI Inference config from environment variables."""
        os.environ["CROWE_PROVIDER"] = "azure_ai_inference"
        os.environ["CROWE_AZURE_AI_ENDPOINT"] = "https://test.models.ai.azure.com"
        os.environ["CROWE_AZURE_AI_MODEL"] = "claude-3-5-sonnet"
        os.environ["CROWE_AZURE_AI_API_KEY"] = "test-key"

        config = load_config()

        assert config.provider == "azure_ai_inference"
        assert config.azure_ai_inference is not None
        assert config.azure_ai_inference.endpoint == "https://test.models.ai.azure.com"
        assert config.azure_ai_inference.model == "claude-3-5-sonnet"
        assert config.azure_ai_inference.api_key == "test-key"

    def test_azure_ai_config_missing_endpoint(self, mock_env_clean: None) -> None:
        """Test error when Azure AI endpoint is missing."""
        os.environ["CROWE_PROVIDER"] = "azure_ai_inference"
        os.environ["CROWE_AZURE_AI_MODEL"] = "claude-3-5-sonnet"
        os.environ["CROWE_AZURE_AI_API_KEY"] = "test-key"

        with pytest.raises(ValueError, match="Missing required config for Azure AI"):
            load_config()


class TestOpenAICompatibleConfig:
    """Test OpenAI-compatible provider configuration."""

    def test_load_openai_config_from_env(self, mock_env_clean: None) -> None:
        """Test loading OpenAI-compatible config from environment variables."""
        os.environ["CROWE_PROVIDER"] = "openai_compatible"
        os.environ["CROWE_OPENAI_BASE_URL"] = "https://api.openai.com/v1"
        os.environ["CROWE_OPENAI_MODEL"] = "gpt-4-turbo"
        os.environ["CROWE_OPENAI_API_KEY"] = "sk-test"

        config = load_config()

        assert config.provider == "openai_compatible"
        assert config.openai_compatible is not None
        assert config.openai_compatible.base_url == "https://api.openai.com/v1"
        assert config.openai_compatible.model == "gpt-4-turbo"
        assert config.openai_compatible.api_key == "sk-test"

    def test_openai_config_missing_base_url(self, mock_env_clean: None) -> None:
        """Test error when OpenAI base_url is missing."""
        os.environ["CROWE_PROVIDER"] = "openai_compatible"
        os.environ["CROWE_OPENAI_MODEL"] = "gpt-4-turbo"
        os.environ["CROWE_OPENAI_API_KEY"] = "sk-test"

        with pytest.raises(ValueError, match="Missing required config for openai_compatible"):
            load_config()


class TestConfigFile:
    """Test config file loading and parsing."""

    def test_find_config_file_in_cwd(
        self, temp_config_dir: Path, sample_config_toml: str
    ) -> None:
        """Test finding config file in current working directory."""
        config_file = temp_config_dir / ".crowelogic.toml"
        config_file.write_text(sample_config_toml)

        with patch("crowe_logic_cli.config_file.Path.cwd", return_value=temp_config_dir):
            found = _find_config_file()

        assert found == config_file

    def test_find_config_file_in_parent(self, tmp_path: Path, sample_config_toml: str) -> None:
        """Test finding config file in parent directory."""
        parent = tmp_path / "parent"
        child = parent / "child"
        child.mkdir(parents=True)

        config_file = parent / ".crowelogic.toml"
        config_file.write_text(sample_config_toml)

        with patch("crowe_logic_cli.config_file.Path.cwd", return_value=child):
            found = _find_config_file()

        assert found == config_file

    def test_find_config_file_not_found(self, tmp_path: Path) -> None:
        """Test when no config file exists."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with patch("crowe_logic_cli.config_file.Path.cwd", return_value=empty_dir):
            with patch("crowe_logic_cli.config_file.Path.home", return_value=tmp_path):
                found = _find_config_file()

        assert found is None

    def test_load_config_file_returns_empty_when_not_found(self, tmp_path: Path) -> None:
        """Test load_config_file returns empty dict when file not found."""
        with patch("crowe_logic_cli.config_file._find_config_file", return_value=None):
            result = load_config_file()

        assert result == {}


class TestConfigValue:
    """Test get_config_value precedence."""

    def test_env_var_takes_precedence(
        self, mock_env_clean: None, temp_config_dir: Path, sample_config_toml: str
    ) -> None:
        """Test that environment variables override config file values."""
        config_file = temp_config_dir / ".crowelogic.toml"
        config_file.write_text(sample_config_toml)

        os.environ["CROWE_AZURE_ENDPOINT"] = "https://env-override.openai.azure.com"

        with patch("crowe_logic_cli.config_file._find_config_file", return_value=config_file):
            value = get_config_value("azure.endpoint", "CROWE_AZURE_ENDPOINT")

        assert value == "https://env-override.openai.azure.com"

    def test_config_file_used_when_no_env_var(
        self, mock_env_clean: None, temp_config_dir: Path, sample_config_toml: str
    ) -> None:
        """Test that config file value is used when env var not set."""
        config_file = temp_config_dir / ".crowelogic.toml"
        config_file.write_text(sample_config_toml)

        with patch("crowe_logic_cli.config_file._find_config_file", return_value=config_file):
            value = get_config_value("azure.endpoint", "CROWE_AZURE_ENDPOINT")

        assert value == "https://test-resource.openai.azure.com"

    def test_default_used_when_nothing_set(self, mock_env_clean: None, tmp_path: Path) -> None:
        """Test that default value is used when nothing else is set."""
        with patch("crowe_logic_cli.config_file._find_config_file", return_value=None):
            value = get_config_value("azure.endpoint", "CROWE_AZURE_ENDPOINT", "default-value")

        assert value == "default-value"

    def test_whitespace_stripped(self, mock_env_clean: None) -> None:
        """Test that whitespace is stripped from values."""
        os.environ["CROWE_TEST_VAR"] = "  https://test.com  "

        value = get_config_value("test", "CROWE_TEST_VAR")

        assert value == "https://test.com"


class TestProviderValidation:
    """Test provider validation."""

    def test_unsupported_provider_raises_error(self, mock_env_clean: None) -> None:
        """Test that unsupported provider raises ValueError."""
        os.environ["CROWE_PROVIDER"] = "unsupported"

        with pytest.raises(ValueError, match="Unsupported provider"):
            load_config()

    def test_default_provider_is_azure(self, mock_env_clean: None) -> None:
        """Test that default provider is azure when not specified."""
        os.environ["CROWE_AZURE_ENDPOINT"] = "https://test.openai.azure.com"
        os.environ["CROWE_AZURE_DEPLOYMENT"] = "gpt-4"
        os.environ["CROWE_AZURE_API_KEY"] = "test-key"

        config = load_config()

        assert config.provider == "azure"


class TestDataclasses:
    """Test config dataclass properties."""

    def test_azure_config_is_frozen(self) -> None:
        """Test that AzureConfig is immutable."""
        config = AzureConfig(
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4",
            api_key="test-key",
        )

        with pytest.raises(AttributeError):
            config.endpoint = "https://new.openai.azure.com"  # type: ignore

    def test_app_config_is_frozen(self) -> None:
        """Test that AppConfig is immutable."""
        config = AppConfig(provider="azure")

        with pytest.raises(AttributeError):
            config.provider = "openai_compatible"  # type: ignore
