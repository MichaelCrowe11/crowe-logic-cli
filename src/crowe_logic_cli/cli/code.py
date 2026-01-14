from __future__ import annotations

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from typing import Optional

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.base import coerce_messages
from crowe_logic_cli.providers.factory import create_provider


app = typer.Typer(add_completion=False, help="Code analysis and generation")
console = Console()


@app.command()
def explain(
    file: Path = typer.Argument(..., help="Code file to explain"),
    detail: str = typer.Option(
        "medium", "--detail", "-d",
        help="Detail level: brief, medium, detailed"
    ),
) -> None:
    """Explain what a piece of code does."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()
    language = file.suffix.lstrip(".") or "unknown"

    detail_instruction = {
        "brief": "Provide a concise 2-3 sentence explanation.",
        "medium": "Provide a paragraph explanation covering main functionality.",
        "detailed": "Provide a comprehensive explanation of all components.",
    }.get(detail, "Provide a paragraph explanation covering main functionality.")

    prompt = f"""Explain this {language} code.
{detail_instruction}

```{language}
{content[:6000]}
```
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Code Explanation: {file.name}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def review(
    file: Path = typer.Argument(..., help="Code file to review"),
    focus: Optional[str] = typer.Option(
        None, "--focus", "-f",
        help="Focus area: security, performance, style, all"
    ),
) -> None:
    """Review code for quality, security, and best practices."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()
    language = file.suffix.lstrip(".") or "unknown"

    focus_instruction = ""
    if focus:
        focus_instruction = f"\nFocus particularly on: {focus}"

    prompt = f"""Review this {language} code for quality and best practices.
{focus_instruction}

Provide:
1. Overall assessment
2. Strengths
3. Issues found (bugs, security, performance)
4. Suggested improvements
5. Code style observations

```{language}
{content[:6000]}
```
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Code Review: {file.name}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def refactor(
    file: Path = typer.Argument(..., help="Code file to refactor"),
    goal: str = typer.Option(
        "readability", "--goal", "-g",
        help="Refactoring goal: readability, performance, modularity, testability"
    ),
) -> None:
    """Suggest refactoring improvements for code."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()
    language = file.suffix.lstrip(".") or "unknown"

    prompt = f"""Suggest refactoring improvements for this {language} code.
Goal: {goal}

Provide:
1. Current issues affecting {goal}
2. Specific refactoring suggestions with code examples
3. Before/after comparisons for key changes
4. Expected benefits

```{language}
{content[:6000]}
```
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Refactoring Suggestions: {file.name}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def generate(
    description: str = typer.Argument(..., help="Description of code to generate"),
    language: str = typer.Option(
        "python", "--language", "-l",
        help="Target programming language"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file path"
    ),
) -> None:
    """Generate code from a natural language description."""
    prompt = f"""Generate {language} code for the following:

{description}

Requirements:
1. Write clean, idiomatic {language} code
2. Include necessary imports
3. Add docstrings/comments for clarity
4. Handle edge cases appropriately
5. Follow best practices for {language}
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Code Generation ({language})[/bold cyan]"))

    generated_code = ""
    for chunk in provider.stream(messages):
        console.print(chunk, end="")
        generated_code += chunk
    console.print()

    if output:
        output.write_text(generated_code)
        console.print(f"\n[green]Code saved to: {output}[/green]")


@app.command()
def test(
    file: Path = typer.Argument(..., help="Code file to generate tests for"),
    framework: str = typer.Option(
        "pytest", "--framework", "-f",
        help="Test framework: pytest, unittest, jest, mocha"
    ),
) -> None:
    """Generate unit tests for code."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()
    language = file.suffix.lstrip(".") or "unknown"

    prompt = f"""Generate comprehensive unit tests for this {language} code using {framework}.

Include:
1. Tests for all public functions/methods
2. Edge case testing
3. Error handling tests
4. Setup/teardown as needed
5. Clear test names and docstrings

```{language}
{content[:6000]}
```
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Test Generation: {file.name}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()
