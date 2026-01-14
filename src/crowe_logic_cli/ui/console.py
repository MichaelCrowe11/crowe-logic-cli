# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""Console and Theme Configuration for Rich UI."""

from dataclasses import dataclass

from rich.console import Console as RichConsole
from rich.theme import Theme as RichTheme


@dataclass
class Theme:
    """Color theme for the UI."""
    # Model colors
    claude_color: str = "bright_magenta"
    gpt_color: str = "bright_green"
    system_color: str = "bright_cyan"

    # Status colors
    success_color: str = "green"
    error_color: str = "red"
    warning_color: str = "yellow"
    info_color: str = "blue"

    # Intent colors
    argue_for_color: str = "green"
    argue_against_color: str = "red"
    synthesis_color: str = "yellow"
    validation_color: str = "cyan"

    # UI elements
    border_color: str = "bright_black"
    highlight_color: str = "bright_white"
    muted_color: str = "dim"

    def to_rich_theme(self) -> RichTheme:
        """Convert to Rich theme."""
        return RichTheme({
            "claude": self.claude_color,
            "gpt": self.gpt_color,
            "system": self.system_color,
            "success": self.success_color,
            "error": self.error_color,
            "warning": self.warning_color,
            "info": self.info_color,
            "argue_for": self.argue_for_color,
            "argue_against": self.argue_against_color,
            "synthesis": self.synthesis_color,
            "validation": self.validation_color,
            "border": self.border_color,
            "highlight": self.highlight_color,
            "muted": self.muted_color,
            # Model-specific styles
            "model.claude": f"bold {self.claude_color}",
            "model.gpt": f"bold {self.gpt_color}",
            "model.unknown": "bold white",
            # Intent styles
            "intent.for": f"bold {self.argue_for_color}",
            "intent.against": f"bold {self.argue_against_color}",
            "intent.synthesis": f"bold {self.synthesis_color}",
            "intent.validation": f"bold {self.validation_color}",
        })


class Console:
    """Customized Rich console with theme support."""

    def __init__(self, theme: Theme | None = None) -> None:
        self.theme = theme or Theme()
        self.rich = RichConsole(theme=self.theme.to_rich_theme())

    def get_model_style(self, model_id: str) -> str:
        """Get the style for a model based on its ID."""
        if "claude" in model_id.lower():
            return "model.claude"
        elif "gpt" in model_id.lower():
            return "model.gpt"
        return "model.unknown"

    def get_model_emoji(self, model_id: str) -> str:
        """Get emoji for a model."""
        if "claude" in model_id.lower():
            return "[magenta]@[/]"
        elif "gpt" in model_id.lower():
            return "[green]%[/]"
        return "[white]#[/]"

    def print_header(self, text: str) -> None:
        """Print a styled header."""
        self.rich.print(f"\n[bold bright_white]{text}[/]")
        self.rich.print("[bright_black]" + "─" * len(text) + "[/]")

    def print_model_message(self, model_id: str, content: str, intent: str = "") -> None:
        """Print a message from a model."""
        style = self.get_model_style(model_id)
        emoji = self.get_model_emoji(model_id)

        intent_badge = ""
        if intent:
            intent_badge = f" [dim]({intent})[/]"

        self.rich.print(f"\n{emoji} [{style}]{model_id}[/]{intent_badge}")
        self.rich.print(content)

    def print_success(self, text: str) -> None:
        """Print a success message."""
        self.rich.print(f"[success][/] {text}")

    def print_error(self, text: str) -> None:
        """Print an error message."""
        self.rich.print(f"[error][/] {text}")

    def print_warning(self, text: str) -> None:
        """Print a warning message."""
        self.rich.print(f"[warning][/] {text}")

    def print_info(self, text: str) -> None:
        """Print an info message."""
        self.rich.print(f"[info][/] {text}")
