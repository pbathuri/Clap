"""
Tests for the operator console service layer.

Service wrappers call existing backend; tests use fixtures or empty config to avoid side effects.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.settings import load_settings, Settings
from workflow_dataset.ui.services import (
    get_settings,
    _resolve_latest_session_id,
    get_setup_sessions,
    get_setup_progress,
    get_projects,
    get_suggestions,
    get_drafts,
    get_style_profiles,
    get_workspaces,
    list_rollback_records,
    get_home_counts,
    build_apply_plan,
    get_diff_preview,
    run_rollback,
)


@pytest.fixture
def minimal_config(tmp_path: Path) -> Path:
    """Minimal settings YAML with paths under tmp_path."""
    config = tmp_path / "settings.yaml"
    data = {
        "project": {"name": "t", "version": "1", "output_excel": "out.xlsx", "output_csv_dir": "csv", "output_parquet_dir": "pq", "qa_report_path": "qa.md"},
        "runtime": {"timezone": "UTC"},
        "paths": {
            "raw_official": "raw",
            "raw_private": "raw_p",
            "interim": "interim",
            "processed": "proc",
            "prompts": "prompts",
            "context": "ctx",
            "sqlite_path": "w.sqlite",
            "event_log_dir": str(tmp_path / "events"),
            "graph_store_path": str(tmp_path / "graph.sqlite"),
        },
        "setup": {
            "setup_dir": str(tmp_path / "setup"),
            "parsed_artifacts_dir": str(tmp_path / "parsed"),
            "style_signals_dir": str(tmp_path / "style"),
            "setup_reports_dir": str(tmp_path / "reports"),
            "style_profiles_dir": str(tmp_path / "profiles"),
            "suggestions_dir": str(tmp_path / "suggestions"),
            "draft_structures_dir": str(tmp_path / "drafts"),
        },
        "materialization": {"materialization_workspace_root": str(tmp_path / "workspaces")},
        "apply": {"apply_manifest_root": str(tmp_path / "applies"), "apply_rollback_enabled": True},
    }
    import yaml
    config.write_text(yaml.dump(data), encoding="utf-8")
    return config


def test_get_settings(minimal_config: Path) -> None:
    settings = get_settings(str(minimal_config))
    assert settings is not None
    assert settings.paths.graph_store_path


def test_resolve_latest_session_empty(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    assert _resolve_latest_session_id(settings) is None


def test_get_setup_sessions_empty(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    sessions = get_setup_sessions(settings)
    assert sessions == []


def test_get_setup_progress_no_session(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    progress = get_setup_progress(settings, None)
    assert progress is None


def test_get_projects_empty(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    projects = get_projects(settings)
    assert projects == []


def test_get_suggestions_empty(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    suggestions = get_suggestions(settings)
    assert suggestions == []


def test_get_drafts_empty(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    drafts = get_drafts(settings)
    assert drafts == []


def test_get_workspaces_empty(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    workspaces = get_workspaces(settings, limit=10)
    assert workspaces == []


def test_list_rollback_records_empty(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    records = list_rollback_records(settings)
    assert records == []


def test_get_home_counts(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    counts = get_home_counts(settings, None)
    assert "sessions" in counts
    assert "projects" in counts
    assert "suggestions" in counts
    assert "drafts" in counts
    assert "workspaces" in counts
    assert "rollback_records" in counts
    assert counts["sessions"] == 0
    assert counts["projects"] == 0


def test_build_apply_plan_nonexistent_workspace(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    plan, err = build_apply_plan(settings, Path("/nonexistent/ws"), Path("/nonexistent/target"))
    assert plan is None
    assert err


def test_get_diff_preview_empty_plan() -> None:
    from workflow_dataset.apply.apply_models import ApplyPlan
    from workflow_dataset.utils.dates import utc_now_iso
    from workflow_dataset.utils.hashes import stable_id
    plan = ApplyPlan(plan_id=stable_id("plan", "t", utc_now_iso()), operations=[], created_utc=utc_now_iso())
    text = get_diff_preview(plan)
    assert isinstance(text, str)


def test_run_rollback_unknown_token(minimal_config: Path) -> None:
    settings = load_settings(str(minimal_config))
    ok, msg = run_rollback(settings, "rb_nonexistent_token_xyz")
    assert ok is False
    assert "not found" in msg or "disabled" in msg or len(msg) > 0
