"""
Tests for M18 release: config resolution, report generation, CLI entrypoints.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from workflow_dataset.cli import app
from workflow_dataset.release.report import write_release_readiness_report

runner = CliRunner()


def test_release_config_resolution() -> None:
    path = Path("configs/release_narrow.yaml")
    if not path.exists():
        pytest.skip("configs/release_narrow.yaml not found")
    with open(path) as f:
        data = yaml.safe_load(f)
    rel = data.get("release", {})
    assert rel.get("scope") == "ops"
    assert "trial_ids" in rel
    assert "default_llm_config" in rel


def test_release_verify_help() -> None:
    result = runner.invoke(app, ["release", "verify", "--help"])
    assert result.exit_code == 0
    assert "verify" in result.output.lower()


def test_release_verify_runs() -> None:
    result = runner.invoke(app, ["release", "verify", "--config", "configs/settings.yaml"])
    assert result.exit_code == 0
    assert "Release scope" in result.output or "scope" in result.output.lower()
    assert "Graph" in result.output or "LLM" in result.output or "Trials" in result.output


def test_release_report_generates(tmp_path: Path) -> None:
    report_path = write_release_readiness_report(
        config_path="configs/settings.yaml",
        release_config_path="configs/release_narrow.yaml",
        output_dir=tmp_path,
    )
    assert report_path.exists()
    text = report_path.read_text()
    assert "Release readiness" in text or "release" in text.lower()
    assert "ops" in text.lower() or "Operations" in text
    assert "Safety" in text or "safety" in text.lower()


def test_release_report_cli(tmp_path: Path) -> None:
    result = runner.invoke(app, [
        "release", "report",
        "--config", "configs/settings.yaml",
        "--release-config", "configs/release_narrow.yaml",
        "--output-dir", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "release_readiness_report.md").exists()


def test_release_run_help() -> None:
    result = runner.invoke(app, ["release", "run", "--help"])
    assert result.exit_code == 0


def test_release_demo_help() -> None:
    result = runner.invoke(app, ["release", "demo", "--help"])
    assert result.exit_code == 0

