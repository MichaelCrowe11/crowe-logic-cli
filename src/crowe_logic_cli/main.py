import typer
from rich.console import Console
from rich.panel import Panel
from .cli import (
    chat, interactive, doctor, plugins, agent,
    history, research, molecular, quantum,
    code, select, aicl,
)
from .cli import config_cmd as config

app = typer.Typer(
    name="crowelogic",
    help="Crowe Logic CLI - Quantum-Enhanced Scientific Reasoning with AICL Multi-Model Orchestration",
    add_completion=False,
)
console = Console()

# Core commands
app.add_typer(chat.app, name="chat")
app.add_typer(interactive.app, name="interactive")
app.add_typer(doctor.app, name="doctor")
app.add_typer(plugins.app, name="plugins")
app.add_typer(agent.app, name="agent")
app.add_typer(config.app, name="config")
app.add_typer(history.app, name="history")
app.add_typer(research.app, name="research")
app.add_typer(molecular.app, name="molecular")
app.add_typer(quantum.app, name="quantum")
app.add_typer(code.app, name="code")
app.add_typer(select.app, name="select")

# AICL Multi-Model Orchestration
app.add_typer(aicl.app, name="aicl")


@app.command()
def version():
    """Show version and system info."""
    console.print(Panel(
        "[bold bright_cyan]Crowe Logic CLI[/bold bright_cyan]\n\n"
        "[bold]Version:[/] 2.0.0\n"
        "[bold]Author:[/] Michael Benjamin Crowe\n"
        "[bold]Email:[/] michael@crowelogic.com\n\n"
        "[bold bright_magenta]New in 2.0:[/bold bright_magenta]\n"
        "  [cyan]AICL[/] - AI Communication Language\n"
        "  Multi-model orchestration (Claude + GPT)\n"
        "  Debate, Verify, Parallel, Chain modes\n"
        "  Rich visual UI with live updates",
        title="[bold]About[/]",
        border_style="bright_cyan",
    ))


if __name__ == "__main__":
    app()
