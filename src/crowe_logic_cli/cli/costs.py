"""Cost tracking CLI commands."""
from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from crowe_logic_cli.cost_tracker import get_tracker
from crowe_logic_cli.output import OutputFormat, print_output

app = typer.Typer(help="View and manage usage costs")
console = Console()


@app.command("summary")
def show_summary(
    days: Optional[int] = typer.Option(None, "--days", "-d", help="Limit to last N days"),
    output: str = typer.Option("text", "--output", "-o", help="Output format: text, json"),
) -> None:
    """Show usage cost summary."""
    tracker = get_tracker()

    if output.lower() == "json":
        summary = tracker.get_summary(days=days)
        data = {
            "total_input_tokens": summary.total_input_tokens,
            "total_output_tokens": summary.total_output_tokens,
            "total_cost_usd": summary.total_cost_usd,
            "request_count": summary.request_count,
            "by_model": summary.by_model,
            "by_day": summary.by_day,
        }
        print_output(data, OutputFormat.JSON, console=console)
    else:
        tracker.print_summary(console=console, days=days)


@app.command("clear")
def clear_usage(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Clear all usage records."""
    if not force:
        confirm = typer.confirm("Are you sure you want to clear all usage records?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    tracker = get_tracker()
    tracker.clear()
    console.print("[green]✓ Usage records cleared[/green]")


@app.command("today")
def show_today() -> None:
    """Show today's usage."""
    tracker = get_tracker()
    tracker.print_summary(console=console, days=1)


@app.command("week")
def show_week() -> None:
    """Show this week's usage."""
    tracker = get_tracker()
    tracker.print_summary(console=console, days=7)


@app.command("month")
def show_month() -> None:
    """Show this month's usage."""
    tracker = get_tracker()
    tracker.print_summary(console=console, days=30)
