from __future__ import annotations

import typer
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from typing import Optional

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.factory import create_provider


app = typer.Typer(add_completion=False, help="Run agent files as structured prompts")
console = Console()

# Maximum file size for context files (1MB)
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024
MAX_FILE_SIZE_MB = MAX_FILE_SIZE_BYTES / (1024 * 1024)

# Directories to search for agents
CLI_ROOT = Path(__file__).parent.parent.parent.parent
AGENTS_DIRS = [
    CLI_ROOT / "agents",  # Local agents in crowe-logic-cli/agents
    CLI_ROOT.parent / "plugins",  # Repo plugins directory
]


def _find_agent_file(name: str) -> Optional[Path]:
    """Find an agent file by name, searching common locations."""
    # Direct path
    if Path(name).exists():
        return Path(name)

    # Search in agent directories
    for agents_dir in AGENTS_DIRS:
        if not agents_dir.exists():
            continue
        for pattern in [
            f"{name}.md",
            f"**/{name}.md",
            f"**/{name}/agent.md",
            f"**/agents/{name}.md",
            f"**/{name}-agent.md",
        ]:
            matches = list(agents_dir.glob(pattern))
            if matches:
                return matches[0]

    return None


def _load_agent_prompt(path: Path) -> str:
    """Load agent system prompt from a markdown file."""
    content = path.read_text()

    # If the file has YAML frontmatter, skip it
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    return content


@app.command()
def run(
    agent_name: str = typer.Argument(..., help="Agent name or path to agent file"),
    prompt: str = typer.Argument(..., help="User prompt to send to the agent"),
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="File to include as context"
    ),
    no_stream: bool = typer.Option(
        False, "--no-stream", help="Disable streaming responses"
    ),
) -> None:
    """Run an agent with a specific prompt.

    Examples:
        crowelogic agent run code-reviewer "Review this code" -f src/main.py
        crowelogic agent run ./my-agent.md "Help me with this task"
    """
    # Find the agent file
    agent_path = _find_agent_file(agent_name)
    if not agent_path:
        console.print(f"[red]Agent not found: {agent_name}[/red]")
        console.print(f"[dim]Searched in: {', '.join(str(d) for d in AGENTS_DIRS)}[/dim]")
        raise typer.Exit(1)

    console.print(f"[dim]Loading agent: {agent_path}[/dim]")

    # Load the agent system prompt
    system_prompt = _load_agent_prompt(agent_path)

    # Build the user message
    user_content = prompt
    if file:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(1)

        # Check file size to prevent memory issues and API limits
        file_size = file.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            console.print(
                f"[red]File too large: {file_size / (1024 * 1024):.2f}MB "
                f"(max: {MAX_FILE_SIZE_MB:.0f}MB)[/red]"
            )
            console.print("[dim]Consider splitting the file or using a smaller excerpt.[/dim]")
            raise typer.Exit(1)

        file_content = file.read_text()
        user_content = f"{prompt}\n\n---\n\nFile: {file.name}\n```\n{file_content}\n```"

    # Create provider and send request
    config = load_config()
    provider = create_provider(config)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    console.print(Panel(f"[bold]Agent:[/bold] {agent_path.stem}", border_style="blue"))

    try:
        if no_stream or not hasattr(provider, "chat_stream"):
            with console.status("[cyan]Agent thinking...[/cyan]", spinner="dots"):
                response = provider.chat(messages)
            console.print(Markdown(response.content))
        else:
            # Stream response
            full_response = ""
            try:
                for chunk in provider.chat_stream(messages):
                    console.print(chunk, end="")
                    full_response += chunk
            except NotImplementedError:
                with console.status("[cyan]Agent thinking...[/cyan]", spinner="dots"):
                    response = provider.chat(messages)
                console.print(Markdown(response.content))
            console.print()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_agents() -> None:
    """List available agents."""
    console.print(Panel("[bold]Available Agents[/bold]", border_style="blue"))

    # Find all .md files that look like agents
    agent_files = []
    for agents_dir in AGENTS_DIRS:
        if not agents_dir.exists():
            continue
        for pattern in ["*.md", "**/agent.md", "**/agents/*.md", "**/*-agent.md"]:
            for match in agents_dir.glob(pattern):
                agent_files.append((match, agents_dir))

    if not agent_files:
        console.print("[dim]No agents found[/dim]")
        return

    seen = set()
    for agent_path, base_dir in sorted(agent_files, key=lambda x: x[0].name):
        name = agent_path.stem if agent_path.stem != "agent" else agent_path.parent.name
        if name in seen:
            continue
        seen.add(name)
        try:
            rel_path = agent_path.relative_to(base_dir)
        except ValueError:
            rel_path = agent_path.name
        console.print(f"  [cyan]{name}[/cyan] - [dim]{rel_path}[/dim]")
