"""
M27I–M27L: Progress board + triggered replanning — signals, recommendation, diff, board.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.progress.models import ReplanSignal, REPLAN_SIGNAL_TYPES
from workflow_dataset.progress.store import (
    get_progress_dir,
    save_prior_plan,
    load_prior_plan,
    save_replan_signals,
    load_replan_signals,
    list_projects,
)
from workflow_dataset.progress.recommendation import (
    recommend_replan,
    compare_plans,
    explain_replan,
    format_plan_diff,
)
from workflow_dataset.progress.board import build_progress_board, format_progress_board


def test_replan_signal_roundtrip():
    s = ReplanSignal(
        signal_type="new_blocker_detected",
        project_id="default",
        reason="Plan has blocked condition",
        ref="approval_scope",
        evidence=["step_index=1"],
    )
    d = s.to_dict()
    assert d["signal_type"] == "new_blocker_detected"
    loaded = ReplanSignal.from_dict(d)
    assert loaded.reason == s.reason


def test_store_prior_plan(tmp_path):
    plan = {"plan_id": "p1", "goal_text": "Goal", "steps": [], "blocked_conditions": []}
    save_prior_plan("default", plan, tmp_path)
    assert get_progress_dir(tmp_path).exists()
    loaded = load_prior_plan("default", tmp_path)
    assert loaded is not None
    assert loaded["plan_id"] == "p1"


def test_store_replan_signals(tmp_path):
    signals = [
        ReplanSignal("repeated_failed_action", "default", "Recurring block", "job_1", [], ""),
    ]
    save_replan_signals(signals, tmp_path)
    loaded = load_replan_signals(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].signal_type == "repeated_failed_action"


def test_list_projects(tmp_path):
    save_prior_plan("proj_a", {"plan_id": "a", "steps": []}, tmp_path)
    projects = list_projects(tmp_path)
    assert "proj_a" in projects


def test_compare_plans():
    prior = {"steps": [{"step_index": 0, "label": "A"}], "blocked_conditions": [], "checkpoints": []}
    new = {"steps": [{"step_index": 0, "label": "A"}, {"step_index": 1, "label": "B"}], "blocked_conditions": [{"reason": "x", "step_index": 1}], "checkpoints": []}
    diff = compare_plans(prior, new)
    assert diff["prior_step_count"] == 1
    assert diff["new_step_count"] == 2
    assert diff["steps_added"] == ["B"]
    assert diff["blocked_changed"] is True


def test_explain_replan():
    signals = [ReplanSignal("new_blocker_detected", "default", "Plan blocked", "", [])]
    text = explain_replan(signals)
    assert "Replan suggested" in text
    assert "new_blocker_detected" in text


def test_format_plan_diff():
    diff = {"prior_step_count": 1, "new_step_count": 2, "steps_added": ["B"], "steps_removed": [], "blocked_changed": True, "checkpoints_changed": False, "prior_blocked_count": 0, "new_blocked_count": 1}
    text = format_plan_diff(diff)
    assert "Plan diff" in text
    assert "prior=1" in text
    assert "new=2" in text
    assert "Blocked" in text


def test_build_progress_board(tmp_path):
    board = build_progress_board(tmp_path)
    assert "active_projects" in board
    assert "project_health" in board
    assert "stalled_projects" in board
    assert "replan_needed_projects" in board
    assert "recurring_blockers" in board
    assert "next_intervention_candidate" in board


def test_format_progress_board(tmp_path):
    board = build_progress_board(tmp_path)
    text = format_progress_board(board)
    assert "Impact / Progress board" in text
    assert "Active projects" in text
    assert "Stalled" in text
    assert "Replan needed" in text


def test_recommend_replan_no_plan(tmp_path):
    rec = recommend_replan(project_id="default", repo_root=tmp_path)
    assert "recommended" in rec
    assert "reason" in rec
    assert "signals" in rec


# ----- M27L.1 Intervention playbooks + recovery -----
from workflow_dataset.progress.playbooks import (
    InterventionPlaybook,
    get_default_playbooks,
    list_playbooks,
)
from workflow_dataset.progress.recovery import (
    build_stalled_recovery,
    format_stalled_recovery,
    match_playbook,
)


def test_playbooks_default():
    playbooks = get_default_playbooks()
    assert len(playbooks) >= 4
    ids = [p.playbook_id for p in playbooks]
    assert "stalled_founder_ops" in ids
    assert "blocked_analyst_case" in ids
    assert "developer_stuck_approval_capability" in ids
    assert "document_heavy_stuck_extraction_review" in ids


def test_playbook_has_all_fields():
    playbooks = list_playbooks()
    for pb in playbooks:
        assert pb.playbook_id
        assert pb.trigger_pattern
        assert pb.operator_intervention
        assert pb.agent_next_step
        assert pb.escalation_defer_guidance
        d = pb.to_dict()
        assert d["playbook_id"] == pb.playbook_id


def test_match_playbook_by_cause():
    board = {"stalled_projects": ["default"], "replan_needed_projects": [], "recurring_blockers": [{"cause_code": "approval_missing", "source_ref": "x"}]}
    pb = match_playbook("default", board, cause_codes=["approval_missing"])
    assert pb is not None
    assert "approval" in pb.operator_intervention.lower() or "approval" in pb.trigger_pattern.lower()


def test_match_playbook_stalled_default():
    board = {"stalled_projects": ["default"], "replan_needed_projects": [], "recurring_blockers": []}
    pb = match_playbook("default", board, cause_codes=[], goal_hint="")
    assert pb is not None
    assert pb.playbook_id == "stalled_founder_ops"


def test_build_stalled_recovery(tmp_path):
    recovery = build_stalled_recovery(project_id="default", repo_root=tmp_path)
    assert "project_id" in recovery
    assert "board_snapshot" in recovery
    assert "matched_playbook" in recovery
    assert "matched_playbook_id" in recovery


def test_format_stalled_recovery(tmp_path):
    recovery = build_stalled_recovery(project_id="default", repo_root=tmp_path)
    text = format_stalled_recovery(recovery)
    assert "Stalled-project recovery" in text
    assert "Board snapshot" in text
    assert "Recommended operator intervention" in text or "Matched playbook" in text
