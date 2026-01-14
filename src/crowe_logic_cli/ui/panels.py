# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""Rich Panel Components for Multi-Model UI."""

from typing import Any

from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax

from ..aicl import AICLMessage, AICLIntent


def get_intent_color(intent: AICLIntent) -> str:
    """Get color for an intent."""
    colors = {
        AICLIntent.ARGUE_FOR: "green",
        AICLIntent.ARGUE_AGAINST: "red",
        AICLIntent.COUNTER: "yellow",
        AICLIntent.SYNTHESIS: "cyan",
        AICLIntent.VALIDATION: "bright_green",
        AICLIntent.CRITIQUE: "bright_red",
        AICLIntent.CODE_GENERATE: "bright_blue",
        AICLIntent.CODE_REVIEW: "bright_magenta",
        AICLIntent.RESPONSE: "white",
    }
    return colors.get(intent, "white")


def get_model_color(model_id: str) -> str:
    """Get color for a model."""
    if "claude" in model_id.lower():
        return "bright_magenta"
    elif "gpt" in model_id.lower():
        return "bright_green"
    return "white"


class ModelPanel:
    """Panel showing a single model's output."""

    def __init__(self, model_id: str, title: str | None = None) -> None:
        self.model_id = model_id
        self.title = title or model_id
        self.messages: list[AICLMessage] = []
        self.color = get_model_color(model_id)

    def add_message(self, message: AICLMessage) -> None:
        """Add a message to the panel."""
        self.messages.append(message)

    def render(self, height: int | None = None) -> Panel:
        """Render the panel."""
        content_parts = []

        for msg in self.messages[-3:]:  # Show last 3 messages
            intent_color = get_intent_color(msg.intent)
            header = Text(f"[{msg.intent.value}] ", style=f"bold {intent_color}")
            header.append(f"(confidence: {msg.confidence:.0%})", style="dim")

            content_parts.append(header)
            content_parts.append(Text(msg.content[:500] + "..." if len(msg.content) > 500 else msg.content))
            content_parts.append(Text(""))

        return Panel(
            Group(*content_parts) if content_parts else Text("[dim]Waiting...[/]"),
            title=f"[bold {self.color}]{self.title}[/]",
            border_style=self.color,
            height=height,
        )


class DebatePanel:
    """Split panel for debate mode showing both sides."""

    def __init__(self, model_a: str, model_b: str) -> None:
        self.panel_a = ModelPanel(model_a, f"{model_a} (FOR)")
        self.panel_b = ModelPanel(model_b, f"{model_b} (AGAINST)")
        self.synthesis: str | None = None

    def add_message(self, message: AICLMessage) -> None:
        """Route message to appropriate panel."""
        if message.sender_model == self.panel_a.model_id:
            self.panel_a.add_message(message)
        elif message.sender_model == self.panel_b.model_id:
            self.panel_b.add_message(message)

        if message.intent == AICLIntent.SYNTHESIS:
            self.synthesis = message.content

    def render(self) -> Layout:
        """Render the debate layout."""
        layout = Layout()

        if self.synthesis:
            layout.split_column(
                Layout(name="debate", ratio=2),
                Layout(name="synthesis", ratio=1),
            )
            layout["debate"].split_row(
                Layout(self.panel_a.render()),
                Layout(self.panel_b.render()),
            )
            layout["synthesis"].update(Panel(
                Markdown(self.synthesis),
                title="[bold cyan]Synthesis[/]",
                border_style="cyan",
            ))
        else:
            layout.split_row(
                Layout(self.panel_a.render()),
                Layout(self.panel_b.render()),
            )

        return layout


class ProgressPanel:
    """Progress tracking panel with stages."""

    def __init__(self) -> None:
        self.stages: list[tuple[str, float, str]] = []  # (name, progress, status)
        self.current_stage: str = ""

    def update(self, stage: str, progress: float) -> None:
        """Update progress."""
        self.current_stage = stage
        # Update or add stage
        for i, (name, _, _) in enumerate(self.stages):
            if name == stage:
                status = "complete" if progress >= 1.0 else "in_progress"
                self.stages[i] = (name, progress, status)
                return
        self.stages.append((stage, progress, "in_progress"))

    def render(self) -> Panel:
        """Render the progress panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Stage", style="bold")
        table.add_column("Progress", width=20)
        table.add_column("Status")

        for name, progress, status in self.stages:
            bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
            status_style = "green" if status == "complete" else "yellow"
            icon = "[green]>[/]" if status == "complete" else "[yellow]>[/]"
            table.add_row(
                name,
                f"[{status_style}]{bar}[/] {progress:.0%}",
                icon,
            )

        return Panel(table, title="[bold]Progress[/]", border_style="bright_black")


class ConversationPanel:
    """Panel showing the full AICL conversation."""

    def __init__(self) -> None:
        self.messages: list[AICLMessage] = []

    def add_message(self, message: AICLMessage) -> None:
        """Add a message."""
        self.messages.append(message)

    def render(self, max_messages: int = 10) -> Panel:
        """Render the conversation panel."""
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Model", style="bold", width=20)
        table.add_column("Intent", width=15)
        table.add_column("Content", ratio=1)
        table.add_column("Conf", width=6)

        for msg in self.messages[-max_messages:]:
            model_color = get_model_color(msg.sender_model)
            intent_color = get_intent_color(msg.intent)

            # Truncate content
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            content = content.replace("\n", " ")

            table.add_row(
                Text(msg.sender_model, style=model_color),
                Text(msg.intent.value, style=intent_color),
                content,
                f"{msg.confidence:.0%}",
            )

        return Panel(
            table,
            title="[bold]AICL Conversation[/]",
            border_style="bright_black",
        )


class CodeComparisonPanel:
    """Panel for comparing code from different models."""

    def __init__(self) -> None:
        self.code_blocks: dict[str, str] = {}  # model_id -> code

    def add_code(self, model_id: str, code: str, language: str = "python") -> None:
        """Add code from a model."""
        self.code_blocks[model_id] = (code, language)

    def render(self) -> Layout:
        """Render side-by-side code comparison."""
        layout = Layout()

        panels = []
        for model_id, (code, language) in self.code_blocks.items():
            color = get_model_color(model_id)
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            panel = Panel(syntax, title=f"[bold {color}]{model_id}[/]", border_style=color)
            panels.append(Layout(panel))

        if panels:
            layout.split_row(*panels)

        return layout
