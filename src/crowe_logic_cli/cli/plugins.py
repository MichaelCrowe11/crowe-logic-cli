from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


app = typer.Typer(add_completion=False, help="Discover available plugins, agents, and commands")
console = Console()


def _find_plugins_dir() -> Optional[Path]:
    """Find the plugins directory relative to the repo root."""
    # Try a few common locations
    candidates = [
        Path(__file__).resolve().parents[4] / "plugins",  # If installed editable in repo
        Path.cwd() / "plugins",
        Path.cwd().parent / "plugins",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _scan_plugin(plugin_path: Path) -> Dict[str, List[str]]:
    """Scan a plugin directory for agents, commands, skills, hooks."""
    result: Dict[str, List[str]] = {
        "agents": [],
        "commands": [],
        "skills": [],
        "hooks": [],
    }

    for category in result.keys():
        category_dir = plugin_path / category
        if category_dir.is_dir():
            for item in category_dir.iterdir():
                if item.suffix == ".md" or item.is_dir():
                    result[category].append(item.stem)

    return result


@app.command("list")
def list_plugins() -> None:
    """List all available plugins and their contents."""
    plugins_dir = _find_plugins_dir()

    if plugins_dir is None:
        console.print("[yellow]Could not find plugins directory.[/yellow]")
        console.print("Make sure you're in the claude-code/code workspace or a subdirectory.")
        raise typer.Exit(1)

    console.print(Panel(f"[bold]Plugins Directory[/bold]: {plugins_dir}", border_style="blue"))

    # Scan each plugin
    plugins = sorted([p for p in plugins_dir.iterdir() if p.is_dir() and not p.name.startswith(".")])

    table = Table(title="Available Plugins", show_header=True, header_style="bold cyan")
    table.add_column("Plugin", style="green")
    table.add_column("Agents", justify="right")
    table.add_column("Commands", justify="right")
    table.add_column("Skills", justify="right")
    table.add_column("Hooks", justify="right")

    for plugin_path in plugins:
        contents = _scan_plugin(plugin_path)
        table.add_row(
            plugin_path.name,
            str(len(contents["agents"])) if contents["agents"] else "-",
            str(len(contents["commands"])) if contents["commands"] else "-",
            str(len(contents["skills"])) if contents["skills"] else "-",
            str(len(contents["hooks"])) if contents["hooks"] else "-",
        )

    console.print(table)


@app.command("show")
def show_plugin(
    name: str = typer.Argument(..., help="Plugin name to inspect"),
) -> None:
    """Show details of a specific plugin."""
    plugins_dir = _find_plugins_dir()

    if plugins_dir is None:
        console.print("[yellow]Could not find plugins directory.[/yellow]")
        raise typer.Exit(1)

    plugin_path = plugins_dir / name
    if not plugin_path.is_dir():
        console.print(f"[red]Plugin '{name}' not found.[/red]")
        raise typer.Exit(1)

    contents = _scan_plugin(plugin_path)

    console.print(Panel(f"[bold green]{name}[/bold green]", border_style="green"))

    # Show README if exists
    readme = plugin_path / "README.md"
    if readme.is_file():
        with open(readme) as f:
            first_lines = "".join(f.readlines()[:10])
        console.print(Panel(first_lines.strip(), title="README (first 10 lines)", border_style="dim"))

    # Show contents
    for category, items in contents.items():
        if items:
            console.print(f"\n[bold cyan]{category.capitalize()}[/bold cyan]")
            for item in items:
                console.print(f"  • {item}")
