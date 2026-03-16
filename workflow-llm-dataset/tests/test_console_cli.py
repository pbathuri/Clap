"""
Tests for the console CLI entrypoint.

Ensures the command is registered and run_console is invoked without requiring interactive TUI.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from workflow_dataset.cli import app
from workflow_dataset.ui import run_console
from workflow_dataset.ui.app import run_console as run_console_impl


runner = CliRunner()


def test_console_command_help() -> None:
    result = runner.invoke(app, ["console", "--help"])
    assert result.exit_code == 0
    assert "console" in result.output
    assert "config" in result.output or "--config" in result.output


def test_console_command_exits_with_bad_config() -> None:
    result = runner.invoke(app, ["console", "--config", "/nonexistent/settings.yaml"])
    assert result.exit_code == 1
    assert "config" in result.output.lower() or "error" in result.output.lower() or "Failed" in result.output


def test_run_console_returns_zero_on_exit() -> None:
    """run_console can be made to exit immediately by simulating KeyboardInterrupt + E."""
    with patch("workflow_dataset.ui.app.get_settings") as mock_settings:
        from workflow_dataset.settings import Settings
        from workflow_dataset.settings import PathSettings, ProjectSettings, RuntimeSettings
        mock_settings.return_value = Settings(
                project=ProjectSettings(name="t", version="1", output_excel="x", output_csv_dir="c", output_parquet_dir="p", qa_report_path="q"),
                runtime=RuntimeSettings(timezone="UTC"),
                paths=PathSettings(raw_official="r", raw_private="rp", interim="i", processed="p", prompts="pr", context="c", sqlite_path="s"),
            )
        with patch("workflow_dataset.ui.app.render_home") as mock_home:
            from workflow_dataset.ui.models import Screen
            mock_home.return_value = Screen.EXIT
            code = run_console_impl("configs/settings.yaml")
            assert code == 0
