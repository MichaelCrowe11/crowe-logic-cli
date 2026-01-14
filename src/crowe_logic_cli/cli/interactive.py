from __future__ import annotations

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional, List

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.base import Message
from crowe_logic_cli.providers.factory import create_provider
from crowe_logic_cli.cli.history import save_conversation


app = typer.Typer(add_completion=False, help="Interactive multi-turn chat session")
console = Console()

SYSTEM_PROMPT = """You are a helpful AI assistant for Crowe Logic. You assist with software engineering tasks, code review, architecture decisions, and developer productivity. Be concise and actionable."""


def _render_response(content: str) -> None:
    """Render assistant response as markdown in a panel."""
    md = Markdown(content)
    console.print(Panel(md, title="[bold cyan]Assistant[/bold cyan]", border_style="cyan"))


@app.command()
def run(
    system: Optional[str] = typer.Option(
        None, "--system", "-s", help="Custom system prompt (overrides default)"
    ),
    no_stream: bool = typer.Option(
        False, "--no-stream", help="Disable streaming responses"
    ),
) -> None:
    """Start an interactive chat session."""
    config = load_config()
    provider = create_provider(config)

    console.print(
        Panel(
            "[bold green]Crowe Logic Interactive Chat[/bold green]\n"
            f"Provider: [cyan]{provider.name()}[/cyan]\n\n"
            "Commands:\n"
            "  [dim]/clear[/dim]  - Clear conversation history\n"
            "  [dim]/save[/dim]   - Save conversation\n"
            "  [dim]/exit[/dim]   - Exit the session\n"
            "  [dim]/system[/dim] - Show current system prompt",
            border_style="green",
        )
    )

    system_prompt = system or SYSTEM_PROMPT
    messages: List[Message] = [{"role": "system", "content": system_prompt}]
    
    total_input_tokens = 0
    total_output_tokens = 0

    while True:
        try:
            user_input = Prompt.ask("\n[bold yellow]You[/bold yellow]")
        except (KeyboardInterrupt, EOFError):
            if total_input_tokens > 0 or total_output_tokens > 0:
                console.print(f"\n[dim]Session totals: {total_input_tokens} in / {total_output_tokens} out / {total_input_tokens + total_output_tokens} total tokens[/dim]")
            console.print("\n[dim]Goodbye![/dim]")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # Handle commands
        if user_input.lower() == "/exit":
            console.print("[dim]Goodbye![/dim]")
            break
        if user_input.lower() == "/clear":
            messages = [{"role": "system", "content": system_prompt}]
            console.print("[dim]Conversation cleared.[/dim]")
            continue
        if user_input.lower() == "/save":
            name = Prompt.ask("Save as", default=f"conversation_{len(messages)}")
            filepath = save_conversation(messages, name)
            console.print(f"[green]Saved to {filepath}[/green]")
            continue
        if user_input.lower() == "/system":
            console.print(Panel(system_prompt, title="System Prompt", border_style="dim"))
            continue

        # Add user message
        messages.append({"role": "user", "content": user_input})

        # Get response (streaming or non-streaming)
        try:
            if no_stream or not hasattr(provider, "chat_stream"):
                with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                    response = provider.chat(messages)
                messages.append({"role": "assistant", "content": response.content})
                _render_response(response.content)
                
                # Track usage
                if response.usage:
                    total_input_tokens += response.usage.input_tokens
                    total_output_tokens += response.usage.output_tokens
                    console.print(
                        f"[dim]Tokens: {response.usage.input_tokens} in / "
                        f"{response.usage.output_tokens} out / "
                        f"{response.usage.total_tokens} total[/dim]"
                    )
            else:
                # Stream response
                console.print("\n[bold cyan]Assistant[/bold cyan]")
                full_response = ""
                fallback_usage = None
                try:
                    for chunk in provider.chat_stream(messages):
                        console.print(chunk, end="")
                        full_response += chunk
                except NotImplementedError:
                    # Fallback to non-streaming
                    with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                        response = provider.chat(messages)
                    full_response = response.content
                    fallback_usage = response.usage
                    console.print(full_response)

                console.print()  # New line after streaming
                messages.append({"role": "assistant", "content": full_response})

                # Track usage - use actual if available from fallback, otherwise estimate
                if fallback_usage:
                    total_input_tokens += fallback_usage.input_tokens
                    total_output_tokens += fallback_usage.output_tokens
                    console.print(
                        f"[dim]Tokens: {fallback_usage.input_tokens} in / "
                        f"{fallback_usage.output_tokens} out / "
                        f"{fallback_usage.total_tokens} total[/dim]"
                    )
                elif full_response:
                    # Estimate tokens for streaming (rough approximation: ~4 chars per token)
                    # Note: Streaming APIs don't return usage info; this is an estimate
                    estimated_output = len(full_response) // 4
                    input_chars = sum(len(m["content"]) for m in messages[:-1])
                    estimated_input = input_chars // 4
                    total_input_tokens += estimated_input
                    total_output_tokens += estimated_output
                    console.print(f"[dim]Tokens (est): ~{estimated_input} in / ~{estimated_output} out[/dim]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            # Remove the failed user message
            messages.pop()
