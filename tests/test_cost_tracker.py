"""Tests for cost tracking."""
import json
import tempfile
from pathlib import Path

import pytest

from crowe_logic_cli.cost_tracker import (
    CostTracker,
    UsageRecord,
    UsageSummary,
    calculate_cost,
    get_model_pricing,
)


class TestGetModelPricing:
    """Tests for get_model_pricing function."""

    def test_exact_match(self):
        pricing = get_model_pricing("claude-3-opus")
        assert pricing["input"] == 15.00
        assert pricing["output"] == 75.00

    def test_partial_match(self):
        # Should match "gpt-4" in "gpt-4-0613"
        pricing = get_model_pricing("gpt-4-0613")
        assert pricing["input"] == 30.00

    def test_default_fallback(self):
        pricing = get_model_pricing("unknown-model-xyz")
        assert pricing["input"] == 3.00  # default
        assert pricing["output"] == 15.00  # default


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_zero_tokens(self):
        cost = calculate_cost(0, 0, "gpt-4")
        assert cost == 0.0

    def test_known_model(self):
        # 1M input tokens at $30/1M = $30
        cost = calculate_cost(1_000_000, 0, "gpt-4")
        assert cost == 30.0

        # 1M output tokens at $60/1M = $60
        cost = calculate_cost(0, 1_000_000, "gpt-4")
        assert cost == 60.0

    def test_combined_tokens(self):
        # 1000 input + 1000 output for gpt-4
        # Input: (1000 / 1M) * 30 = 0.03
        # Output: (1000 / 1M) * 60 = 0.06
        cost = calculate_cost(1000, 1000, "gpt-4")
        assert abs(cost - 0.09) < 0.001


class TestUsageRecord:
    """Tests for UsageRecord dataclass."""

    def test_to_dict(self):
        record = UsageRecord(
            timestamp="2026-01-14T12:00:00Z",
            model="gpt-4",
            provider="azure",
            input_tokens=100,
            output_tokens=200,
            cost_usd=0.05,
            command="chat",
        )
        data = record.to_dict()
        assert data["model"] == "gpt-4"
        assert data["input_tokens"] == 100
        assert data["cost_usd"] == 0.05

    def test_from_dict(self):
        data = {
            "timestamp": "2026-01-14T12:00:00Z",
            "model": "gpt-4",
            "provider": "azure",
            "input_tokens": 100,
            "output_tokens": 200,
            "cost_usd": 0.05,
        }
        record = UsageRecord.from_dict(data)
        assert record.model == "gpt-4"
        assert record.input_tokens == 100


class TestCostTracker:
    """Tests for CostTracker class."""

    @pytest.fixture
    def temp_tracker(self, tmp_path):
        """Create a CostTracker with a temporary directory."""
        return CostTracker(data_dir=tmp_path)

    def test_record_usage(self, temp_tracker):
        record = temp_tracker.record(
            model="gpt-4",
            provider="azure",
            input_tokens=100,
            output_tokens=200,
            command="chat",
        )
        assert record.model == "gpt-4"
        assert record.input_tokens == 100
        assert record.output_tokens == 200
        assert record.cost_usd > 0

    def test_get_summary_empty(self, temp_tracker):
        summary = temp_tracker.get_summary()
        assert summary.total_input_tokens == 0
        assert summary.total_output_tokens == 0
        assert summary.total_cost_usd == 0
        assert summary.request_count == 0

    def test_get_summary_with_records(self, temp_tracker):
        temp_tracker.record("gpt-4", "azure", 100, 200)
        temp_tracker.record("gpt-4", "azure", 300, 400)

        summary = temp_tracker.get_summary()
        assert summary.total_input_tokens == 400
        assert summary.total_output_tokens == 600
        assert summary.request_count == 2

    def test_summary_by_model(self, temp_tracker):
        temp_tracker.record("gpt-4", "azure", 100, 200)
        temp_tracker.record("gpt-3.5-turbo", "azure", 300, 400)

        summary = temp_tracker.get_summary()
        assert "gpt-4" in summary.by_model
        assert "gpt-3.5-turbo" in summary.by_model

    def test_clear(self, temp_tracker):
        temp_tracker.record("gpt-4", "azure", 100, 200)
        assert temp_tracker.get_summary().request_count == 1

        temp_tracker.clear()
        assert temp_tracker.get_summary().request_count == 0

    def test_persistence(self, tmp_path):
        # Create tracker and add record
        tracker1 = CostTracker(data_dir=tmp_path)
        tracker1.record("gpt-4", "azure", 100, 200)

        # Create new tracker with same directory
        tracker2 = CostTracker(data_dir=tmp_path)
        summary = tracker2.get_summary()

        assert summary.request_count == 1
        assert summary.total_input_tokens == 100
