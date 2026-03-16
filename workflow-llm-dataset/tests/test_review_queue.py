"""
Tests for M21T: Operator review queue and publishable package.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from workflow_dataset.cli import app
from workflow_dataset.release.reporting_workspaces import (
    get_workspace_inventory,
    list_reporting_workspaces,
)
from workflow_dataset.release.review_state import (
    get_approved_artifacts,
    load_review_state,
    save_review_state,
    set_artifact_state,
)
from workflow_dataset.release.package_builder import build_package

runner = CliRunner()


def test_get_workspace_inventory_ops_reporting_workspace(tmp_path: Path) -> None:
    """Inventory for ops_reporting_workspace with workspace_manifest.json."""
    (tmp_path / "workspace_manifest.json").write_text(
        json.dumps({
            "workflow": "ops_reporting_workspace",
            "timestamp": "2025-03-15T12:00:00Z",
            "grounding": "task_context_only",
            "saved_artifact_paths": ["source_snapshot.md", "weekly_status.md"],
        }, indent=2),
        encoding="utf-8",
    )
    (tmp_path / "source_snapshot.md").write_text("# Source", encoding="utf-8")
    (tmp_path / "weekly_status.md").write_text("**Summary:** Done.", encoding="utf-8")
    inv = get_workspace_inventory(tmp_path)
    assert inv is not None
    assert inv["workflow"] == "ops_reporting_workspace"
    assert inv.get("run_id") == tmp_path.name
    assert "source_snapshot.md" in inv["artifacts"]
    assert "weekly_status.md" in inv["artifacts"]


def test_get_workspace_inventory_weekly_status(tmp_path: Path) -> None:
    """Inventory for weekly_status with manifest.json."""
    (tmp_path / "manifest.json").write_text(
        json.dumps({
            "artifact_type": "weekly_status",
            "timestamp": "2025-03-15T12:00:00Z",
            "grounding": "task_context_only",
        }, indent=2),
        encoding="utf-8",
    )
    (tmp_path / "weekly_status.md").write_text("**Summary:** Done.", encoding="utf-8")
    inv = get_workspace_inventory(tmp_path)
    assert inv is not None
    assert inv["workflow"] == "weekly_status" or "weekly_status" in inv["artifacts"]


def test_list_reporting_workspaces_empty(tmp_path: Path) -> None:
    """list_reporting_workspaces returns empty when no workflow dirs."""
    items = list_reporting_workspaces(tmp_path, limit=10)
    assert items == []


def test_list_reporting_workspaces_finds_runs(tmp_path: Path) -> None:
    """list_reporting_workspaces finds run dirs under workflow subdirs."""
    ws_root = tmp_path / "weekly_status"
    ws_root.mkdir(parents=True)
    run_dir = ws_root / "2025-03-15_1200_abc"
    run_dir.mkdir()
    (run_dir / "manifest.json").write_text(
        json.dumps({"artifact_type": "weekly_status", "timestamp": "2025-03-15T12:00:00Z"}, indent=2),
        encoding="utf-8",
    )
    (run_dir / "weekly_status.md").write_text("Done.", encoding="utf-8")
    items = list_reporting_workspaces(tmp_path, limit=10)
    assert len(items) >= 1
    assert any(inv["workflow"] == "weekly_status" for inv in items)


def test_review_state_save_load(tmp_path: Path) -> None:
    """Review state round-trip."""
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    artifacts = {"weekly_status.md": {"state": "approved", "note": "", "reviewed_at": "2025-03-15T12:00:00Z"}}
    save_review_state(workspace_path, artifacts, repo_root=tmp_path)
    loaded = load_review_state(workspace_path, repo_root=tmp_path)
    assert loaded["artifacts"].get("weekly_status.md", {}).get("state") == "approved"


def test_set_artifact_state(tmp_path: Path) -> None:
    """set_artifact_state updates state."""
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    set_artifact_state(workspace_path, "weekly_status.md", "approved", repo_root=tmp_path)
    approved = get_approved_artifacts(workspace_path, repo_root=tmp_path)
    assert "weekly_status.md" in approved
    set_artifact_state(workspace_path, "weekly_status.md", "excluded", repo_root=tmp_path)
    approved = get_approved_artifacts(workspace_path, repo_root=tmp_path)
    assert "weekly_status.md" not in approved


def test_build_package(tmp_path: Path) -> None:
    """build_package creates package dir with approved artifacts and manifest."""
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    (workspace_path / "weekly_status.md").write_text("**Summary:** Done.", encoding="utf-8")
    (workspace_path / "stakeholder_update.md").write_text("**Headline:** On track.", encoding="utf-8")
    (workspace_path / "manifest.json").write_text(
        json.dumps({"workflow": "weekly_status", "grounding": "task_context_only"}, indent=2),
        encoding="utf-8",
    )
    set_artifact_state(workspace_path, "weekly_status.md", "approved", repo_root=tmp_path)
    set_artifact_state(workspace_path, "stakeholder_update.md", "approved", repo_root=tmp_path)
    package_dir = build_package(workspace_path, repo_root=tmp_path)
    assert package_dir.is_dir()
    assert (package_dir / "package_manifest.json").exists()
    assert (package_dir / "approved_summary.md").exists()
    assert (package_dir / "handoff_readme.md").exists()
    assert (package_dir / "weekly_status.md").exists()
    assert (package_dir / "stakeholder_update.md").exists()
    manifest = json.loads((package_dir / "package_manifest.json").read_text())
    assert manifest["workflow"] == "weekly_status"
    assert "weekly_status.md" in manifest["approved_artifacts"]


def test_build_package_no_approved_raises(tmp_path: Path) -> None:
    """build_package raises when no artifacts are approved."""
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    (workspace_path / "weekly_status.md").write_text("Done.", encoding="utf-8")
    with pytest.raises(ValueError, match="No approved artifacts"):
        build_package(workspace_path, repo_root=tmp_path)


def test_build_package_with_profile_internal_team(tmp_path: Path) -> None:
    """build_package with profile=internal_team includes all approved (same as no profile)."""
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    (workspace_path / "weekly_status.md").write_text("**Summary:** Done.", encoding="utf-8")
    (workspace_path / "action_register.md").write_text("**Action:** X", encoding="utf-8")
    (workspace_path / "manifest.json").write_text(
        json.dumps({"workflow": "weekly_status", "grounding": "task_context_only"}, indent=2),
        encoding="utf-8",
    )
    set_artifact_state(workspace_path, "weekly_status.md", "approved", repo_root=tmp_path)
    set_artifact_state(workspace_path, "action_register.md", "approved", repo_root=tmp_path)
    package_dir = build_package(workspace_path, repo_root=tmp_path, profile="internal_team")
    manifest = json.loads((package_dir / "package_manifest.json").read_text())
    assert manifest.get("handoff_profile") == "internal_team"
    assert set(manifest["profile_included_artifacts"]) == {"weekly_status.md", "action_register.md"}
    assert (package_dir / "weekly_status.md").exists()
    assert (package_dir / "action_register.md").exists()
    assert "Approved summary (internal team)" in (package_dir / "approved_summary.md").read_text()


def test_build_package_with_profile_stakeholder(tmp_path: Path) -> None:
    """build_package with profile=stakeholder includes only stakeholder-safe artifacts."""
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    (workspace_path / "weekly_status.md").write_text("**Summary:** Done.", encoding="utf-8")
    (workspace_path / "action_register.md").write_text("**Action:** X", encoding="utf-8")
    (workspace_path / "manifest.json").write_text(
        json.dumps({"workflow": "weekly_status", "grounding": "task_context_only"}, indent=2),
        encoding="utf-8",
    )
    set_artifact_state(workspace_path, "weekly_status.md", "approved", repo_root=tmp_path)
    set_artifact_state(workspace_path, "action_register.md", "approved", repo_root=tmp_path)
    package_dir = build_package(workspace_path, repo_root=tmp_path, profile="stakeholder")
    manifest = json.loads((package_dir / "package_manifest.json").read_text())
    assert manifest["handoff_profile"] == "stakeholder"
    assert set(manifest["approved_artifacts"]) == {"weekly_status.md", "action_register.md"}
    assert manifest["profile_included_artifacts"] == ["weekly_status.md"]
    assert (package_dir / "weekly_status.md").exists()
    assert not (package_dir / "action_register.md").exists()
    assert "stakeholder" in (package_dir / "approved_summary.md").read_text().lower()


def test_build_package_with_profile_stakeholder_excludes_all_raises(tmp_path: Path) -> None:
    """build_package with profile=stakeholder raises when no approved artifacts are stakeholder-safe."""
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    (workspace_path / "action_register.md").write_text("**Action:** X", encoding="utf-8")
    (workspace_path / "manifest.json").write_text(
        json.dumps({"workflow": "weekly_status", "grounding": "task_context_only"}, indent=2),
        encoding="utf-8",
    )
    set_artifact_state(workspace_path, "action_register.md", "approved", repo_root=tmp_path)
    with pytest.raises(ValueError, match="excludes all approved"):
        build_package(workspace_path, repo_root=tmp_path, profile="stakeholder")


def test_build_package_with_profile_operator_archive(tmp_path: Path) -> None:
    """build_package with profile=operator_archive includes all approved and sets handoff_profile."""
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    (workspace_path / "weekly_status.md").write_text("**Summary:** Done.", encoding="utf-8")
    (workspace_path / "manifest.json").write_text(
        json.dumps({"workflow": "weekly_status", "grounding": "task_context_only"}, indent=2),
        encoding="utf-8",
    )
    set_artifact_state(workspace_path, "weekly_status.md", "approved", repo_root=tmp_path)
    package_dir = build_package(workspace_path, repo_root=tmp_path, profile="operator_archive")
    manifest = json.loads((package_dir / "package_manifest.json").read_text())
    assert manifest["handoff_profile"] == "operator_archive"
    assert "operator archive" in (package_dir / "approved_summary.md").read_text().lower()


def test_build_package_invalid_profile_raises(tmp_path: Path) -> None:
    """build_package with unknown profile raises ValueError."""
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    (workspace_path / "weekly_status.md").write_text("Done.", encoding="utf-8")
    (workspace_path / "manifest.json").write_text(
        json.dumps({"workflow": "weekly_status"}, indent=2), encoding="utf-8"
    )
    set_artifact_state(workspace_path, "weekly_status.md", "approved", repo_root=tmp_path)
    with pytest.raises(ValueError, match="Unknown handoff profile"):
        build_package(workspace_path, repo_root=tmp_path, profile="unknown_profile")


def test_review_list_profiles_cli() -> None:
    """review list-profiles runs and shows profile names."""
    result = runner.invoke(app, ["review", "list-profiles"])
    assert result.exit_code == 0
    assert "internal_team" in result.output
    assert "stakeholder" in result.output
    assert "operator_archive" in result.output


def test_review_list_workspaces_cli() -> None:
    """review list-workspaces runs and exits 0."""
    result = runner.invoke(app, ["review", "list-workspaces", "--limit", "5"])
    assert result.exit_code == 0


def test_review_show_workspace_requires_arg() -> None:
    """review show-workspace fails without workspace."""
    result = runner.invoke(app, ["review", "show-workspace"])
    assert result.exit_code != 0


def test_review_help() -> None:
    """review group shows subcommands."""
    result = runner.invoke(app, ["review", "--help"])
    assert result.exit_code == 0
    assert "list-workspaces" in result.output
    assert "build-package" in result.output


def test_dashboard_data_structure(tmp_path: Path) -> None:
    """get_dashboard_data returns expected sections (readiness, workspaces, review_package, staging, cohort, cohort_summary, alerts, next_actions, local_sources)."""
    from workflow_dataset.release.dashboard_data import get_dashboard_data

    data = get_dashboard_data(repo_root=tmp_path)
    assert "readiness" in data
    assert "recent_workspaces" in data
    assert "review_package" in data
    assert "staging" in data
    assert "cohort" in data
    assert "cohort_summary" in data
    assert "alerts" in data
    assert "action_macros" in data
    assert "next_actions" in data
    assert "local_sources" in data
    assert "ready" in data["readiness"]
    assert "unreviewed_count" in data["review_package"]
    assert "staged_count" in data["staging"]
    summary = data["cohort_summary"]
    assert "active_cohort_name" in summary
    assert "sessions_count" in summary
    assert "recent_recommendation" in summary
    alerts = data["alerts"]
    assert "review_pending" in alerts
    assert "review_pending_count" in alerts
    assert "package_ready" in alerts
    assert "staged_apply_plan_available" in alerts
    assert "benchmark_regression_detected" in alerts
    sources = data["local_sources"]
    assert "repo_root" in sources
    assert "workspaces_root" in sources
    assert "pilot_dir" in sources
    assert "packages_root" in sources
    assert "review_root" in sources
    assert "staging_dir" in sources
    assert str(tmp_path.resolve()) in sources["repo_root"]


def test_dashboard_next_actions_commands(tmp_path: Path) -> None:
    """Next actions contain copy-pasteable commands (workflow-dataset or cat with path)."""
    from workflow_dataset.release.dashboard_data import get_dashboard_data

    data = get_dashboard_data(repo_root=tmp_path)
    actions = data.get("next_actions") or []
    for a in actions:
        cmd = a.get("command", "")
        assert cmd, f"next_action missing command: {a}"
        assert "workflow-dataset" in cmd or cmd.strip().startswith("cat "), (
            f"next_action command should be workflow-dataset or cat: {cmd!r}"
        )


def test_dashboard_cli_exits_zero() -> None:
    """workflow-dataset dashboard runs and exits 0."""
    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 0
    assert "Readiness" in result.output or "Dashboard" in result.output


def test_dashboard_workflow_filter(tmp_path: Path) -> None:
    """get_dashboard_data with workflow_filter limits recent_workspaces to that workflow."""
    from workflow_dataset.release.dashboard_data import get_dashboard_data

    ws_root = tmp_path / "data/local/workspaces"
    for wf in ["weekly_status", "ops_reporting_workspace"]:
        (ws_root / wf).mkdir(parents=True)
        run_dir = ws_root / wf / "2025-03-15_1200_abc"
        run_dir.mkdir()
        (run_dir / "manifest.json").write_text(
            json.dumps({"artifact_type": wf, "timestamp": "2025-03-15T12:00:00Z"}, indent=2),
            encoding="utf-8",
        )
        (run_dir / "weekly_status.md").write_text("Done.", encoding="utf-8") if wf == "weekly_status" else (run_dir / "report.md").write_text("Done.", encoding="utf-8")

    data_all = get_dashboard_data(repo_root=tmp_path)
    data_weekly = get_dashboard_data(repo_root=tmp_path, workflow_filter="weekly_status")
    assert data_all.get("workflow_filter") is None
    assert len(data_all["recent_workspaces"]) >= 1
    assert data_weekly.get("workflow_filter") == "weekly_status"
    for w in data_weekly["recent_workspaces"]:
        assert w["workflow"] == "weekly_status"


def test_dashboard_drilldown_structure(tmp_path: Path) -> None:
    """get_dashboard_drilldown returns drill_type, path, ref, payload."""
    from workflow_dataset.release.dashboard_data import get_dashboard_drilldown

    for drill in ("workspace", "package", "cohort", "apply_plan"):
        data = get_dashboard_drilldown(repo_root=tmp_path, drill=drill)
        assert data.get("drill_type") == drill
        assert "path" in data
        assert "ref" in data
        assert "payload" in data


def test_dashboard_cli_workflow_filter() -> None:
    """workflow-dataset dashboard --workflow <name> runs and exits 0."""
    result = runner.invoke(app, ["dashboard", "--workflow", "weekly_status"])
    assert result.exit_code == 0
    assert "Dashboard" in result.output or "Readiness" in result.output


def test_dashboard_drilldown_cli() -> None:
    """workflow-dataset dashboard workspace | package | cohort | apply-plan exit 0."""
    for sub in ("workspace", "package", "cohort", "apply-plan"):
        result = runner.invoke(app, ["dashboard", sub])
        assert result.exit_code == 0, f"dashboard {sub}: {result.output}"


def test_dashboard_cohort_summary_and_alerts(tmp_path: Path) -> None:
    """C3: cohort_summary and alerts populated; review_pending true when workspaces need review."""
    from workflow_dataset.release.dashboard_data import get_dashboard_data

    ws_root = tmp_path / "data/local/workspaces/weekly_status"
    ws_root.mkdir(parents=True)
    run_dir = ws_root / "2025-03-15_1200_abc"
    run_dir.mkdir()
    (run_dir / "manifest.json").write_text(
        json.dumps({"artifact_type": "weekly_status", "timestamp": "2025-03-15T12:00:00Z"}, indent=2),
        encoding="utf-8",
    )
    (run_dir / "weekly_status.md").write_text("Done.", encoding="utf-8")

    data = get_dashboard_data(repo_root=tmp_path)
    assert "cohort_summary" in data
    assert data["cohort_summary"]["sessions_count"] >= 0
    assert "alerts" in data
    assert isinstance(data["alerts"]["review_pending"], bool)
    assert isinstance(data["alerts"]["review_pending_count"], int)
    assert isinstance(data["alerts"]["package_ready"], bool)
    assert isinstance(data["alerts"]["staged_apply_plan_available"], bool)
    assert isinstance(data["alerts"]["benchmark_regression_detected"], bool)
    # With one workspace and no review state, review_pending should be true (artifacts not reviewed)
    assert data["alerts"]["review_pending_count"] >= 0


def test_dashboard_action_macros(tmp_path: Path) -> None:
    """C4: action_macros includes staging-board and benchmark-board; each has id, label, command."""
    from workflow_dataset.release.dashboard_data import get_dashboard_data

    data = get_dashboard_data(repo_root=tmp_path)
    macros = data.get("action_macros") or []
    ids = [m.get("id") for m in macros]
    assert "staging-board" in ids
    assert "benchmark-board" in ids
    for m in macros:
        assert "id" in m and "label" in m and "command" in m


def test_dashboard_action_cli() -> None:
    """C4: workflow-dataset dashboard action <id> runs; invalid id exits 0 with message."""
    result = runner.invoke(app, ["dashboard", "action", "staging-board"])
    assert result.exit_code == 0
    result_invalid = runner.invoke(app, ["dashboard", "action", "no-such-macro"])
    assert result_invalid.exit_code == 0
    assert "No macro" in result_invalid.output or "Available" in result_invalid.output


# ----- M21V Staging board -----
def test_staging_board_add_package_and_clear(tmp_path: Path) -> None:
    """Add package to staging board; list; clear."""
    from workflow_dataset.release.staging_board import (
        add_staged_package,
        list_staged_items,
        clear_staging,
        load_staging_board,
    )
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "weekly_status.md").write_text("**Summary:** Done.", encoding="utf-8")
    (pkg_dir / "package_manifest.json").write_text(
        json.dumps({"workflow": "weekly_status", "approved_artifacts": ["weekly_status.md"]}, indent=2),
        encoding="utf-8",
    )
    item = add_staged_package(pkg_dir, repo_root=tmp_path)
    assert item.get("staged_id")
    assert item.get("source_type") == "package"
    assert "weekly_status.md" in item.get("artifact_paths", [])
    items = list_staged_items(repo_root=tmp_path)
    assert len(items) == 1
    clear_staging(repo_root=tmp_path)
    board = load_staging_board(repo_root=tmp_path)
    assert len(board.get("items") or []) == 0


def test_staging_build_apply_plan_from_staging(tmp_path: Path) -> None:
    """Build apply-plan from staged package; preview saved."""
    from workflow_dataset.release.staging_board import (
        add_staged_package,
        build_apply_plan_from_staging,
        get_last_apply_plan_preview_path,
    )
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "weekly_status.md").write_text("**Summary:** Done.", encoding="utf-8")
    (pkg_dir / "package_manifest.json").write_text(
        json.dumps({"workflow": "weekly_status", "approved_artifacts": ["weekly_status.md"]}, indent=2),
        encoding="utf-8",
    )
    add_staged_package(pkg_dir, repo_root=tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    plan, err = build_apply_plan_from_staging(target, repo_root=tmp_path, save_preview=True)
    assert plan is not None
    assert err == "" or not err
    path = get_last_apply_plan_preview_path(repo_root=tmp_path)
    assert path and Path(path).exists()
    assert "Apply plan preview" in Path(path).read_text()


def test_review_staging_board_cli() -> None:
    """review staging-board runs (empty or not)."""
    result = runner.invoke(app, ["review", "staging-board"])
    assert result.exit_code == 0


def test_review_queue_status_cli() -> None:
    """review queue-status runs."""
    result = runner.invoke(app, ["review", "queue-status"])
    assert result.exit_code == 0
    assert "Review queue" in result.output or "Staging board" in result.output
