"""M20: Tests for pilot verify, status, latest-report, and recovery/degraded behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_pilot_verify_result_structure(tmp_path: Path) -> None:
    """pilot_verify_result returns ready, blocking, warnings, details."""
    from workflow_dataset.pilot.health import pilot_verify_result
    # Use repo config if present; else minimal
    config = Path("configs/settings.yaml")
    if not config.exists():
        config = tmp_path / "settings.yaml"
        config.write_text("paths:\n  graph_store_path: /nonexistent/graph.sqlite\n")
    result = pilot_verify_result(config_path=str(config))
    assert "ready" in result
    assert "blocking" in result
    assert "warnings" in result
    assert "details" in result
    assert isinstance(result["blocking"], list)
    assert isinstance(result["warnings"], list)


def test_pilot_verify_result_blocks_when_graph_missing(tmp_path: Path) -> None:
    """When graph path does not exist, ready is False and blocking lists graph."""
    import yaml
    config = tmp_path / "settings.yaml"
    config.write_text(yaml.dump({
        "paths": {"graph_store_path": str(tmp_path / "nonexistent_graph.sqlite")},
        "setup": {
            "setup_dir": str(tmp_path / "setup"),
            "parsed_artifacts_dir": str(tmp_path / "parsed"),
            "style_signals_dir": str(tmp_path / "style_signals"),
        },
    }, default_flow_style=False))
    from workflow_dataset.pilot.health import pilot_verify_result
    result = pilot_verify_result(config_path=str(config))
    assert result["ready"] is False
    assert any("graph" in b.lower() or "Graph" in b for b in result["blocking"])


def test_pilot_status_dict_structure() -> None:
    """pilot_status_dict returns ready, degraded, safe_to_demo, adapter_ok, etc."""
    from workflow_dataset.pilot.health import pilot_status_dict
    status = pilot_status_dict()
    assert "ready" in status
    assert "degraded" in status
    assert "safe_to_demo" in status
    assert "adapter_ok" in status
    assert "blocking" in status
    assert "warnings" in status


def test_write_pilot_readiness_report(tmp_path: Path) -> None:
    """write_pilot_readiness_report creates markdown file with recommendation."""
    from workflow_dataset.pilot.health import write_pilot_readiness_report
    out = tmp_path / "pilot_readiness_report.md"
    path = write_pilot_readiness_report(output_path=out, pilot_dir=tmp_path)
    assert path == out
    assert path.exists()
    content = path.read_text()
    assert "Pilot readiness report" in content
    assert "Recommendation" in content
    assert "Blocking" in content or "blocking" in content.lower()


def test_record_workflow_artifact_stores_template_id(tmp_path: Path) -> None:
    """M22E-F6: record_workflow_artifact appends artifact path and stores template_id in session extra."""
    from workflow_dataset.pilot.session_log import (
        start_session,
        get_current_session_id,
        load_session,
        record_workflow_artifact,
    )
    pilot_dir = tmp_path / "pilot"
    pilot_dir.mkdir()
    start_session(pilot_dir=pilot_dir)
    sid = get_current_session_id(pilot_dir)
    assert sid
    artifact_dir = tmp_path / "workspace_run"
    artifact_dir.mkdir()
    record_workflow_artifact(
        "ops_reporting_workspace",
        artifact_dir,
        pilot_dir=pilot_dir,
        template_id="ops_reporting_core",
    )
    record = load_session(sid, pilot_dir)
    assert str(artifact_dir.resolve()) in record.artifacts_produced
    assert isinstance(record.extra, dict)
    assert record.extra.get("template_id") == "ops_reporting_core"


def test_reliability_issues_json_loads() -> None:
    """data/local/pilot/reliability_issues.json is valid JSON and has expected categories."""
    path = Path("data/local/pilot/reliability_issues.json")
    if not path.exists():
        pytest.skip("reliability_issues.json not found")
    data = json.loads(path.read_text())
    assert isinstance(data, list)
    for item in data:
        assert "id" in item
        assert "category" in item
        assert item["category"] in ("must_fix_before_pilot", "acceptable_with_warning", "post_pilot")


def test_pilot_verify_cli_help() -> None:
    """pilot verify --help runs."""
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["pilot", "verify", "--help"])
    assert result.exit_code == 0
    assert "verify" in result.output.lower()


def test_pilot_status_cli_json(tmp_path: Path) -> None:
    """pilot status --json outputs valid JSON."""
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["pilot", "status", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "ready" in data
    assert "safe_to_demo" in data


def test_release_verify_exits_one_when_graph_missing(tmp_path: Path) -> None:
    """Release verify exits 1 when graph is missing (hardened)."""
    import yaml
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    config = tmp_path / "settings.yaml"
    config.write_text(yaml.dump({
        "project": {"name": "t", "version": "1", "output_excel": "x", "output_csv_dir": "c", "output_parquet_dir": "p", "qa_report_path": "q"},
        "runtime": {"timezone": "UTC"},
        "paths": {"raw_official": "r", "raw_private": "r", "interim": "i", "processed": "p", "prompts": "pr", "context": "c", "sqlite_path": "s", "graph_store_path": str(tmp_path / "nonexistent.sqlite")},
        "setup": {
            "setup_dir": str(tmp_path / "setup"),
            "parsed_artifacts_dir": str(tmp_path / "parsed"),
            "style_signals_dir": str(tmp_path / "style"),
            "style_profiles_dir": str(tmp_path / "profiles"),
            "suggestions_dir": str(tmp_path / "suggestions"),
            "draft_structures_dir": str(tmp_path / "drafts"),
        },
    }, default_flow_style=False))
    runner = CliRunner()
    result = runner.invoke(app, ["release", "verify", "--config", str(config)])
    assert result.exit_code == 1
    assert "Blocking" in result.output or "blocking" in result.output.lower()
