"""Integration tests for CLI commands."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from crowe_logic_cli.main import app
from crowe_logic_cli.providers.base import ChatResponse, UsageInfo


runner = CliRunner()


class TestDoctorCommand:
    """Test the doctor command."""

    def test_doctor_shows_config_error(self, mock_env_clean: None) -> None:
        """Test doctor command when config is invalid."""
        result = runner.invoke(app, ["doctor", "run"])

        # Should show config error since no config is set
        assert result.exit_code != 0 or "Missing" in result.output or "Error" in result.output

    def test_doctor_masks_api_key(self, mock_env_clean: None) -> None:
        """Test that doctor command masks API keys."""
        os.environ["CROWE_PROVIDER"] = "azure"
        os.environ["CROWE_AZURE_ENDPOINT"] = "https://test.openai.azure.com"
        os.environ["CROWE_AZURE_DEPLOYMENT"] = "gpt-4"
        os.environ["CROWE_AZURE_API_KEY"] = "super-secret-key-12345"

        # Mock the provider's healthcheck to avoid actual API calls
        with patch("crowe_logic_cli.cli.doctor.create_provider") as mock_factory:
            mock_provider = MagicMock()
            mock_provider.name.return_value = "azure"
            mock_provider.healthcheck.side_effect = Exception("Connection failed")
            mock_factory.return_value = mock_provider

            result = runner.invoke(app, ["doctor", "run"])

        # Full key should not appear in output
        assert "super-secret-key-12345" not in result.output
        # Last 4 chars should appear (masked format shows last 4)
        assert "2345" in result.output


class TestConfigCommand:
    """Test the config command (interactive wizard)."""

    def test_config_help(self) -> None:
        """Test config command shows help."""
        result = runner.invoke(app, ["config", "--help"])

        assert result.exit_code == 0
        assert "run" in result.output
        assert "wizard" in result.output.lower() or "configuration" in result.output.lower()

    def test_config_run_shows_wizard(self) -> None:
        """Test config run command starts wizard (non-interactive test)."""
        # Since config run is interactive, provide input to simulate user interaction
        # Input: "1" for Azure AI Inference, then quit early
        result = runner.invoke(app, ["config", "run"], input="1\n")

        # Should show wizard title or provider selection
        assert "Configuration" in result.output or "provider" in result.output.lower()


class TestChatCommand:
    """Test the chat command."""

    def test_chat_run_with_mock_provider(self, mock_env_clean: None) -> None:
        """Test chat run command with mocked provider."""
        os.environ["CROWE_PROVIDER"] = "azure"
        os.environ["CROWE_AZURE_ENDPOINT"] = "https://test.openai.azure.com"
        os.environ["CROWE_AZURE_DEPLOYMENT"] = "gpt-4"
        os.environ["CROWE_AZURE_API_KEY"] = "test-key"

        mock_response = ChatResponse(
            content="Hello! I'm here to help.",
            usage=UsageInfo(input_tokens=10, output_tokens=5),
        )

        with patch("crowe_logic_cli.cli.chat.create_provider") as mock_factory:
            mock_provider = MagicMock()
            mock_provider.chat.return_value = mock_response
            mock_factory.return_value = mock_provider

            result = runner.invoke(app, ["chat", "run", "Hello!"])

        assert result.exit_code == 0
        assert "Hello! I'm here to help." in result.output

    def test_chat_run_with_system_prompt(self, mock_env_clean: None) -> None:
        """Test chat run with custom system prompt."""
        os.environ["CROWE_PROVIDER"] = "azure"
        os.environ["CROWE_AZURE_ENDPOINT"] = "https://test.openai.azure.com"
        os.environ["CROWE_AZURE_DEPLOYMENT"] = "gpt-4"
        os.environ["CROWE_AZURE_API_KEY"] = "test-key"

        mock_response = ChatResponse(content="I am a pirate!", usage=None)

        with patch("crowe_logic_cli.cli.chat.create_provider") as mock_factory:
            mock_provider = MagicMock()
            mock_provider.chat.return_value = mock_response
            mock_factory.return_value = mock_provider

            result = runner.invoke(
                app, ["chat", "run", "--system", "You are a pirate.", "Hello!"]
            )

        # Verify system prompt was passed
        call_args = mock_provider.chat.call_args[0][0]
        assert any(msg["role"] == "system" and "pirate" in msg["content"] for msg in call_args)


class TestHistoryCommand:
    """Test history management commands."""

    def test_history_list_empty(self, tmp_path: Path) -> None:
        """Test history list when no conversations exist."""
        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=tmp_path
        ):
            result = runner.invoke(app, ["history", "list"])

        assert result.exit_code == 0
        assert "No saved conversations" in result.output

    def test_history_list_with_conversations(
        self, temp_history_dir: Path, sample_conversation: Dict[str, Any]
    ) -> None:
        """Test history list shows saved conversations."""
        conv_file = temp_history_dir / "my-chat.json"
        with open(conv_file, "w") as f:
            json.dump(sample_conversation, f)

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            result = runner.invoke(app, ["history", "list"])

        assert result.exit_code == 0
        assert "my-chat" in result.output

    def test_history_load_displays_conversation(
        self, temp_history_dir: Path, sample_conversation: Dict[str, Any]
    ) -> None:
        """Test history load displays conversation contents."""
        conv_file = temp_history_dir / "test-conv.json"
        with open(conv_file, "w") as f:
            json.dump(sample_conversation, f)

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            result = runner.invoke(app, ["history", "load", "test-conv"])

        assert result.exit_code == 0
        assert "Hello!" in result.output
        assert "Hi there!" in result.output

    def test_history_load_not_found(self, temp_history_dir: Path) -> None:
        """Test history load with non-existent conversation."""
        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            result = runner.invoke(app, ["history", "load", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_history_delete(
        self, temp_history_dir: Path, sample_conversation: Dict[str, Any]
    ) -> None:
        """Test history delete removes conversation."""
        conv_file = temp_history_dir / "to-delete.json"
        with open(conv_file, "w") as f:
            json.dump(sample_conversation, f)

        with patch(
            "crowe_logic_cli.cli.history.get_history_dir", return_value=temp_history_dir
        ):
            result = runner.invoke(app, ["history", "delete", "to-delete"])

        assert result.exit_code == 0
        assert not conv_file.exists()


class TestPluginsCommand:
    """Test plugin discovery commands."""

    def test_plugins_list(self, tmp_path: Path) -> None:
        """Test plugins list command."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()

        # Create a sample plugin
        plugin = plugins_dir / "test-plugin"
        plugin.mkdir()
        (plugin / "agents").mkdir()
        (plugin / "agents" / "test-agent.md").write_text("# Test Agent")

        with patch(
            "crowe_logic_cli.cli.plugins._find_plugins_dir", return_value=plugins_dir
        ):
            result = runner.invoke(app, ["plugins", "list"])

        assert result.exit_code == 0
        assert "test-plugin" in result.output

    def test_plugins_show(self, tmp_path: Path) -> None:
        """Test plugins show command."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()

        plugin = plugins_dir / "my-plugin"
        plugin.mkdir()
        (plugin / "README.md").write_text("# My Plugin\nThis is a test plugin.")
        (plugin / "commands").mkdir()
        (plugin / "commands" / "test-cmd.md").write_text("# Test Command")

        with patch(
            "crowe_logic_cli.cli.plugins._find_plugins_dir", return_value=plugins_dir
        ):
            result = runner.invoke(app, ["plugins", "show", "my-plugin"])

        assert result.exit_code == 0
        assert "my-plugin" in result.output
        assert "test-cmd" in result.output.lower() or "Commands" in result.output


class TestAgentCommand:
    """Test agent runner commands."""

    def test_agent_list(self, tmp_path: Path) -> None:
        """Test agent list command."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "code-reviewer.md").write_text("# Code Reviewer Agent")

        with patch(
            "crowe_logic_cli.cli.agent.AGENTS_DIRS", [agents_dir]
        ):
            result = runner.invoke(app, ["agent", "list"])

        assert result.exit_code == 0
        assert "code-reviewer" in result.output

    def test_agent_run_not_found(self) -> None:
        """Test agent run with non-existent agent."""
        with patch("crowe_logic_cli.cli.agent.AGENTS_DIRS", []):
            result = runner.invoke(
                app, ["agent", "run", "nonexistent-agent", "test prompt"]
            )

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestHelpCommands:
    """Test help and usage information."""

    def test_main_help(self) -> None:
        """Test main help displays available commands."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "chat" in result.output
        assert "interactive" in result.output
        assert "config" in result.output
        assert "doctor" in result.output

    def test_chat_help(self) -> None:
        """Test chat command help."""
        result = runner.invoke(app, ["chat", "--help"])

        assert result.exit_code == 0
        assert "run" in result.output

    def test_history_help(self) -> None:
        """Test history command help."""
        result = runner.invoke(app, ["history", "--help"])

        assert result.exit_code == 0
        assert "list" in result.output
        assert "load" in result.output
        assert "resume" in result.output
        assert "delete" in result.output
