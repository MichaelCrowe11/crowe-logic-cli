"""Tests for output formatting and clipboard utilities."""
import json
from dataclasses import dataclass

import pytest

from crowe_logic_cli.output import (
    OutputFormat,
    copy_to_clipboard,
    format_output,
    to_json_serializable,
)


class TestToJsonSerializable:
    """Tests for to_json_serializable function."""

    def test_string(self):
        assert to_json_serializable("hello") == "hello"

    def test_int(self):
        assert to_json_serializable(42) == 42

    def test_dict(self):
        data = {"key": "value", "nested": {"a": 1}}
        assert to_json_serializable(data) == data

    def test_list(self):
        data = [1, 2, {"key": "value"}]
        assert to_json_serializable(data) == data

    def test_dataclass(self):
        @dataclass
        class TestData:
            name: str
            value: int

        obj = TestData(name="test", value=42)
        result = to_json_serializable(obj)
        assert result == {"name": "test", "value": 42}

    def test_enum(self):
        result = to_json_serializable(OutputFormat.JSON)
        assert result == "json"


class TestFormatOutput:
    """Tests for format_output function."""

    def test_text_format_string(self):
        result = format_output("hello world", OutputFormat.TEXT)
        assert result == "hello world"

    def test_text_format_dict(self):
        result = format_output({"key": "value"}, OutputFormat.TEXT)
        assert "key" in result

    def test_json_format_string(self):
        result = format_output("hello", OutputFormat.JSON)
        assert json.loads(result) == "hello"

    def test_json_format_dict(self):
        data = {"key": "value", "number": 42}
        result = format_output(data, OutputFormat.JSON)
        assert json.loads(result) == data

    def test_markdown_format_string(self):
        result = format_output("hello", OutputFormat.MARKDOWN)
        assert result == "hello"

    def test_markdown_format_dict(self):
        data = {"key": "value"}
        result = format_output(data, OutputFormat.MARKDOWN)
        assert "```json" in result
        assert '"key"' in result


class TestCopyToClipboard:
    """Tests for copy_to_clipboard function."""

    def test_copy_returns_bool(self):
        # This test just ensures the function runs without error
        # Actual clipboard access may not work in CI
        result = copy_to_clipboard("test")
        assert isinstance(result, bool)
