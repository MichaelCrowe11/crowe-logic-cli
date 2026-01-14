"""Pytest fixtures for crowe-logic-cli tests."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for config files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    yield config_dir


@pytest.fixture
def temp_history_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for history files."""
    history_dir = tmp_path / ".crowelogic" / "history"
    history_dir.mkdir(parents=True)
    yield history_dir


@pytest.fixture
def mock_env_clean() -> Generator[None, None, None]:
    """Clear all CROWE_ environment variables and mock config file to not be found."""
    original_env = os.environ.copy()
    crowe_vars = [k for k in os.environ if k.startswith("CROWE_")]
    for var in crowe_vars:
        del os.environ[var]

    # Also mock the config file finder to return None (no config file)
    # This ensures tests use only environment variables
    with patch("crowe_logic_cli.config_file._find_config_file", return_value=None):
        yield

    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_config_toml() -> str:
    """Sample config TOML content."""
    return '''
provider = "azure"

[azure]
endpoint = "https://test-resource.openai.azure.com"
deployment = "gpt-4"
api_key = "test-api-key"
api_version = "2024-02-15-preview"
'''


@pytest.fixture
def sample_azure_ai_config_toml() -> str:
    """Sample Azure AI inference config TOML content."""
    return '''
provider = "azure_ai_inference"

[azure_ai_inference]
endpoint = "https://test-model.eastus.models.ai.azure.com"
model = "claude-3-5-sonnet"
api_key = "test-api-key"
api_version = "2024-05-01-preview"
'''


@pytest.fixture
def sample_openai_config_toml() -> str:
    """Sample OpenAI-compatible config TOML content."""
    return '''
provider = "openai_compatible"

[openai_compatible]
base_url = "https://api.openai.com/v1"
model = "gpt-4-turbo"
api_key = "sk-test-key"
'''


@pytest.fixture
def sample_conversation() -> Dict[str, Any]:
    """Sample conversation data for history tests."""
    return {
        "timestamp": "2026-01-12T10:30:00",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there! How can I help you today?"},
        ],
    }
