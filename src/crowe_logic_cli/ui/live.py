# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""Live Orchestration Display with Real-Time Updates."""

import asyncio
from typing import Any, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from ..aicl import AICLMessage, AICLConversation
from ..orchestrator import OrchestrationMode
from .panels import (
    ModelPanel,
    DebatePanel,
    ProgressPanel,
    ConversationPanel,
    CodeComparisonPanel,
    get_model_color,
)


class LiveOrchestration:
    """
    Live display for multi-model orchestration.
    Shows real-time updates as models communicate.
    """

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.mode: OrchestrationMode | None = None
        self.models: list[str] = []
        self.messages: list[AICLMessage] = []

        # Panels
        self.progress_panel = ProgressPanel()
        self.conversation_panel = ConversationPanel()
        self.debate_panel: DebatePanel | None = None
        self.model_panels: dict[str, ModelPanel] = {}

        # State
        self.current_stage: str = "Initializing"
        self.is_complete: bool = False
        self.final_output: str = ""

    def setup(self, mode: OrchestrationMode, models: list[str]) -> None:
        """Set up the display for a specific mode."""
        self.mode = mode
        self.models = models

        for model in models:
            self.model_panels[model] = ModelPanel(model)

        if mode == OrchestrationMode.DEBATE and len(models) >= 2:
            self.debate_panel = DebatePanel(models[0], models[1])

    def on_message(self, message: AICLMessage) -> None:
        """Handle an incoming AICL message."""
        self.messages.append(message)
        self.conversation_panel.add_message(message)

        if message.sender_model in self.model_panels:
            self.model_panels[message.sender_model].add_message(message)

        if self.debate_panel:
            self.debate_panel.add_message(message)

    def on_progress(self, stage: str, progress: float) -> None:
        """Handle progress update."""
        self.current_stage = stage
        self.progress_panel.update(stage, progress)

        if progress >= 1.0:
            self.is_complete = True

    def _build_header(self) -> Panel:
        """Build the header panel."""
        mode_name = self.mode.value if self.mode else "Unknown"

        model_text = Text()
        for i, model in enumerate(self.models):
            color = get_model_color(model)
            if i > 0:
                model_text.append(" vs ", style="dim")
            model_text.append(model, style=f"bold {color}")

        header_content = Table.grid(padding=(0, 2))
        header_content.add_column()
        header_content.add_column()
        header_content.add_row(
            Text(f"Mode: {mode_name.upper()}", style="bold bright_white"),
            model_text,
        )

        return Panel(
            header_content,
            title="[bold bright_cyan]CROWE LOGIC AICL ORCHESTRATOR[/]",
            border_style="bright_cyan",
        )

    def _build_status(self) -> Panel:
        """Build the status panel."""
        if self.is_complete:
            status = Text(" Complete", style="bold green")
        else:
            status = Text(f" {self.current_stage}", style="bold yellow")

        return Panel(status, title="[bold]Status[/]", border_style="bright_black")

    def _build_layout(self) -> Layout:
        """Build the main layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="main", ratio=3),
            Layout(name="footer", size=8),
        )

        # Header
        layout["header"].update(self._build_header())

        # Main content - depends on mode
        if self.mode == OrchestrationMode.DEBATE and self.debate_panel:
            layout["main"].update(self.debate_panel.render())
        elif self.mode == OrchestrationMode.VERIFY and len(self.model_panels) >= 2:
            layout["main"].split_row(
                Layout(list(self.model_panels.values())[0].render()),
                Layout(list(self.model_panels.values())[1].render()),
            )
        elif self.mode == OrchestrationMode.PARALLEL:
            panels = [Layout(p.render()) for p in self.model_panels.values()]
            if panels:
                layout["main"].split_row(*panels)
        else:
            layout["main"].update(self.conversation_panel.render())

        # Footer
        layout["footer"].split_row(
            Layout(self.progress_panel.render(), ratio=1),
            Layout(self._build_status(), ratio=1),
        )

        return layout

    async def run_with_display(
        self,
        orchestrate_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Run orchestration with live display.

        Args:
            orchestrate_func: Async function to run
            *args, **kwargs: Arguments for the function

        Returns:
            Result of the orchestration
        """
        result = None

        with Live(self._build_layout(), console=self.console, refresh_per_second=4) as live:
            async def update_display() -> None:
                while not self.is_complete:
                    live.update(self._build_layout())
                    await asyncio.sleep(0.25)

            # Run both concurrently
            display_task = asyncio.create_task(update_display())

            try:
                result = await orchestrate_func(*args, **kwargs)
                self.is_complete = True
                self.final_output = result.final_output if hasattr(result, 'final_output') else str(result)
            finally:
                self.is_complete = True
                await asyncio.sleep(0.1)  # Let display catch up
                display_task.cancel()
                try:
                    await display_task
                except asyncio.CancelledError:
                    pass

            # Final update
            live.update(self._build_layout())

        return result

    def print_final_output(self) -> None:
        """Print the final output."""
        if self.final_output:
            self.console.print("\n")
            self.console.print(Panel(
                self.final_output,
                title="[bold bright_green]Final Output[/]",
                border_style="bright_green",
            ))


class QuickDisplay:
    """Simple non-live display for quick outputs."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def show_message(self, message: AICLMessage) -> None:
        """Display a single AICL message."""
        color = get_model_color(message.sender_model)

        self.console.print(f"\n[{color}]{'=' * 60}[/]")
        self.console.print(f"[bold {color}]{message.sender_model}[/] | "
                          f"[dim]{message.intent.value}[/] | "
                          f"Confidence: {message.confidence:.0%}")
        self.console.print(f"[{color}]{'─' * 60}[/]")
        self.console.print(message.content)

    def show_result(self, result: Any) -> None:
        """Display orchestration result."""
        self.console.print("\n[bold bright_green]━━━ ORCHESTRATION COMPLETE ━━━[/]")
        self.console.print(f"Iterations: {result.iterations}")
        self.console.print(f"Consensus: {'Yes' if result.consensus_reached else 'No'}")
        self.console.print(f"Quality Score: {result.quality_score:.0%}")
        self.console.print("\n[bold]Model Contributions:[/]")
        for model, count in result.model_contributions.items():
            color = get_model_color(model)
            self.console.print(f"  [{color}]{model}[/]: {count} messages")
