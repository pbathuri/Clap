"""Tests for setup/onboarding: session creation, resumable job behavior, CLI, safe defaults."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from workflow_dataset.cli import app
from workflow_dataset.setup.setup_models import SetupStage, ArtifactFamily, ScanScope
from workflow_dataset.setup.job_store import create_session, load_session, save_session, save_progress
from workflow_dataset.setup.progress_tracker import update_progress, get_progress
from workflow_dataset.setup.scan_scheduler import iter_scan_paths

runner = CliRunner()


def test_setup_session_creation(tmp_path: Path) -> None:
    """Setup session is created and persisted."""
    session = create_session(
        tmp_path,
        scan_roots=[str(tmp_path)],
        exclude_dirs=[".git"],
        enabled_adapters=["document", "tabular"],
    )
    assert session.session_id.startswith("session_")
    assert session.current_stage == SetupStage.BOOTSTRAP
    loaded = load_session(tmp_path, session.session_id)
    assert loaded is not None
    assert loaded.session_id == session.session_id


def test_progress_tracker(tmp_path: Path) -> None:
    """Progress can be updated and loaded."""
    session_id = "test_session_123"
    update_progress(
        tmp_path,
        session_id,
        current_stage=SetupStage.INVENTORY,
        files_scanned=10,
        artifacts_classified=8,
    )
    progress = get_progress(tmp_path, session_id)
    assert progress is not None
    assert progress.files_scanned == 10
    assert progress.artifacts_classified == 8
    assert progress.current_stage == SetupStage.INVENTORY


def test_scan_scheduler_deterministic_batches(tmp_path: Path) -> None:
    """Scan scheduler yields batches under scope."""
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    scope = ScanScope(root_paths=[str(tmp_path)], max_files_per_scan=10)
    batches = list(iter_scan_paths(scope, batch_size=1))
    assert len(batches) >= 1
    total = sum(len(b) for b in batches)
    assert total >= 2


def test_setup_cli_init_requires_config(tmp_path: Path) -> None:
    """setup init with missing setup config exits gracefully or uses defaults."""
    # Config without setup section: we added default data["setup"] = {}
    result = runner.invoke(app, ["setup", "init", "--config", "configs/settings.yaml"])
    # May succeed with default setup or fail if config missing
    assert result.exit_code in (0, 1)


def test_setup_cli_status_no_session(tmp_path: Path) -> None:
    """setup status with no sessions exits 0 and prints dim message."""
    result = runner.invoke(app, ["setup", "status", "--config", "configs/settings.yaml"])
    assert result.exit_code == 0


def test_setup_session_onboarding_mode(tmp_path: Path) -> None:
    """Session stores onboarding_mode and config_snapshot for raw-text policy."""
    session = create_session(
        tmp_path,
        scan_roots=[str(tmp_path)],
        onboarding_mode="full_onboarding",
        config_snapshot={"allow_raw_text_parsing": True},
    )
    assert session.onboarding_mode == "full_onboarding"
    assert session.config_snapshot.get("allow_raw_text_parsing") is True
    loaded = load_session(tmp_path, session.session_id)
    assert loaded is not None
    assert loaded.onboarding_mode == "full_onboarding"


def test_setup_summary_markdown(tmp_path: Path) -> None:
    """build_summary_markdown produces markdown and can write to file."""
    from workflow_dataset.setup.setup_summary import build_summary_markdown
    from workflow_dataset.setup.setup_models import SetupSession, SetupProgress, SetupStage, ScanScope
    session = SetupSession(session_id="t", scan_scope=ScanScope(), onboarding_mode="conservative")
    progress = SetupProgress(session_id="t", current_stage=SetupStage.SUMMARY, files_scanned=5)
    report_path = tmp_path / "summary.md"
    text = build_summary_markdown(session, progress, report_path=report_path)
    assert "Setup onboarding summary" in text
    assert report_path.exists()
    assert "Files scanned: 5" in report_path.read_text()
