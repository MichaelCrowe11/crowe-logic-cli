from __future__ import annotations

from typing import Optional


def get_secret_from_keyvault(vault_url: str, secret_name: str) -> Optional[str]:
    """
    Retrieve a secret from Azure Key Vault.
    
    Args:
        vault_url: The Key Vault URL (e.g., https://my-vault.vault.azure.net/)
        secret_name: The name of the secret to retrieve
        
    Returns:
        The secret value, or None if retrieval fails
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
        
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        secret = client.get_secret(secret_name)
        return secret.value
    except ImportError:
        print("Warning: azure-identity and azure-keyvault-secrets packages required for Key Vault support")
        return None
    except Exception as e:
        print(f"Warning: Failed to retrieve secret from Key Vault: {e}")
        return None


def resolve_secret(value: str) -> str:
    """
    Resolve a value that may be a Key Vault reference.

    Supports keyvault:// URL format:
    - keyvault://vault-name/secret-name
    - keyvault://vault-name.vault.azure.net/secret-name

    If the value doesn't start with keyvault://, returns it unchanged.

    Args:
        value: The value to resolve (may be a keyvault:// URL)

    Returns:
        The resolved value (secret from Key Vault or original value)
    """
    if not value.startswith("keyvault://"):
        return value

    # Parse keyvault://vault-name/secret-name
    parts = value[11:].split("/", 1)  # Remove "keyvault://"
    if len(parts) != 2:
        return value  # Invalid format, return as-is

    vault_name, secret_name = parts

    # Build vault URL
    if ".vault.azure.net" in vault_name:
        vault_url = f"https://{vault_name}/"
    else:
        vault_url = f"https://{vault_name}.vault.azure.net/"

    result = get_secret_from_keyvault(vault_url, secret_name)
    return result if result else value


def resolve_api_key(
    api_key: Optional[str] = None,
    keyvault_url: Optional[str] = None,
    keyvault_secret: Optional[str] = None,
) -> Optional[str]:
    """
    Resolve API key from direct value or Key Vault.

    Priority:
    1. Direct api_key if provided
    2. Key Vault secret if keyvault_url and keyvault_secret are provided

    Args:
        api_key: Direct API key value
        keyvault_url: Azure Key Vault URL
        keyvault_secret: Name of the secret in Key Vault

    Returns:
        Resolved API key or None
    """
    if api_key:
        return api_key

    if keyvault_url and keyvault_secret:
        return get_secret_from_keyvault(keyvault_url, keyvault_secret)

    return None
