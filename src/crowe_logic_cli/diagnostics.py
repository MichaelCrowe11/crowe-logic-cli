from __future__ import annotations

from typing import Optional
from rich.console import Console

console = Console()


def diagnose_connection_error(error: Exception, endpoint: str, provider_name: str) -> None:
    """Provide helpful diagnostics for common connection errors."""
    error_msg = str(error).lower()
    
    console.print(f"\n[red]Connection Error:[/red] {error}")
    console.print(f"\n[yellow]Diagnostics:[/yellow]")
    
    # Common error patterns
    if "404" in error_msg or "not found" in error_msg:
        console.print("  • [dim]404 Not Found - The endpoint path may be incorrect[/dim]")
        console.print(f"  • Current endpoint: [cyan]{endpoint}[/cyan]")
        
        if provider_name == "azure_ai_inference":
            console.print("  • Expected format: [dim]https://<resource>.cognitiveservices.azure.com[/dim]")
            console.print("  • The API path is constructed as: [dim]/models/{model}/messages[/dim]")
        elif provider_name == "azure":
            console.print("  • Expected format: [dim]https://<resource>.openai.azure.com[/dim]")
        
        console.print("\n[yellow]Try:[/yellow]")
        console.print("  1. Verify your endpoint URL in Azure Portal")
        console.print("  2. Check that your deployment name matches exactly")
        console.print("  3. Run: [cyan]az cognitiveservices account show --name <resource>[/cyan]")
    
    elif "401" in error_msg or "403" in error_msg or "unauthorized" in error_msg:
        console.print("  • [dim]Authentication failed - Invalid or missing API key[/dim]")
        console.print("\n[yellow]Try:[/yellow]")
        console.print("  1. Verify your API key in Azure Portal → Keys and Endpoint")
        console.print("  2. Check Key Vault access if using keyvault:// reference")
        console.print("  3. Ensure you're authenticated: [cyan]az login[/cyan]")
        console.print("  4. Regenerate keys if compromised")
    
    elif "429" in error_msg or "rate limit" in error_msg:
        console.print("  • [dim]Rate limit exceeded - Too many requests[/dim]")
        console.print("\n[yellow]Try:[/yellow]")
        console.print("  1. Wait a few seconds and try again")
        console.print("  2. Check your quota in Azure Portal")
        console.print("  3. Consider upgrading your tier")
    
    elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
        console.print("  • [dim]Server error - Azure service may be temporarily unavailable[/dim]")
        console.print("\n[yellow]Try:[/yellow]")
        console.print("  1. Wait a moment and retry")
        console.print("  2. Check Azure Status: [cyan]https://status.azure.com[/cyan]")
    
    elif "timeout" in error_msg or "timed out" in error_msg:
        console.print("  • [dim]Request timed out - Network or service issue[/dim]")
        console.print("\n[yellow]Try:[/yellow]")
        console.print("  1. Check your internet connection")
        console.print("  2. Verify firewall/proxy settings")
        console.print("  3. Try again in a moment")
    
    elif "connection refused" in error_msg or "connection reset" in error_msg:
        console.print("  • [dim]Connection refused - Cannot reach endpoint[/dim]")
        console.print("\n[yellow]Try:[/yellow]")
        console.print("  1. Check endpoint URL for typos")
        console.print("  2. Verify your network connection")
        console.print("  3. Check if VPN/proxy is required")
    
    elif "keyvault" in error_msg or "credential" in error_msg:
        console.print("  • [dim]Azure authentication issue[/dim]")
        console.print("\n[yellow]Try:[/yellow]")
        console.print("  1. Login: [cyan]az login[/cyan]")
        console.print("  2. Check Key Vault permissions: [cyan]az keyvault show --name <vault>[/cyan]")
        console.print("  3. Verify secret exists: [cyan]az keyvault secret show --vault-name <vault> --name <secret>[/cyan]")
    
    else:
        console.print("  • [dim]Unexpected error[/dim]")
        console.print("\n[yellow]Debugging steps:[/yellow]")
        console.print("  1. Run [cyan]crowelogic doctor run[/cyan] for detailed diagnostics")
        console.print("  2. Check your configuration: [cyan]cat ~/.crowelogic.toml[/cyan]")
        console.print("  3. Enable verbose logging if available")


def suggest_config_fix(provider: str, error: Exception) -> None:
    """Suggest configuration fixes based on error."""
    console.print("\n[bold yellow]Configuration Help:[/bold yellow]")
    
    if provider == "azure_ai_inference":
        console.print("Verify your [cyan]~/.crowelogic.toml[/cyan] has:")
        console.print('''
[azure_ai_inference]
endpoint = "https://YOUR-RESOURCE.cognitiveservices.azure.com"
model = "claude-opus-4-5"
api_key = "YOUR-API-KEY"  # or "keyvault://vault-name/secret-name"
api_version = "2024-05-01-preview"
''')
    
    elif provider == "azure":
        console.print("Verify your [cyan]~/.crowelogic.toml[/cyan] has:")
        console.print('''
[azure]
endpoint = "https://YOUR-RESOURCE.openai.azure.com"
deployment = "YOUR-DEPLOYMENT-NAME"
api_key = "YOUR-API-KEY"  # or "keyvault://vault-name/secret-name"
api_version = "2024-02-15-preview"
''')
    
    console.print("\n[dim]Run [cyan]crowelogic config run[/cyan] for an interactive setup wizard.[/dim]")


def format_validation_error(error: ValueError) -> str:
    """Format validation errors with helpful context."""
    msg = str(error)
    
    if "Missing required" in msg:
        return (
            f"[red]{msg}[/red]\n\n"
            "[yellow]Quick fix:[/yellow]\n"
            "Run the configuration wizard: [cyan]crowelogic config run[/cyan]\n"
            "Or manually edit: [cyan]~/.crowelogic.toml[/cyan]"
        )
    
    elif "Unsupported provider" in msg:
        return (
            f"[red]{msg}[/red]\n\n"
            "[yellow]Valid providers:[/yellow]\n"
            "  • azure_ai_inference  (Claude on Azure AI)\n"
            "  • azure              (Azure OpenAI)\n"
            "  • openai_compatible  (Generic OpenAI-compatible API)"
        )
    
    elif "Key Vault" in msg:
        return (
            f"[red]{msg}[/red]\n\n"
            "[yellow]Key Vault setup:[/yellow]\n"
            "1. Login: [cyan]az login[/cyan]\n"
            "2. Create vault: [cyan]az keyvault create --name my-vault --resource-group my-rg[/cyan]\n"
            "3. Store secret: [cyan]az keyvault secret set --vault-name my-vault --name api-key --value YOUR_KEY[/cyan]\n"
            "4. Use in config: [cyan]api_key = \"keyvault://my-vault/api-key\"[/cyan]"
        )
    
    return f"[red]{msg}[/red]"
