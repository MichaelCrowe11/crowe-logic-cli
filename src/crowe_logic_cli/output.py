"""Output formatting and clipboard utilities."""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Optional

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel


class OutputFormat(str, Enum):
    """Supported output formats."""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


def to_json_serializable(obj: Any) -> Any:
    """Convert an object to JSON-serializable format."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dict__"):
        return {k: to_json_serializable(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [to_json_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    return obj


def format_output(
    data: Any,
    output_format: OutputFormat = OutputFormat.TEXT,
    console: Optional[Console] = None,
) -> str:
    """Format data according to the specified output format.

    Args:
        data: The data to format (string, dict, dataclass, etc.)
        output_format: The desired output format
        console: Optional Rich console for styled output

    Returns:
        Formatted string representation of the data
    """
    if output_format == OutputFormat.JSON:
        serializable = to_json_serializable(data)
        return json.dumps(serializable, indent=2, ensure_ascii=False)

    if output_format == OutputFormat.MARKDOWN:
        if isinstance(data, str):
            return data
        serializable = to_json_serializable(data)
        return f"```json\n{json.dumps(serializable, indent=2, ensure_ascii=False)}\n```"

    # TEXT format
    if isinstance(data, str):
        return data
    return str(data)


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard.

    Args:
        text: The text to copy

    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == "darwin":
            # macOS
            subprocess.run(
                ["pbcopy"],
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            return True
        elif sys.platform == "win32":
            # Windows
            subprocess.run(
                ["clip"],
                input=text.encode("utf-16le"),
                check=True,
                capture_output=True,
            )
            return True
        else:
            # Linux - try xclip first, then xsel
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    subprocess.run(
                        cmd,
                        input=text.encode("utf-8"),
                        check=True,
                        capture_output=True,
                    )
                    return True
                except FileNotFoundError:
                    continue
            return False
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False


def print_output(
    data: Any,
    output_format: OutputFormat = OutputFormat.TEXT,
    copy: bool = False,
    console: Optional[Console] = None,
    title: Optional[str] = None,
) -> None:
    """Print formatted output and optionally copy to clipboard.

    Args:
        data: The data to output
        output_format: The desired output format
        copy: Whether to copy to clipboard
        console: Rich console for output
        title: Optional title for panel display
    """
    if console is None:
        console = Console()

    formatted = format_output(data, output_format, console)

    if output_format == OutputFormat.JSON:
        # Use Rich's JSON syntax highlighting
        if title:
            console.print(Panel(JSON(formatted), title=title))
        else:
            console.print(JSON(formatted))
    elif title and output_format == OutputFormat.TEXT:
        console.print(Panel(formatted, title=title))
    else:
        console.print(formatted)

    if copy:
        if copy_to_clipboard(formatted):
            console.print("[dim green]✓ Copied to clipboard[/dim green]")
        else:
            console.print("[dim red]✗ Failed to copy to clipboard[/dim red]")
