from __future__ import annotations

import typer
from rich.console import Console
from typing import Optional

from crowe_logic_cli.config import load_config
from crowe_logic_cli.cost_tracker import get_tracker
from crowe_logic_cli.output import OutputFormat, copy_to_clipboard, print_output
from crowe_logic_cli.providers.base import coerce_messages
from crowe_logic_cli.providers.factory import create_provider
from crowe_logic_cli.retry import RetryConfig, with_retry


app = typer.Typer(add_completion=False, help="Chat with the configured model provider")
console = Console()


@app.command()
def run(
    prompt: str = typer.Argument(..., help="User prompt"),
    system: Optional[str] = typer.Option(
        None, "--system", help="Optional system prompt"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, markdown"
    ),
    copy: bool = typer.Option(
        False, "--copy", "-c", help="Copy response to clipboard"
    ),
    retry: int = typer.Option(
        3, "--retry", "-r", help="Number of retries on failure (0 to disable)"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress retry messages"
    ),
) -> None:
    """Send a chat message and get a response."""
    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt, system=system)

    # Configure retry
    retry_config = RetryConfig(max_retries=retry)

    @with_retry(config=retry_config, console=console, verbose=not quiet)
    def do_chat():
        return provider.chat(messages)

    response = do_chat()

    # Track usage
    if response.usage:
        tracker = get_tracker()
        tracker.record(
            model=getattr(config.azure, "deployment", None)
            or getattr(config.azure_ai_inference, "model", None)
            or getattr(config.openai_compatible, "model", None)
            or "unknown",
            provider=provider.name(),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            command="chat",
        )

    # Format output
    output_format = OutputFormat(output.lower()) if output.lower() in [f.value for f in OutputFormat] else OutputFormat.TEXT

    if output_format == OutputFormat.JSON:
        data = {
            "content": response.content,
            "usage": {
                "input_tokens": response.usage.input_tokens if response.usage else None,
                "output_tokens": response.usage.output_tokens if response.usage else None,
            } if response.usage else None,
        }
        print_output(data, output_format, console=console)
    else:
        console.print(response.content)

    if copy:
        if copy_to_clipboard(response.content):
            console.print("[dim green]✓ Copied to clipboard[/dim green]")
        else:
            console.print("[dim red]✗ Failed to copy to clipboard[/dim red]")
