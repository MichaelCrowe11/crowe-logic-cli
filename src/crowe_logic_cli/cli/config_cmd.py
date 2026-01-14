from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path

from crowe_logic_cli.config import load_config
from crowe_logic_cli.config_file import _find_config_file, load_config_file


app = typer.Typer(add_completion=False, help="Manage CLI configuration")
console = Console()


@app.command()
def show() -> None:
    """Show current configuration."""
    config_path = _find_config_file()
    
    table = Table(title="Crowe Logic CLI Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    if config_path:
        table.add_row("Config file", str(config_path))
    else:
        table.add_row("Config file", "[dim]Not found[/dim]")
    
    try:
        config = load_config()
        table.add_row("Provider", config.provider)
        
        if config.azure:
            table.add_row("Azure endpoint", config.azure.endpoint)
            table.add_row("Azure deployment", config.azure.deployment)
            table.add_row("Azure API version", config.azure.api_version)
            # Mask API key
            key = config.azure.api_key
            masked = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "****"
            table.add_row("Azure API key", masked)
        
        if config.openai_compatible:
            table.add_row("Base URL", config.openai_compatible.base_url)
            table.add_row("Model", config.openai_compatible.model)
    except Exception as e:
        table.add_row("Error", f"[red]{e}[/red]")
    
    console.print(table)


@app.command()
def init() -> None:
    """Create a new configuration file."""
    config_path = Path.home() / ".crowelogic.toml"
    
    if config_path.exists():
        console.print(f"[yellow]Config already exists: {config_path}[/yellow]")
        if not typer.confirm("Overwrite?"):
            raise typer.Exit(0)
    
    template = '''# Crowe Logic CLI Configuration

provider = "azure"

[azure]
endpoint = "https://YOUR-RESOURCE.cognitiveservices.azure.com/"
deployment = "claude-opus-4-5"
api_key = "YOUR-API-KEY"
api_version = "2024-02-15-preview"

# Optional: Use Key Vault for API key
# api_key = "keyvault://your-vault/secret-name"
'''
    
    config_path.write_text(template)
    console.print(f"[green]Created config file: {config_path}[/green]")
    console.print("[dim]Edit the file to add your Azure credentials.[/dim]")


@app.command()
def path() -> None:
    """Show path to config file."""
    config_path = _find_config_file()
    if config_path:
        console.print(str(config_path))
    else:
        console.print("[dim]No config file found[/dim]")
        console.print(f"[dim]Expected: ~/.crowelogic.toml[/dim]")
