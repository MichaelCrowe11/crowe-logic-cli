"""License management CLI commands."""
from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from crowe_logic_cli.licensing import get_license_manager
from crowe_logic_cli.output import OutputFormat, print_output

app = typer.Typer(help="Manage your Crowe Logic license")
console = Console()


@app.command("status")
def show_status(
    output: str = typer.Option("text", "--output", "-o", help="Output format: text, json"),
) -> None:
    """Show current license status."""
    manager = get_license_manager()

    if output.lower() == "json":
        license_info = manager.license
        data = {
            "tier": license_info.tier.value,
            "email": license_info.email,
            "organization": license_info.organization,
            "expires_at": license_info.expires_at,
            "is_valid": license_info.is_valid,
            "is_expired": license_info.is_expired,
        }
        print_output(data, OutputFormat.JSON, console=console)
    else:
        manager.print_status(console=console)


@app.command("activate")
def activate_license(
    license_key: str = typer.Argument(..., help="Your license key"),
) -> None:
    """Activate a license key."""
    manager = get_license_manager()
    success, message = manager.activate(license_key)

    if success:
        console.print(f"[green]✓ {message}[/green]")
        console.print("\n[dim]Run 'crowelogic license status' to see your new features.[/dim]")
    else:
        console.print(f"[red]✗ {message}[/red]")
        raise typer.Exit(1)


@app.command("deactivate")
def deactivate_license(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Deactivate current license."""
    if not force:
        confirm = typer.confirm("Are you sure you want to deactivate your license?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    manager = get_license_manager()
    manager.deactivate()
    console.print("[green]✓ License deactivated. You are now on the Free tier.[/green]")


@app.command("upgrade")
def show_upgrade() -> None:
    """Show upgrade options."""
    console.print("\n[bold cyan]Crowe Logic CLI - Pricing[/bold cyan]\n")

    console.print("[bold]Free Tier[/bold] - $0/month")
    console.print("  • Basic chat and ask commands")
    console.print("  • 50 requests/day")
    console.print("  • 7-day history retention")
    console.print()

    console.print("[bold green]Pro Tier[/bold green] - $19/month")
    console.print("  • Everything in Free, plus:")
    console.print("  • Quantum-enhanced reasoning")
    console.print("  • Code analysis & review")
    console.print("  • Molecular dynamics")
    console.print("  • Research paper analysis")
    console.print("  • 1,000 requests/day")
    console.print("  • 90-day history retention")
    console.print("  • Priority support")
    console.print()

    console.print("[bold gold1]Enterprise Tier[/bold gold1] - Custom pricing")
    console.print("  • Everything in Pro, plus:")
    console.print("  • SSO integration")
    console.print("  • Audit logs")
    console.print("  • Team sharing")
    console.print("  • Custom models")
    console.print("  • API access")
    console.print("  • Unlimited requests")
    console.print("  • Dedicated support")
    console.print()

    console.print("[link=https://crowelogic.com/pricing]Visit https://crowelogic.com/pricing to upgrade[/link]")
    console.print("\nOr contact [link=mailto:sales@crowelogic.com]sales@crowelogic.com[/link] for Enterprise inquiries.")


@app.command("features")
def list_features() -> None:
    """List all available features by tier."""
    from crowe_logic_cli.licensing import (
        FREE_FEATURES,
        PRO_FEATURES,
        ENTERPRISE_ONLY_FEATURES,
        LicenseTier,
    )
    from rich.table import Table

    table = Table(title="Features by Tier")
    table.add_column("Feature", style="cyan")
    table.add_column("Free", justify="center")
    table.add_column("Pro", justify="center")
    table.add_column("Enterprise", justify="center")

    all_features = sorted(FREE_FEATURES | PRO_FEATURES | ENTERPRISE_ONLY_FEATURES)

    for feature in all_features:
        free = "[green]✓[/green]" if feature in FREE_FEATURES else "[dim]–[/dim]"
        pro = "[green]✓[/green]" if feature in FREE_FEATURES or feature in PRO_FEATURES else "[dim]–[/dim]"
        enterprise = "[green]✓[/green]"  # Enterprise has all features
        table.add_row(feature, free, pro, enterprise)

    console.print(table)
