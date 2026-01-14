from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm


app = typer.Typer(add_completion=False, help="Interactive configuration wizard")
console = Console()


@app.command()
def run(
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output path for config file (default: ~/.crowelogic.toml)"
    ),
) -> None:
    """Run interactive configuration wizard to set up the CLI."""
    
    console.print(Panel(
        "[bold green]Crowe Logic CLI Configuration Wizard[/bold green]\n\n"
        "This wizard will help you set up your connection to Azure AI endpoints.",
        border_style="green"
    ))
    
    # Determine provider type
    console.print("\n[bold]Step 1: Choose your provider[/bold]")
    console.print("1. Azure AI Inference (Cognitive Services with Claude)")
    console.print("2. Azure OpenAI (GPT models)")
    console.print("3. OpenAI-compatible endpoint")
    
    provider_choice = Prompt.ask("Select provider", choices=["1", "2", "3"], default="1")
    
    config_lines = []
    
    if provider_choice == "1":
        # Azure AI Inference
        console.print("\n[bold]Step 2: Azure AI Inference Configuration[/bold]")
        endpoint = Prompt.ask("Azure endpoint URL", 
                             default="https://your-resource.cognitiveservices.azure.com")
        model = Prompt.ask("Model/deployment name", default="claude-opus-4-5")
        api_version = Prompt.ask("API version", default="2024-05-01-preview")
        
        use_keyvault = Confirm.ask("Store API key in Azure Key Vault?", default=False)
        
        if use_keyvault:
            vault_name = Prompt.ask("Key Vault name")
            secret_name = Prompt.ask("Secret name", default="crowe-api-key")
            api_key = f"keyvault://{vault_name}/{secret_name}"
            
            console.print(f"\n[yellow]Don't forget to store your key:[/yellow]")
            console.print(f"az keyvault secret set --vault-name {vault_name} --name {secret_name} --value YOUR_API_KEY")
        else:
            api_key = Prompt.ask("API key", password=True)
        
        config_lines = [
            'provider = "azure_ai_inference"',
            "",
            "[azure_ai_inference]",
            f'endpoint = "{endpoint}"',
            f'model = "{model}"',
            f'api_key = "{api_key}"',
            f'api_version = "{api_version}"',
        ]
    
    elif provider_choice == "2":
        # Azure OpenAI
        console.print("\n[bold]Step 2: Azure OpenAI Configuration[/bold]")
        endpoint = Prompt.ask("Azure OpenAI endpoint", 
                             default="https://your-resource.openai.azure.com")
        deployment = Prompt.ask("Deployment name")
        api_version = Prompt.ask("API version", default="2024-02-15-preview")
        
        use_keyvault = Confirm.ask("Store API key in Azure Key Vault?", default=False)
        
        if use_keyvault:
            vault_name = Prompt.ask("Key Vault name")
            secret_name = Prompt.ask("Secret name", default="azure-openai-key")
            api_key = f"keyvault://{vault_name}/{secret_name}"
        else:
            api_key = Prompt.ask("API key", password=True)
        
        config_lines = [
            'provider = "azure"',
            "",
            "[azure]",
            f'endpoint = "{endpoint}"',
            f'deployment = "{deployment}"',
            f'api_key = "{api_key}"',
            f'api_version = "{api_version}"',
        ]
    
    else:
        # OpenAI-compatible
        console.print("\n[bold]Step 2: OpenAI-compatible Configuration[/bold]")
        base_url = Prompt.ask("Base URL")
        model = Prompt.ask("Model name")
        api_key = Prompt.ask("API key", password=True)
        
        config_lines = [
            'provider = "openai_compatible"',
            "",
            "[openai_compatible]",
            f'base_url = "{base_url}"',
            f'model = "{model}"',
            f'api_key = "{api_key}"',
        ]
    
    # Determine output path
    if output is None:
        output = Path.home() / ".crowelogic.toml"
    
    # Show preview
    console.print("\n[bold]Configuration Preview:[/bold]")
    console.print(Panel("\n".join(config_lines), border_style="blue"))
    
    # Confirm and write
    if output.exists():
        overwrite = Confirm.ask(f"\n[yellow]{output} already exists. Overwrite?[/yellow]", default=False)
        if not overwrite:
            console.print("[red]Configuration cancelled.[/red]")
            raise typer.Exit(1)
    
    output.write_text("\n".join(config_lines) + "\n")
    console.print(f"\n[green]✓ Configuration saved to {output}[/green]")
    
    # Test connection
    test = Confirm.ask("\nTest connection now?", default=True)
    if test:
        console.print("\n[dim]Running: crowelogic doctor run[/dim]")
        import subprocess
        result = subprocess.run(["crowelogic", "doctor", "run"], capture_output=False)
        if result.returncode == 0:
            console.print("\n[green]✓ Setup complete! Try: crowelogic interactive run[/green]")
        else:
            console.print("\n[yellow]Connection test failed. Check your configuration.[/yellow]")
