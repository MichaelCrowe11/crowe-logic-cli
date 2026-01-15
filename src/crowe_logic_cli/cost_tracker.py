"""Token usage and cost tracking."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.table import Table


# Pricing per 1M tokens (as of 2024 - update as needed)
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Claude models
    "claude-opus-4-5": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    # GPT models
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # Default fallback
    "default": {"input": 3.00, "output": 15.00},
}


@dataclass
class UsageRecord:
    """Single usage record."""
    timestamp: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    command: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "command": self.command,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UsageRecord":
        """Create from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            model=data["model"],
            provider=data["provider"],
            input_tokens=data["input_tokens"],
            output_tokens=data["output_tokens"],
            cost_usd=data["cost_usd"],
            command=data.get("command"),
        )


@dataclass
class UsageSummary:
    """Aggregated usage summary."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    request_count: int = 0
    by_model: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_day: dict[str, dict[str, Any]] = field(default_factory=dict)


def get_model_pricing(model: str) -> dict[str, float]:
    """Get pricing for a model.

    Args:
        model: Model name/identifier

    Returns:
        Dict with 'input' and 'output' prices per 1M tokens
    """
    model_lower = model.lower()

    # Check for exact match first
    if model_lower in MODEL_PRICING:
        return MODEL_PRICING[model_lower]

    # Check for partial matches
    for key, pricing in MODEL_PRICING.items():
        if key in model_lower:
            return pricing

    return MODEL_PRICING["default"]


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> float:
    """Calculate cost for token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name

    Returns:
        Cost in USD
    """
    pricing = get_model_pricing(model)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


class CostTracker:
    """Track and persist usage costs."""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        """Initialize cost tracker.

        Args:
            data_dir: Directory for storing usage data
        """
        if data_dir is None:
            data_dir = Path.home() / ".crowelogic" / "usage"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._usage_file = self.data_dir / "usage.json"
        self._records: list[UsageRecord] = []
        self._load()

    def _load(self) -> None:
        """Load usage records from disk."""
        if self._usage_file.exists():
            try:
                with open(self._usage_file, "r") as f:
                    data = json.load(f)
                    self._records = [UsageRecord.from_dict(r) for r in data.get("records", [])]
            except (json.JSONDecodeError, KeyError):
                self._records = []

    def _save(self) -> None:
        """Save usage records to disk."""
        data = {"records": [r.to_dict() for r in self._records]}
        with open(self._usage_file, "w") as f:
            json.dump(data, f, indent=2)

    def record(
        self,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        command: Optional[str] = None,
    ) -> UsageRecord:
        """Record a usage event.

        Args:
            model: Model name
            provider: Provider name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            command: Command that generated this usage

        Returns:
            The created usage record
        """
        cost = calculate_cost(input_tokens, output_tokens, model)
        record = UsageRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            command=command,
        )
        self._records.append(record)
        self._save()
        return record

    def get_summary(
        self,
        days: Optional[int] = None,
        model: Optional[str] = None,
    ) -> UsageSummary:
        """Get usage summary.

        Args:
            days: Limit to last N days (None = all time)
            model: Filter by model name

        Returns:
            Usage summary
        """
        summary = UsageSummary()
        now = datetime.now(timezone.utc)

        for record in self._records:
            # Parse timestamp
            try:
                record_time = datetime.fromisoformat(record.timestamp.replace("Z", "+00:00"))
            except ValueError:
                continue

            # Filter by days
            if days is not None:
                delta = now - record_time
                if delta.days > days:
                    continue

            # Filter by model
            if model is not None and model.lower() not in record.model.lower():
                continue

            # Aggregate totals
            summary.total_input_tokens += record.input_tokens
            summary.total_output_tokens += record.output_tokens
            summary.total_cost_usd += record.cost_usd
            summary.request_count += 1

            # Aggregate by model
            if record.model not in summary.by_model:
                summary.by_model[record.model] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                    "count": 0,
                }
            summary.by_model[record.model]["input_tokens"] += record.input_tokens
            summary.by_model[record.model]["output_tokens"] += record.output_tokens
            summary.by_model[record.model]["cost_usd"] += record.cost_usd
            summary.by_model[record.model]["count"] += 1

            # Aggregate by day
            day_key = record_time.strftime("%Y-%m-%d")
            if day_key not in summary.by_day:
                summary.by_day[day_key] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                    "count": 0,
                }
            summary.by_day[day_key]["input_tokens"] += record.input_tokens
            summary.by_day[day_key]["output_tokens"] += record.output_tokens
            summary.by_day[day_key]["cost_usd"] += record.cost_usd
            summary.by_day[day_key]["count"] += 1

        return summary

    def clear(self) -> None:
        """Clear all usage records."""
        self._records = []
        self._save()

    def print_summary(
        self,
        console: Optional[Console] = None,
        days: Optional[int] = None,
    ) -> None:
        """Print usage summary to console.

        Args:
            console: Rich console for output
            days: Limit to last N days
        """
        if console is None:
            console = Console()

        summary = self.get_summary(days=days)

        # Header
        period = f"Last {days} days" if days else "All time"
        console.print(f"\n[bold cyan]Usage Summary ({period})[/bold cyan]\n")

        # Totals
        total_tokens = summary.total_input_tokens + summary.total_output_tokens
        console.print(f"  Total requests: [bold]{summary.request_count:,}[/bold]")
        console.print(f"  Total tokens: [bold]{total_tokens:,}[/bold]")
        console.print(f"    Input: {summary.total_input_tokens:,}")
        console.print(f"    Output: {summary.total_output_tokens:,}")
        console.print(f"  Total cost: [bold green]${summary.total_cost_usd:.4f}[/bold green]\n")

        # By model table
        if summary.by_model:
            table = Table(title="By Model")
            table.add_column("Model", style="cyan")
            table.add_column("Requests", justify="right")
            table.add_column("Input", justify="right")
            table.add_column("Output", justify="right")
            table.add_column("Cost", justify="right", style="green")

            for model, stats in sorted(summary.by_model.items()):
                table.add_row(
                    model,
                    f"{stats['count']:,}",
                    f"{stats['input_tokens']:,}",
                    f"{stats['output_tokens']:,}",
                    f"${stats['cost_usd']:.4f}",
                )

            console.print(table)

        # Recent daily usage
        if summary.by_day:
            console.print()
            daily_table = Table(title="Daily Usage (Recent)")
            daily_table.add_column("Date", style="cyan")
            daily_table.add_column("Requests", justify="right")
            daily_table.add_column("Tokens", justify="right")
            daily_table.add_column("Cost", justify="right", style="green")

            # Show last 7 days
            for day in sorted(summary.by_day.keys(), reverse=True)[:7]:
                stats = summary.by_day[day]
                total = stats["input_tokens"] + stats["output_tokens"]
                daily_table.add_row(
                    day,
                    f"{stats['count']:,}",
                    f"{total:,}",
                    f"${stats['cost_usd']:.4f}",
                )

            console.print(daily_table)


# Global tracker instance
_tracker: Optional[CostTracker] = None


def get_tracker() -> CostTracker:
    """Get or create global cost tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
