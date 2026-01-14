from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.base import coerce_messages
from crowe_logic_cli.providers.factory import create_provider


app = typer.Typer(add_completion=False, help="Interactive selection and clipboard operations")
console = Console()


def get_clipboard_content() -> str:
    """Get content from system clipboard."""
    try:
        import subprocess
        import sys

        if sys.platform == "darwin":
            result = subprocess.run(["pbpaste"], capture_output=True, text=True)
            return result.stdout
        elif sys.platform == "linux":
            result = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                                   capture_output=True, text=True)
            return result.stdout
        elif sys.platform == "win32":
            result = subprocess.run(["powershell", "-command", "Get-Clipboard"],
                                   capture_output=True, text=True)
            return result.stdout
        else:
            return ""
    except Exception:
        return ""


def set_clipboard_content(content: str) -> bool:
    """Set content to system clipboard."""
    try:
        import subprocess
        import sys

        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=content, text=True, check=True)
            return True
        elif sys.platform == "linux":
            subprocess.run(["xclip", "-selection", "clipboard"],
                          input=content, text=True, check=True)
            return True
        elif sys.platform == "win32":
            subprocess.run(["powershell", "-command", f"Set-Clipboard -Value '{content}'"],
                          check=True)
            return True
        else:
            return False
    except Exception:
        return False


@app.command()
def clipboard(
    action: str = typer.Option(
        "explain", "--action", "-a",
        help="Action: explain, review, improve, summarize"
    ),
) -> None:
    """Analyze code or text from clipboard."""
    content = get_clipboard_content()

    if not content.strip():
        console.print("[yellow]Clipboard is empty or could not be read.[/yellow]")
        raise typer.Exit(1)

    action_prompts = {
        "explain": "Explain what this code/text does:",
        "review": "Review this code for quality and issues:",
        "improve": "Suggest improvements for this code/text:",
        "summarize": "Summarize this content:",
    }

    prompt = f"""{action_prompts.get(action, action_prompts["explain"])}

{content[:6000]}
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Clipboard Analysis ({action})[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def transform(
    instruction: str = typer.Argument(..., help="Transformation instruction"),
    copy_result: bool = typer.Option(
        False, "--copy", "-c",
        help="Copy result to clipboard"
    ),
) -> None:
    """Transform clipboard content based on instruction."""
    content = get_clipboard_content()

    if not content.strip():
        console.print("[yellow]Clipboard is empty or could not be read.[/yellow]")
        raise typer.Exit(1)

    prompt = f"""Transform the following content according to this instruction:
"{instruction}"

Content to transform:
{content[:6000]}

Provide only the transformed result, no explanation.
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel("[bold cyan]Transformation Result[/bold cyan]"))

    result = ""
    for chunk in provider.stream(messages):
        console.print(chunk, end="")
        result += chunk
    console.print()

    if copy_result and result:
        if set_clipboard_content(result):
            console.print("\n[green]Result copied to clipboard.[/green]")
        else:
            console.print("\n[yellow]Could not copy to clipboard.[/yellow]")


@app.command()
def diff(
    description: str = typer.Option(
        None, "--description", "-d",
        help="Description of the change made"
    ),
) -> None:
    """Explain a diff/patch from clipboard."""
    content = get_clipboard_content()

    if not content.strip():
        console.print("[yellow]Clipboard is empty or could not be read.[/yellow]")
        raise typer.Exit(1)

    context = f"\nContext: {description}" if description else ""

    prompt = f"""Explain this diff/patch in plain English.
{context}

What changed, why might it matter, and are there any potential issues?

Diff:
{content[:6000]}
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel("[bold cyan]Diff Explanation[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()
