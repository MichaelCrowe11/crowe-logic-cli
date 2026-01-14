from __future__ import annotations

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from typing import Optional

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.base import coerce_messages
from crowe_logic_cli.providers.factory import create_provider


app = typer.Typer(add_completion=False, help="Research paper analysis and review")
console = Console()


@app.command()
def review(
    file: Path = typer.Argument(..., help="Research paper file to review"),
    focus: Optional[str] = typer.Option(
        None, "--focus", "-f", help="Specific aspect to focus on (methodology, results, citations)"
    ),
) -> None:
    """Review a research paper for quality and completeness."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()

    focus_instruction = f"\nFocus particularly on: {focus}" if focus else ""
    prompt = f"""Review this research paper for scientific rigor, methodology, and completeness.
{focus_instruction}

Paper content:
{content[:8000]}

Provide:
1. Summary of the research
2. Methodology assessment
3. Results validity
4. Strengths and weaknesses
5. Recommendations for improvement
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Research Review: {file.name}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def summarize(
    file: Path = typer.Argument(..., help="Research paper to summarize"),
    length: str = typer.Option(
        "medium", "--length", "-l", help="Summary length: brief, medium, detailed"
    ),
) -> None:
    """Generate a summary of a research paper."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()

    length_instruction = {
        "brief": "Provide a 2-3 sentence summary.",
        "medium": "Provide a 1-2 paragraph summary.",
        "detailed": "Provide a comprehensive summary covering all major sections.",
    }.get(length, "Provide a 1-2 paragraph summary.")

    prompt = f"""Summarize this research paper.
{length_instruction}

Paper content:
{content[:8000]}
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Summary: {file.name}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def extract_citations(
    file: Path = typer.Argument(..., help="Research paper file"),
) -> None:
    """Extract and list all citations from a research paper."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()

    prompt = f"""Extract all citations and references from this research paper.
List them in a structured format with:
- Authors
- Title
- Publication/Journal
- Year
- DOI if available

Paper content:
{content[:10000]}
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel("[bold cyan]Extracted Citations[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()
