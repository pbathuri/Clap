"""M22B: Mission control layer — state aggregation, next-action, report. Local-first; operator-controlled."""

from __future__ import annotations

import pytest

from workflow_dataset.mission_control import (
    get_mission_control_state,
    recommend_next_action,
    format_mission_control_report,
)
from workflow_dataset.mission_control.next_action import ACTIONS


def test_mission_control_state_structure(tmp_path):
    """get_mission_control_state(repo_root) returns dict with four sections and local_sources."""
    state = get_mission_control_state(tmp_path)
    assert isinstance(state, dict)
    assert "product_state" in state
    assert "evaluation_state" in state
    assert "development_state" in state
    assert "incubator_state" in state
    assert "local_sources" in state
    assert state["local_sources"].get("repo_root") == str(tmp_path.resolve())


def test_mission_control_state_includes_desktop_bridge(tmp_path):
    """M23H: get_mission_control_state includes desktop_bridge when available."""
    state = get_mission_control_state(tmp_path)
    assert "desktop_bridge" in state
    db = state["desktop_bridge"]
    if "error" not in db:
        assert "adapters_count" in db
        assert "approvals_path" in db
        assert "approvals_file_exists" in db
        assert "tasks_count" in db
        assert "adapter_ids" in db


def test_recommend_next_action_returns_valid_action():
    """recommend_next_action(state) returns action in ACTIONS and a rationale."""
    state = {
        "product_state": {},
        "evaluation_state": {"recommendation": "ship", "runs_count": 1},
        "development_state": {"pending_proposals": 0},
        "incubator_state": {"candidates_total": 0},
    }
    rec = recommend_next_action(state)
    assert rec.get("action") in ACTIONS
    assert rec.get("rationale")


def test_recommend_rollback_when_revert():
    """When evaluation_state.recommendation == 'revert', action is rollback."""
    state = {
        "product_state": {},
        "evaluation_state": {"recommendation": "revert", "latest_run_id": "abc"},
        "development_state": {},
        "incubator_state": {},
    }
    rec = recommend_next_action(state)
    assert rec["action"] == "rollback"
    assert "revert" in rec.get("rationale", "").lower() or "regression" in rec.get("rationale", "").lower()


def test_format_report():
    """format_mission_control_report returns string with expected sections and operator note."""
    state = {
        "product_state": {"validated_workflows": ["w1"], "cohort_recommendation": None, "cohort_sessions_count": 0, "review_package": {}},
        "evaluation_state": {"latest_run_id": None, "recommendation": "hold", "runs_count": 0},
        "development_state": {"experiment_queue": {}, "pending_proposals": 0, "accepted_proposals": 0, "rejected_proposals": 0},
        "incubator_state": {"candidates_by_stage": {}, "promoted_count": 0, "rejected_count": 0, "hold_count": 0},
        "coordination_graph_summary": {"tasks_count": 0, "total_nodes": 0, "total_edges": 0},
        "desktop_bridge": {
            "adapters_count": 4,
            "adapter_ids": ["file_ops", "notes_document", "browser_open", "app_launch"],
            "approvals_path": "/some/approvals.yaml",
            "approvals_file_exists": False,
            "tasks_count": 0,
            "coordination_nodes": 0,
            "coordination_edges": 0,
        },
        "local_sources": {},
    }
    report = format_mission_control_report(state=state)
    assert "Mission Control" in report
    assert "[Product]" in report
    assert "[Evaluation]" in report
    assert "[Development]" in report
    assert "[Incubator]" in report
    assert "[Desktop bridge]" in report
    assert "Recommended next action" in report
    assert "Operator-controlled" in report


def test_recommend_replay_task_when_tasks_available():
    """M23H: When coordination_graph_summary.tasks_count > 0 and no higher-priority signal, recommend replay_task."""
    state = {
        "product_state": {"review_package": {"unreviewed_count": 0}, "cohort_recommendation": ""},
        "evaluation_state": {"recommendation": "ship", "runs_count": 5},
        "development_state": {"pending_proposals": 0},
        "incubator_state": {"candidates_total": 0},
        "observation_state": {"enabled_sources": ["file"]},
        "coordination_graph_summary": {"tasks_count": 3, "total_nodes": 5, "total_edges": 2},
    }
    rec = recommend_next_action(state)
    assert rec.get("action") == "replay_task"
    assert "replay" in rec.get("rationale", "").lower() or "task" in rec.get("rationale", "").lower()


def test_mission_control_incubator_no_error_when_present(tmp_path):
    """M23W: With incubator package present, incubator_state has no avoidable error."""
    state = get_mission_control_state(tmp_path)
    ins = state.get("incubator_state", {})
    assert "error" not in ins


def test_mission_control_report_includes_environment(tmp_path):
    """M23W: Report includes [Environment] section when environment_health in state."""
    state = get_mission_control_state(tmp_path)
    report = format_mission_control_report(state=state)
    assert "[Environment]" in report


def test_mission_control_report_includes_starter_kits(tmp_path):
    """M23Y: Report includes [Starter kits] section when starter_kits in state."""
    state = get_mission_control_state(tmp_path)
    report = format_mission_control_report(state=state)
    assert "[Starter kits]" in report
