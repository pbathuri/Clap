"""M24F: Tests for rollout manager — demo definitions, launcher, tracker, support bundle, issues report, mission_control rollout block."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.rollout.demos import list_demos, get_demo, GuidedDemo, DEMO_TO_SCENARIO
from workflow_dataset.rollout.tracker import (
    load_rollout_state,
    save_rollout_state,
    update_rollout_from_acceptance,
    get_rollout_dir,
    get_state_path,
)
from workflow_dataset.rollout.support_bundle import build_support_bundle, build_support_bundle_summary_only
from workflow_dataset.rollout.issues import format_issues_report
from workflow_dataset.rollout.launcher import launch_golden_journey
from workflow_dataset.rollout.readiness import build_rollout_readiness_report, format_rollout_readiness_report
from workflow_dataset.rollout.runbooks import list_runbooks, get_runbook_path, get_runbook_content


def test_demo_definitions() -> None:
    ids = list_demos()
    assert "founder_demo" in ids
    assert "analyst_demo" in ids
    assert "developer_demo" in ids
    assert "document_worker_demo" in ids


def test_get_demo() -> None:
    d = get_demo("founder_demo")
    assert d is not None
    assert isinstance(d, GuidedDemo)
    assert d.demo_id == "founder_demo"
    assert d.required_pack == "founder_ops_starter"
    assert "install_readiness" in d.demo_steps
    assert get_demo("nonexistent") is None


def test_demo_to_scenario_mapping() -> None:
    assert DEMO_TO_SCENARIO["founder_demo"] == "founder_first_run"
    assert DEMO_TO_SCENARIO["analyst_demo"] == "analyst_first_run"


def test_tracker_load_save(tmp_path: Path) -> None:
    state_path = get_state_path(tmp_path)
    assert state_path.parent == get_rollout_dir(tmp_path)
    empty = load_rollout_state(tmp_path)
    assert empty == {} or "updated_at" in empty
    state = {"target_scenario_id": "founder_first_run", "current_stage": "in_progress"}
    path = save_rollout_state(state, tmp_path)
    assert path.exists()
    loaded = load_rollout_state(tmp_path)
    assert loaded.get("target_scenario_id") == "founder_first_run"
    assert loaded.get("current_stage") == "in_progress"
    assert "updated_at" in loaded


def test_update_rollout_from_acceptance(tmp_path: Path) -> None:
    result = {
        "scenario_id": "founder_first_run",
        "outcome": "pass",
        "reasons": ["All critical steps met."],
        "ready_for_trial": True,
    }
    state = update_rollout_from_acceptance(result, repo_root=tmp_path, target_scenario_id="founder_first_run")
    assert state.get("target_scenario_id") == "founder_first_run"
    assert state.get("current_stage") == "ready_for_trial"
    assert "acceptance_pass" in state.get("passed_readiness_checks", [])
    assert state.get("latest_acceptance_result", {}).get("outcome") == "pass"
    assert "next_required_action" in state


def test_support_bundle_creation(tmp_path: Path) -> None:
    out_dir = tmp_path / "bundle_out"
    summary = build_support_bundle(repo_root=tmp_path, output_dir=out_dir)
    assert summary.get("output_dir") == str(out_dir)
    assert (out_dir / "environment_health.json").exists()
    assert (out_dir / "runtime_mesh.json").exists()
    assert (out_dir / "starter_kits.json").exists()
    assert (out_dir / "latest_acceptance.json").exists()
    assert (out_dir / "trust_cockpit.json").exists()
    assert (out_dir / "rollout_state.json").exists()
    assert (out_dir / "issue_summary.txt").exists()
    assert "issue_summary_path" in summary


def test_support_bundle_summary_only(tmp_path: Path) -> None:
    summary = build_support_bundle_summary_only(repo_root=tmp_path)
    assert "environment_health" in summary
    assert "runtime_mesh" in summary
    assert "starter_kits" in summary
    assert "latest_acceptance" in summary
    assert "rollout_state" in summary
    assert "trust_cockpit" in summary


def test_format_issues_report() -> None:
    text = format_issues_report(None)
    assert "Support / issue summary" in text
    assert "Steps to reproduce" in text
    summary = {
        "environment_health": {"required_ok": True},
        "latest_acceptance": {"scenario_id": "founder_first_run", "outcome": "pass", "ready_for_trial": True},
        "rollout_state": {"current_stage": "ready_for_trial", "next_required_action": "Proceed."},
    }
    text2 = format_issues_report(summary)
    assert "founder_first_run" in text2
    assert "ready_for_trial" in text2


def test_launch_golden_journey_unknown_demo(tmp_path: Path) -> None:
    result = launch_golden_journey("nonexistent_demo", repo_root=tmp_path)
    assert result.get("error")
    assert result.get("outcome") == "fail"
    assert "next_step" in result


def test_launch_golden_journey_founder(tmp_path: Path) -> None:
    """Launcher runs acceptance and returns outcome/next_step; may pass/partial/blocked/fail depending on env."""
    result = launch_golden_journey("founder_demo", repo_root=tmp_path)
    assert "demo_id" in result
    assert result.get("demo_id") == "founder_demo"
    assert result.get("scenario_id") == "founder_first_run"
    assert result.get("outcome") in ("pass", "partial", "blocked", "fail", None) or "error" in result
    assert "next_step" in result


def test_mission_control_includes_rollout(tmp_path: Path) -> None:
    """Mission control state includes rollout section when rollout module is available."""
    from workflow_dataset.mission_control.state import get_mission_control_state
    state = get_mission_control_state(tmp_path)
    assert "rollout" in state
    ro = state["rollout"]
    if "error" not in ro:
        assert "rollout_status" in ro or "demo_readiness" in ro or "next_rollout_action" in ro


def test_readiness_report_generation(tmp_path: Path) -> None:
    """Readiness report returns structure with demo_ready, first_user_ready, blocks, operator_actions, experimental."""
    r = build_rollout_readiness_report(tmp_path)
    assert "demo_ready" in r
    assert "first_user_ready" in r
    assert "blocks" in r
    assert "operator_actions" in r
    assert "experimental" in r
    assert isinstance(r["demo_ready"], bool)
    assert isinstance(r["blocks"], list)
    text = format_rollout_readiness_report(tmp_path)
    assert "Rollout readiness" in text
    assert "Demo-ready" in text
    assert "First-user-ready" in text
    assert "Blocks" in text
    assert "Operator actions" in text


def test_readiness_report_blocked_state(tmp_path: Path) -> None:
    """When rollout state has blocked_items and stage != ready_for_trial, demo_ready is False and blocks listed."""
    from workflow_dataset.rollout.tracker import save_rollout_state
    save_rollout_state({
        "target_scenario_id": "founder_first_run",
        "current_stage": "blocked",
        "blocked_items": ["Install check did not pass.", "Missing: config file"],
        "next_required_action": "Fix install check and re-run acceptance.",
        "latest_acceptance_result": {"outcome": "blocked", "ready_for_trial": False},
    }, repo_root=tmp_path)
    r = build_rollout_readiness_report(tmp_path)
    assert r["demo_ready"] is False
    assert len(r["blocks"]) >= 1
    assert any("blocked" in str(b).lower() or "install" in str(b).lower() for b in r["blocks"])
    assert len(r["operator_actions"]) >= 1


def test_runbooks_list() -> None:
    """Runbooks module lists operator_runbooks and recovery_escalation."""
    ids = list_runbooks()
    assert "operator_runbooks" in ids
    assert "recovery_escalation" in ids


def test_runbooks_path_and_content(tmp_path: Path) -> None:
    """When docs/rollout/OPERATOR_RUNBOOKS.md exists, get_runbook_path and get_runbook_content return path and content."""
    (tmp_path / "docs" / "rollout").mkdir(parents=True)
    (tmp_path / "docs" / "rollout" / "OPERATOR_RUNBOOKS.md").write_text("# Operator runbooks\n\nHow to run demos.", encoding="utf-8")
    (tmp_path / "docs" / "rollout" / "RECOVERY_ESCALATION.md").write_text("# Recovery\n\nEscalation decision tree.", encoding="utf-8")
    path = get_runbook_path("operator_runbooks", tmp_path)
    assert path is not None
    assert path.name == "OPERATOR_RUNBOOKS.md"
    content = get_runbook_content("operator_runbooks", tmp_path)
    assert content is not None
    assert "Operator runbooks" in content
    assert "run demos" in content
    rec = get_runbook_content("recovery_escalation", tmp_path)
    assert rec is not None
    assert "Recovery" in rec
    assert "Escalation" in rec
