"""CLI tests for workflow trials (M17)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from workflow_dataset.cli import app

runner = CliRunner()


def test_trials_list_help() -> None:
    result = runner.invoke(app, ["trials", "list", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output.lower()


def test_trials_list() -> None:
    result = runner.invoke(app, ["trials", "list"])
    assert result.exit_code == 0
    assert "ops" in result.output or "founder" in result.output or "trial" in result.output.lower()


def test_trials_run_baseline(tmp_path: Path) -> None:
    """Run one trial in baseline mode (no LLM)."""
    import yaml
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(yaml.dump({
        "project": {"name": "t", "version": "1", "output_excel": "x", "output_csv_dir": "c", "output_parquet_dir": "p", "qa_report_path": "q"},
        "runtime": {"timezone": "UTC"},
        "paths": {"raw_official": "r", "raw_private": "r", "interim": "i", "processed": "p", "prompts": "pr", "context": "c", "sqlite_path": "s", "graph_store_path": str(tmp_path / "graph.sqlite")},
        "setup": {
            "setup_dir": str(tmp_path / "setup"),
            "style_signals_dir": str(tmp_path / "style_signals"),
            "parsed_artifacts_dir": str(tmp_path / "parsed"),
            "style_profiles_dir": str(tmp_path / "style_profiles"),
            "suggestions_dir": str(tmp_path / "suggestions"),
            "draft_structures_dir": str(tmp_path / "drafts"),
        },
    }, default_flow_style=False))
    result = runner.invoke(app, [
        "trials", "run", "ops_summarize_reporting",
        "--mode", "baseline",
        "--output-dir", str(tmp_path),
        "--config", str(config_path),
    ])
    assert result.exit_code == 0
    assert "Result:" in result.output or "result" in result.output.lower()


def test_trials_report_no_results(tmp_path: Path) -> None:
    result = runner.invoke(app, ["trials", "report", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "no" in result.output.lower() or "found" in result.output.lower()
