"""Quick one-shot question command."""
import sys
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="Quick one-shot questions")
console = Console()


def get_provider_and_stream(question: str, system: Optional[str] = None):
    """Get provider and stream response."""
    from ..config import load_config
    from ..providers.factory import create_provider
    
    config = load_config()
    provider = create_provider(config)
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": question})
    
    return provider.chat_completion_stream(messages)


@app.callback(invoke_without_command=True)
def ask_default(
    ctx: typer.Context,
    question: Optional[str] = typer.Argument(None, help="Question to ask"),
):
    """Ask a quick one-shot question."""
    if ctx.invoked_subcommand is not None:
        return
    
    if question is None:
        if not sys.stdin.isatty():
            question = sys.stdin.read().strip()
        else:
            console.print("[red]Error: No question provided[/red]")
            raise typer.Exit(1)
    
    for chunk in get_provider_and_stream(question):
        console.print(chunk, end="")
    console.print()


@app.command("explain")
def ask_explain(topic: str = typer.Argument(..., help="Topic to explain")):
    """Get a quick explanation of a topic."""
    system = "Explain concepts clearly and concisely."
    console.print(Panel(f"[bold]{topic}[/bold]", title="[cyan]Explaining[/cyan]"))
    for chunk in get_provider_and_stream(f"Explain: {topic}", system):
        console.print(chunk, end="")
    console.print()


@app.command("how")
def ask_how(task: str = typer.Argument(..., help="Task to explain")):
    """Get quick how-to instructions."""
    system = "Provide clear, step-by-step instructions."
    console.print(Panel(f"[bold]How to: {task}[/bold]", title="[cyan]Instructions[/cyan]"))
    for chunk in get_provider_and_stream(f"How do I {task}?", system):
        console.print(chunk, end="")
    console.print()


@app.command("fix")
def ask_fix(error: Optional[str] = typer.Argument(None, help="Error message")):
    """Get help fixing an error."""
    if error is None:
        if not sys.stdin.isatty():
            error = sys.stdin.read().strip()
        else:
            console.print("[yellow]Paste error, then Ctrl+D:[/yellow]")
            error = sys.stdin.read().strip()
    
    system = "Analyze the error and provide a clear fix."
    console.print(Panel("[bold red]Error Analysis[/bold red]"))
    for chunk in get_provider_and_stream(f"Fix this error:\n```\n{error}\n```", system):
        console.print(chunk, end="")
    console.print()
