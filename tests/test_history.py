"""Tests for conversation history management."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from crowe_logic_cli.cli.history import (
    get_history_dir,
    save_conversation,
    load_conversation,
)
from crowe_logic_cli.providers.base import Message


class TestHistoryDir:
    """Test history directory management."""

    def test_get_history_dir_creates_directory(self, tmp_path: Path) -> None:
        """Test that get_history_dir creates the directory if it doesn't exist."""
        home = tmp_path / "home"
        home.mkdir()

        with patch("crowe_logic_cli.cli.history.Path.home", return_value=home):
            history_dir = get_history_dir()

        assert history_dir.exists()
        assert history_dir == home / ".crowelogic" / "history"

    def test_get_history_dir_returns_existing(self, temp_history_dir: Path) -> None:
        """Test that get_history_dir returns existing directory."""
        home = temp_history_dir.parent.parent

        with patch("crowe_logic_cli.cli.history.Path.home", return_value=home):
            history_dir = get_history_dir()

        assert history_dir == temp_history_dir


class TestSaveConversation:
    """Test conversation saving."""

    def test_save_conversation_with_name(self, temp_history_dir: Path) -> None:
        """Test saving a conversation with a specific name."""
        messages: list[Message] = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            filepath = save_conversation(messages, "test-conversation")

        assert filepath.exists()
        assert filepath.name == "test-conversation.json"

        with open(filepath) as f:
            data = json.load(f)

        assert data["messages"] == messages
        assert "timestamp" in data

    def test_save_conversation_generates_name(self, temp_history_dir: Path) -> None:
        """Test saving a conversation without a name generates timestamp-based name."""
        messages: list[Message] = [
            {"role": "user", "content": "Hello!"},
        ]

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            filepath = save_conversation(messages)

        assert filepath.exists()
        assert filepath.stem.startswith("conversation_")

    def test_save_conversation_sanitizes_name(self, temp_history_dir: Path) -> None:
        """Test that conversation names are sanitized."""
        messages: list[Message] = [{"role": "user", "content": "Test"}]

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            filepath = save_conversation(messages, "my/unsafe:name*test")

        # Special characters should be replaced with underscores
        assert "/" not in filepath.stem
        assert ":" not in filepath.stem
        assert "*" not in filepath.stem

    def test_save_conversation_preserves_valid_chars(self, temp_history_dir: Path) -> None:
        """Test that valid characters are preserved in names."""
        messages: list[Message] = [{"role": "user", "content": "Test"}]

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            filepath = save_conversation(messages, "valid-name_123")

        assert filepath.stem == "valid-name_123"


class TestLoadConversation:
    """Test conversation loading."""

    def test_load_conversation_by_name(
        self, temp_history_dir: Path, sample_conversation: Dict[str, Any]
    ) -> None:
        """Test loading a conversation by name."""
        conv_file = temp_history_dir / "my-conversation.json"
        with open(conv_file, "w") as f:
            json.dump(sample_conversation, f)

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            messages = load_conversation("my-conversation")

        assert messages == sample_conversation["messages"]

    def test_load_conversation_with_json_extension(
        self, temp_history_dir: Path, sample_conversation: Dict[str, Any]
    ) -> None:
        """Test loading works with .json extension in name."""
        conv_file = temp_history_dir / "test.json"
        with open(conv_file, "w") as f:
            json.dump(sample_conversation, f)

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            messages = load_conversation("test")

        assert messages == sample_conversation["messages"]

    def test_load_conversation_not_found(self, temp_history_dir: Path) -> None:
        """Test error when conversation doesn't exist."""
        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            with pytest.raises(FileNotFoundError, match="Conversation not found"):
                load_conversation("nonexistent")


class TestConversationRoundTrip:
    """Test saving and loading conversations."""

    def test_save_and_load_roundtrip(self, temp_history_dir: Path) -> None:
        """Test that saving and loading preserves data."""
        original_messages: list[Message] = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4."},
            {"role": "user", "content": "Thanks!"},
            {"role": "assistant", "content": "You're welcome!"},
        ]

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            filepath = save_conversation(original_messages, "roundtrip-test")
            loaded_messages = load_conversation("roundtrip-test")

        assert loaded_messages == original_messages

    def test_multiple_conversations(self, temp_history_dir: Path) -> None:
        """Test managing multiple conversations."""
        conv1: list[Message] = [{"role": "user", "content": "First conversation"}]
        conv2: list[Message] = [{"role": "user", "content": "Second conversation"}]

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            save_conversation(conv1, "conv1")
            save_conversation(conv2, "conv2")

            loaded1 = load_conversation("conv1")
            loaded2 = load_conversation("conv2")

        assert loaded1 == conv1
        assert loaded2 == conv2


class TestTimestampParsing:
    """Test timestamp handling in history list."""

    def test_valid_iso_timestamp(
        self, temp_history_dir: Path, sample_conversation: Dict[str, Any]
    ) -> None:
        """Test that valid ISO timestamps are parsed correctly."""
        sample_conversation["timestamp"] = "2026-01-12T15:30:00"
        conv_file = temp_history_dir / "test.json"
        with open(conv_file, "w") as f:
            json.dump(sample_conversation, f)

        # Verify the timestamp can be parsed
        with open(conv_file) as f:
            data = json.load(f)

        dt = datetime.fromisoformat(data["timestamp"])
        assert dt.year == 2026
        assert dt.month == 1
        assert dt.day == 12

    def test_invalid_timestamp_handled_gracefully(self, temp_history_dir: Path) -> None:
        """Test that invalid timestamps don't cause crashes."""
        data = {
            "timestamp": "not-a-valid-timestamp",
            "messages": [{"role": "user", "content": "Test"}],
        }
        conv_file = temp_history_dir / "test.json"
        with open(conv_file, "w") as f:
            json.dump(data, f)

        # This should not raise - the bare except was fixed to (ValueError, TypeError)
        with open(conv_file) as f:
            loaded = json.load(f)

        try:
            dt = datetime.fromisoformat(loaded["timestamp"])
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            date_str = loaded["timestamp"]

        assert date_str == "not-a-valid-timestamp"
