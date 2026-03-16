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
        "local_sources": {},
    }
    report = format_mission_control_report(state=state)
    assert "Mission Control" in report
    assert "[Product]" in report
    assert "[Evaluation]" in report
    assert "[Development]" in report
    assert "[Incubator]" in report
    assert "Recommended next action" in report
    assert "Operator-controlled" in report
