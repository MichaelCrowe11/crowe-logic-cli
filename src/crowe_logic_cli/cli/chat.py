from __future__ import annotations

import typer
from rich.console import Console
from typing import Optional

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.base import coerce_messages
from crowe_logic_cli.providers.factory import create_provider


app = typer.Typer(add_completion=False, help="Chat with the configured model provider")
console = Console()


@app.command()
def run(
    prompt: str = typer.Argument(..., help="User prompt"),
    system: Optional[str] = typer.Option(
        None, "--system", help="Optional system prompt"
    ),
) -> None:
    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt, system=system)
    response = provider.chat(messages)
    console.print(response.content)
