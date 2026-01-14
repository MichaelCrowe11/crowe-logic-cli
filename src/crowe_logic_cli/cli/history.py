from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.base import Message
from crowe_logic_cli.providers.factory import create_provider


app = typer.Typer(add_completion=False, help="Manage conversation history")
console = Console()


def get_history_dir() -> Path:
    """Get the directory for storing conversation history."""
    history_dir = Path.home() / ".crowelogic" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def save_conversation(messages: List[Message], name: Optional[str] = None) -> Path:
    """Save a conversation to disk."""
    history_dir = get_history_dir()
    
    if name is None:
        # Generate timestamp-based name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"conversation_{timestamp}"
    
    # Sanitize filename
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
    filepath = history_dir / f"{safe_name}.json"
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "messages": messages,
    }
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    return filepath


def load_conversation(name: str) -> List[Message]:
    """Load a conversation from disk."""
    history_dir = get_history_dir()
    
    # Try exact match
    filepath = history_dir / f"{name}.json"
    if not filepath.exists():
        # Try without .json extension
        filepath = history_dir / name
        if not filepath.exists():
            raise FileNotFoundError(f"Conversation not found: {name}")
    
    with open(filepath) as f:
        data = json.load(f)
    
    return data["messages"]


@app.command("save")
def save_cmd(
    name: str = typer.Argument(..., help="Name for the conversation"),
) -> None:
    """Save the current interactive session (use /save in interactive mode instead)."""
    console.print("[yellow]This command is for internal use. Use /save within interactive mode.[/yellow]")


@app.command("load")
def load_cmd(
    name: str = typer.Argument(..., help="Name of conversation to load"),
) -> None:
    """Load and display a saved conversation."""
    try:
        messages = load_conversation(name)
        
        console.print(Panel(f"[bold]Loaded: {name}[/bold]", border_style="green"))
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                console.print(Panel(content, title="[dim]System[/dim]", border_style="dim"))
            elif role == "user":
                console.print(Panel(content, title="[bold yellow]User[/bold yellow]", border_style="yellow"))
            elif role == "assistant":
                console.print(Panel(content, title="[bold cyan]Assistant[/bold cyan]", border_style="cyan"))
        
        console.print(f"\n[dim]To resume this conversation, use: crowelogic history resume {name}[/dim]")
    
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_conversations() -> None:
    """List all saved conversations."""
    history_dir = get_history_dir()
    conversations = sorted(history_dir.glob("*.json"), reverse=True)
    
    if not conversations:
        console.print("[yellow]No saved conversations found.[/yellow]")
        return
    
    table = Table(title="Saved Conversations", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green")
    table.add_column("Date", style="dim")
    table.add_column("Messages", justify="right")
    
    for conv_file in conversations:
        with open(conv_file) as f:
            data = json.load(f)
        
        name = conv_file.stem
        timestamp = data.get("timestamp", "Unknown")
        try:
            dt = datetime.fromisoformat(timestamp)
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            date_str = timestamp
        
        message_count = len(data.get("messages", []))
        
        table.add_row(name, date_str, str(message_count))
    
    console.print(table)
    console.print(f"\n[dim]Load with: crowelogic history load <name>[/dim]")
    console.print(f"[dim]Resume with: crowelogic history resume <name>[/dim]")


@app.command("resume")
def resume_conversation(
    name: str = typer.Argument(..., help="Name of conversation to resume"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming"),
) -> None:
    """Resume a saved conversation in interactive mode."""
    try:
        messages = load_conversation(name)
        
        console.print(Panel(
            f"[bold green]Resuming: {name}[/bold green]\n"
            f"Loaded {len(messages)} messages",
            border_style="green"
        ))
        
        # Show last few messages for context
        recent = messages[-4:] if len(messages) > 4 else messages
        for msg in recent:
            role = msg["role"]
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            
            if role == "user":
                console.print(f"[yellow]You:[/yellow] {content}")
            elif role == "assistant":
                console.print(f"[cyan]Assistant:[/cyan] {content}")
        
        # Start interactive session with loaded messages
        config = load_config()
        provider = create_provider(config)
        
        console.print("\n[dim]Continue the conversation below. Type /exit to quit, /save to save.[/dim]\n")
        
        while True:
            try:
                user_input = Prompt.ask("[bold yellow]You[/bold yellow]")
            except (KeyboardInterrupt, EOFError):
                # Auto-save on exit
                filepath = save_conversation(messages, name)
                console.print(f"\n[dim]Saved to {filepath}[/dim]")
                console.print("[dim]Goodbye![/dim]")
                break
            
            user_input = user_input.strip()
            if not user_input:
                continue
            
            if user_input.lower() == "/exit":
                filepath = save_conversation(messages, name)
                console.print(f"[dim]Saved to {filepath}[/dim]")
                console.print("[dim]Goodbye![/dim]")
                break
            
            if user_input.lower() == "/save":
                filepath = save_conversation(messages, name)
                console.print(f"[green]Saved to {filepath}[/green]")
                continue
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Get response
            try:
                if no_stream or not hasattr(provider, "chat_stream"):
                    with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                        response = provider.chat(messages)
                    console.print(f"[cyan]Assistant:[/cyan] {response.content}")
                    messages.append({"role": "assistant", "content": response.content})
                else:
                    console.print("[cyan]Assistant:[/cyan] ", end="")
                    full_response = ""
                    try:
                        for chunk in provider.chat_stream(messages):
                            console.print(chunk, end="")
                            full_response += chunk
                    except NotImplementedError:
                        response = provider.chat(messages)
                        full_response = response.content
                        console.print(full_response)
                    console.print()
                    messages.append({"role": "assistant", "content": full_response})
            
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                messages.pop()
    
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_conversation(
    name: str = typer.Argument(..., help="Name of conversation to delete"),
) -> None:
    """Delete a saved conversation."""
    history_dir = get_history_dir()
    filepath = history_dir / f"{name}.json"
    
    if not filepath.exists():
        console.print(f"[red]Conversation not found: {name}[/red]")
        raise typer.Exit(1)
    
    filepath.unlink()
    console.print(f"[green]Deleted: {name}[/green]")
