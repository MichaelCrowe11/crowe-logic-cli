from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from crowe_logic_cli.keyvault import resolve_secret


CONFIG_FILENAME = ".crowelogic.toml"


def _find_config_file() -> Optional[Path]:
    """Search for config file in cwd and parent directories, then home."""
    cwd = Path.cwd()
    for directory in [cwd, *cwd.parents]:
        candidate = directory / CONFIG_FILENAME
        if candidate.is_file():
            return candidate

    home_config = Path.home() / CONFIG_FILENAME
    if home_config.is_file():
        return home_config

    return None


def load_config_file() -> Dict[str, Any]:
    """Load config from .crowelogic.toml if it exists."""
    path = _find_config_file()
    if path is None:
        return {}

    with open(path, "rb") as f:
        return tomllib.load(f)


def get_config_value(key: str, env_var: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a config value with precedence: env var > config file > default.
    
    Key should be dot-separated for nested access, e.g. "azure.endpoint".
    
    Supports Azure Key Vault references in config file:
    - Format: keyvault://vault-name/secret-name
    - Example: api_key = "keyvault://my-vault/crowe-api-key"
    """
    # Env var takes precedence
    env_value = os.getenv(env_var)
    if env_value and env_value.strip():
        return resolve_secret(env_value.strip())

    # Try config file
    config = load_config_file()
    parts = key.split(".")
    value = config
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
            break

    if value is not None and isinstance(value, str) and value.strip():
        return resolve_secret(value.strip())

    return default
