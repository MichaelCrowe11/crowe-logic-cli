import typer
from rich.console import Console
from .cli import (
    chat, interactive, doctor, plugins, agent,
    history, research, molecular, quantum,
    code, select,
)
from .cli import config_cmd as config

app = typer.Typer(
    name="crowelogic",
    help="Crowe Logic CLI - Quantum-Enhanced Scientific Reasoning",
    add_completion=False,
)
console = Console()

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

@app.command()
def version():
    console.print("[bold cyan]Crowe Logic CLI[/bold cyan]")
    console.print("Version: 1.0.0")
    console.print("Author: Michael Benjamin Crowe")
    console.print("Email: michael@crowelogic.com")

if __name__ == "__main__":
    app()
