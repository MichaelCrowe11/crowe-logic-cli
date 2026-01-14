from __future__ import annotations

import typer
from rich.console import Console

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.factory import create_provider
from crowe_logic_cli.diagnostics import diagnose_connection_error, format_validation_error


app = typer.Typer(add_completion=False, help="Validate provider configuration and connectivity")
console = Console()


def _mask(value: str, show_last: int = 4) -> str:
    if len(value) <= show_last:
        return "*" * len(value)
    return "*" * (len(value) - show_last) + value[-show_last:]


@app.command()
def run() -> None:
    try:
        config = load_config()
    except ValueError as e:
        console.print(format_validation_error(e))
        raise typer.Exit(1)
    
    try:
        provider = create_provider(config)
    except Exception as e:
        console.print(f"[red]Error creating provider: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"Provider: {provider.name()}")

    # Print minimal config hints without leaking secrets
    if config.azure:
        console.print(f"Azure endpoint: {config.azure.endpoint}")
        console.print(f"Azure deployment: {config.azure.deployment}")
        console.print(f"Azure api-version: {config.azure.api_version}")
        console.print(f"Azure api-key: {_mask(config.azure.api_key)}")

    if config.openai_compatible:
        console.print(f"Base URL: {config.openai_compatible.base_url}")
        console.print(f"Model: {config.openai_compatible.model}")
        console.print(f"API key: {_mask(config.openai_compatible.api_key)}")

    if config.azure_ai_inference:
        console.print(f"Azure AI endpoint: {config.azure_ai_inference.endpoint}")
        console.print(f"Azure AI model: {config.azure_ai_inference.model}")
        console.print(f"Azure AI api-version: {config.azure_ai_inference.api_version}")
        console.print(f"Azure AI api-key: {_mask(config.azure_ai_inference.api_key)}")

    # Best-effort healthcheck if provider implements it
    healthcheck = getattr(provider, "healthcheck", None)
    if callable(healthcheck):
        console.print("Running healthcheck...")
        try:
            healthcheck()
            console.print("[green]OK[/green]")
        except Exception as e:
            console.print(f"[red]Healthcheck failed[/red]")
            endpoint = ""
            if config.azure:
                endpoint = config.azure.endpoint
            elif config.azure_ai_inference:
                endpoint = config.azure_ai_inference.endpoint
            elif config.openai_compatible:
                endpoint = config.openai_compatible.base_url
            diagnose_connection_error(e, endpoint, provider.name())
            raise typer.Exit(1)
    else:
        console.print("No healthcheck available for this provider")
