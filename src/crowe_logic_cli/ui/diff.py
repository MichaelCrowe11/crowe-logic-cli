# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""Diff View for Comparing Model Outputs."""

import difflib
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


class DiffView:
    """
    Visual diff comparison between model outputs.
    Highlights differences between responses from different models.
    """

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def compare_text(
        self,
        text_a: str,
        text_b: str,
        label_a: str = "Model A",
        label_b: str = "Model B",
    ) -> None:
        """
        Compare two text outputs with visual diff.
        """
        lines_a = text_a.splitlines()
        lines_b = text_b.splitlines()

        diff = difflib.unified_diff(
            lines_a, lines_b,
            fromfile=label_a,
            tofile=label_b,
            lineterm="",
        )

        diff_text = Text()
        for line in diff:
            if line.startswith("+++") or line.startswith("---"):
                diff_text.append(line + "\n", style="bold")
            elif line.startswith("@@"):
                diff_text.append(line + "\n", style="cyan")
            elif line.startswith("+"):
                diff_text.append(line + "\n", style="green")
            elif line.startswith("-"):
                diff_text.append(line + "\n", style="red")
            else:
                diff_text.append(line + "\n")

        self.console.print(Panel(
            diff_text,
            title="[bold]Diff Comparison[/]",
            border_style="bright_black",
        ))

    def compare_code(
        self,
        code_a: str,
        code_b: str,
        label_a: str = "Model A",
        label_b: str = "Model B",
        language: str = "python",
    ) -> None:
        """
        Compare two code outputs with syntax highlighting.
        """
        # Side by side comparison
        table = Table(show_header=True, box=None)
        table.add_column(label_a, ratio=1)
        table.add_column(label_b, ratio=1)

        syntax_a = Syntax(code_a, language, theme="monokai", line_numbers=True)
        syntax_b = Syntax(code_b, language, theme="monokai", line_numbers=True)

        self.console.print(Panel(
            table,
            title="[bold]Code Comparison[/]",
            border_style="bright_black",
        ))

        # Also show diff
        self.compare_text(code_a, code_b, label_a, label_b)

    def similarity_score(self, text_a: str, text_b: str) -> float:
        """Calculate similarity between two texts."""
        return difflib.SequenceMatcher(None, text_a, text_b).ratio()

    def compare_responses(
        self,
        responses: dict[str, str],
        show_similarity: bool = True,
    ) -> None:
        """
        Compare multiple model responses.
        Shows pairwise similarity scores.
        """
        models = list(responses.keys())

        if show_similarity and len(models) > 1:
            self.console.print("\n[bold]Similarity Matrix[/]")
            table = Table()
            table.add_column("")
            for m in models:
                table.add_column(m)

            for m1 in models:
                row = [m1]
                for m2 in models:
                    if m1 == m2:
                        row.append("[dim]---[/]")
                    else:
                        score = self.similarity_score(responses[m1], responses[m2])
                        color = "green" if score > 0.8 else "yellow" if score > 0.5 else "red"
                        row.append(f"[{color}]{score:.0%}[/]")
                table.add_row(*row)

            self.console.print(table)

        # Show each response
        for model, response in responses.items():
            from .panels import get_model_color
            color = get_model_color(model)
            self.console.print(Panel(
                response,
                title=f"[bold {color}]{model}[/]",
                border_style=color,
            ))


class MergeView:
    """
    Visual merge of multiple model outputs.
    Shows common elements and unique contributions.
    """

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def find_common(self, texts: list[str]) -> list[str]:
        """Find common lines across all texts."""
        if not texts:
            return []

        lines_sets = [set(t.splitlines()) for t in texts]
        common = lines_sets[0]
        for s in lines_sets[1:]:
            common &= s

        return list(common)

    def merge_display(
        self,
        responses: dict[str, str],
        highlight_unique: bool = True,
    ) -> None:
        """
        Display merged view of responses.
        Common elements shown once, unique contributions highlighted.
        """
        texts = list(responses.values())
        common_lines = self.find_common(texts)

        self.console.print("\n[bold]Merged View[/]")
        self.console.print(f"[dim]Found {len(common_lines)} common lines[/]\n")

        # Show common section
        if common_lines:
            common_text = "\n".join(common_lines[:10])  # First 10 common lines
            if len(common_lines) > 10:
                common_text += f"\n... and {len(common_lines) - 10} more common lines"
            self.console.print(Panel(
                common_text,
                title="[bold cyan]Common Elements[/]",
                border_style="cyan",
            ))

        # Show unique contributions
        if highlight_unique:
            for model, response in responses.items():
                unique_lines = [
                    line for line in response.splitlines()
                    if line not in common_lines and line.strip()
                ]
                if unique_lines:
                    from .panels import get_model_color
                    color = get_model_color(model)
                    unique_text = "\n".join(unique_lines[:5])
                    if len(unique_lines) > 5:
                        unique_text += f"\n... and {len(unique_lines) - 5} more unique lines"
                    self.console.print(Panel(
                        unique_text,
                        title=f"[bold {color}]Unique: {model}[/]",
                        border_style=color,
                    ))
