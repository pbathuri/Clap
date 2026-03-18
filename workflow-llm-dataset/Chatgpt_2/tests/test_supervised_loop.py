"""
M27E–M27H: Tests for supervised agent loop — next-action proposal, approval queue, handoff, cycle summary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.supervised_loop.models import (
    AgentCycle,
    QueuedAction,
    ApprovalQueueItem,
    ExecutionHandoff,
    CycleSummary,
    BlockedCycleReason,
    OperatorPolicy,
    RISK_ORDER,
)
from workflow_dataset.supervised_loop.store import (
    get_loop_dir,
    save_cycle,
    load_cycle,
    load_queue,
    save_queue,
    append_queue_history,
    append_handoff,
    load_handoffs,
    load_operator_policy,
    save_operator_policy,
)
from workflow_dataset.supervised_loop.next_action import propose_next_actions
from workflow_dataset.supervised_loop.queue import (
    enqueue_proposal,
    list_pending,
    list_pending_sorted,
    list_deferred,
    get_item,
    approve,
    reject,
    defer,
    revisit_deferred,
    approve_batch,
)
from workflow_dataset.supervised_loop.summary import build_cycle_summary


def test_agent_cycle_roundtrip(tmp_path: Path) -> None:
    cycle = AgentCycle(
        cycle_id="cy_test1",
        project_slug="founder_case_alpha",
        goal_text="Ship weekly report",
        status="awaiting_approval",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    d = cycle.to_dict()
    back = AgentCycle.from_dict(d)
    assert back.cycle_id == cycle.cycle_id
    assert back.project_slug == cycle.project_slug
    assert back.goal_text == cycle.goal_text
    assert back.status == cycle.status


def test_save_load_cycle(tmp_path: Path) -> None:
    cycle = AgentCycle(
        cycle_id="cy_save",
        project_slug="p1",
        goal_text="Goal",
        status="idle",
        created_at="",
        updated_at="",
    )
    save_cycle(cycle, tmp_path)
    loaded = load_cycle(tmp_path)
    assert loaded is not None
    assert loaded.cycle_id == "cy_save"
    assert loaded.project_slug == "p1"


def test_propose_next_actions_no_plan(tmp_path: Path) -> None:
    """With no goal/plan, proposal can be planner_compile or empty depending on store."""
    proposed, blocked = propose_next_actions("default", tmp_path)
    # No plan and no current_goal -> we may get compile with empty goal or blocked
    assert blocked is None or (isinstance(blocked, BlockedCycleReason) and proposed == [])
    if proposed:
        assert len(proposed) >= 1
        assert proposed[0].action_type in ("planner_compile", "executor_run", "executor_resume")


def test_queue_enqueue_list_pending(tmp_path: Path) -> None:
    action = QueuedAction(
        action_id="a_1",
        label="Run job X",
        action_type="executor_run",
        plan_ref="job_1",
        plan_source="job",
        mode="simulate",
        why="Next step",
        risk_level="low",
        created_at="",
    )
    item = enqueue_proposal(action, "cy_1", tmp_path)
    assert item.queue_id.startswith("q_")
    assert item.status == "pending"
    pending = list_pending(tmp_path)
    assert len(pending) == 1
    assert pending[0].queue_id == item.queue_id
    assert get_item(item.queue_id, tmp_path) is not None


def test_queue_approve_reject_defer(tmp_path: Path) -> None:
    action = QueuedAction(
        action_id="a_2",
        label="Compile plan",
        action_type="planner_compile",
        why="No plan",
        risk_level="low",
        created_at="",
    )
    item = enqueue_proposal(action, "cy_2", tmp_path)
    qid = item.queue_id
    approved = approve(qid, "ok", tmp_path)
    assert approved is not None
    assert approved.status == "approved"
    pending = list_pending(tmp_path)
    assert len(pending) == 0
    items = load_queue(tmp_path)
    assert any(q.queue_id == qid and q.status == "approved" for q in items)

    action2 = QueuedAction(action_id="a_3", label="Run", action_type="executor_run", plan_ref="r1", plan_source="routine", mode="simulate", why="", risk_level="medium", created_at="")
    item2 = enqueue_proposal(action2, "cy_2", tmp_path)
    rejected = reject(item2.queue_id, "not now", tmp_path)
    assert rejected is not None
    assert rejected.status == "rejected"

    action3 = QueuedAction(action_id="a_4", label="Defer me", action_type="executor_run", plan_ref="j1", plan_source="job", mode="simulate", why="", risk_level="low", created_at="")
    item3 = enqueue_proposal(action3, "cy_2", tmp_path)
    deferred = defer(item3.queue_id, "later", tmp_path)
    assert deferred is not None
    assert deferred.status == "deferred"


def test_approve_nonexistent(tmp_path: Path) -> None:
    result = approve("q_nonexistent", "", tmp_path)
    assert result is None


def test_build_cycle_summary(tmp_path: Path) -> None:
    summary = build_cycle_summary(tmp_path)
    assert isinstance(summary, CycleSummary)
    assert summary.pending_queue_count >= 0
    assert summary.approved_count >= 0
    assert summary.rejected_count >= 0
    assert summary.deferred_count >= 0


def test_handoff_planner_compile(tmp_path: Path) -> None:
    """Execute approved planner_compile: compiles goal and saves plan."""
    from workflow_dataset.planner.store import save_current_goal, load_latest_plan
    save_current_goal("Test goal for handoff", tmp_path)
    action = QueuedAction(
        action_id="a_compile",
        label="Compile plan",
        action_type="planner_compile",
        mode="simulate",
        why="Test",
        risk_level="low",
        created_at="",
    )
    item = enqueue_proposal(action, "cy_h", tmp_path)
    approve(item.queue_id, "", tmp_path)
    from workflow_dataset.supervised_loop.handoff import execute_approved
    result = execute_approved(item.queue_id, tmp_path)
    assert "error" not in result or not result.get("error")
    assert result.get("status") == "completed"
    plan = load_latest_plan(tmp_path)
    assert plan is not None
    assert plan.goal_text == "Test goal for handoff"


def test_cycle_summary_after_handoff(tmp_path: Path) -> None:
    save_cycle(
        AgentCycle(cycle_id="cy_sum", project_slug="p", goal_text="G", status="completed", created_at="", updated_at="", last_handoff_id="h_1", last_run_id=""),
        tmp_path,
    )
    append_handoff(
        ExecutionHandoff(handoff_id="h_1", queue_id="q_1", cycle_id="cy_sum", action_type="planner_compile", status="completed", outcome_summary="plan_id=xyz", started_at="", ended_at=""),
        tmp_path,
    )
    summary = build_cycle_summary(tmp_path)
    assert summary.cycle_id == "cy_sum"
    assert summary.last_handoff_status == "completed"


def test_blocked_cycle_reason() -> None:
    r = BlockedCycleReason(reason="No executable step", detail="All steps blocked", step_index=0)
    assert r.reason == "No executable step"
    assert r.step_index == 0


# ----- M27H.1: Batched approvals, operator policies, prioritization, defer/revisit -----


def test_operator_policy_roundtrip(tmp_path: Path) -> None:
    policy = OperatorPolicy(
        batch_approve_max_risk="low",
        auto_queue_action_types=["planner_compile"],
        always_manual_review_action_types=["executor_resume"],
        always_manual_review_risk_levels=["high"],
        always_manual_review_modes=["real"],
        defer_revisit_max_days=7,
    )
    save_operator_policy(policy, tmp_path)
    loaded = load_operator_policy(tmp_path)
    assert loaded.batch_approve_max_risk == "low"
    assert "executor_resume" in loaded.always_manual_review_action_types
    assert loaded.requires_manual_review(QueuedAction(action_type="executor_resume", risk_level="low")) is True
    assert loaded.requires_manual_review(QueuedAction(action_type="planner_compile", risk_level="low")) is False
    assert loaded.risk_within_batch_limit("low") is True
    assert loaded.risk_within_batch_limit("high") is False


def test_list_pending_sorted(tmp_path: Path) -> None:
    """Manual-review and high-risk sort first; then by risk low first; then created_at."""
    policy = OperatorPolicy(always_manual_review_action_types=["executor_resume"])
    save_operator_policy(policy, tmp_path)
    low = QueuedAction(action_id="a_low", label="Low", action_type="planner_compile", risk_level="low", created_at="2025-01-01")
    high = QueuedAction(action_id="a_high", label="Resume", action_type="executor_resume", risk_level="medium", created_at="2025-01-02")
    enqueue_proposal(low, "cy", tmp_path)
    enqueue_proposal(high, "cy", tmp_path)
    sorted_list = list_pending_sorted(tmp_path, policy)
    assert len(sorted_list) == 2
    assert sorted_list[0].action.action_type == "executor_resume"
    assert sorted_list[1].action.action_type == "planner_compile"


def test_defer_with_reason_and_revisit(tmp_path: Path) -> None:
    action = QueuedAction(action_id="a_d", label="Defer", action_type="executor_run", risk_level="low", created_at="")
    item = enqueue_proposal(action, "cy", tmp_path)
    deferred = defer(item.queue_id, "later", tmp_path, defer_reason="wait for sign-off", revisit_after="2025-02-01")
    assert deferred is not None
    assert deferred.status == "deferred"
    assert deferred.defer_reason == "wait for sign-off"
    assert deferred.revisit_after == "2025-02-01"
    items = load_queue(tmp_path)
    found = next(q for q in items if q.queue_id == item.queue_id)
    assert found.defer_reason == "wait for sign-off"
    assert found.revisit_after == "2025-02-01"


def test_list_deferred_and_revisit(tmp_path: Path) -> None:
    action = QueuedAction(action_id="a_x", label="X", action_type="planner_compile", risk_level="low", created_at="")
    item = enqueue_proposal(action, "cy", tmp_path)
    defer(item.queue_id, "", tmp_path)
    deferred = list_deferred(tmp_path)
    assert len(deferred) == 1
    assert deferred[0].queue_id == item.queue_id
    back = revisit_deferred(item.queue_id, tmp_path)
    assert back is not None
    assert back.status == "pending"
    assert list_deferred(tmp_path) == []
    assert len(list_pending(tmp_path)) == 1


def test_approve_batch_low_risk_only(tmp_path: Path) -> None:
    """Batch approves only low-risk; skips manual-review and higher risk."""
    save_operator_policy(OperatorPolicy(batch_approve_max_risk="low", always_manual_review_action_types=["executor_resume"]), tmp_path)
    low1 = QueuedAction(action_id="a1", label="Low1", action_type="planner_compile", risk_level="low", created_at="")
    low2 = QueuedAction(action_id="a2", label="Low2", action_type="planner_compile", risk_level="low", created_at="")
    manual = QueuedAction(action_id="a3", label="Resume", action_type="executor_resume", risk_level="low", created_at="")
    enqueue_proposal(low1, "cy", tmp_path)
    enqueue_proposal(manual, "cy", tmp_path)
    enqueue_proposal(low2, "cy", tmp_path)
    result = approve_batch(max_risk="low", run_after=False, repo_root=tmp_path)
    assert result["approved_count"] == 2
    assert len(result["approved_ids"]) == 2
    assert result["approved_ids"][0] != result["approved_ids"][1]
    assert len(result["skipped_manual_review"]) == 1
    pending = list_pending(tmp_path)
    assert len(pending) == 1
    manual_item = next(q for q in load_queue(tmp_path) if q.action.action_type == "executor_resume")
    assert manual_item.status == "pending"
    approved = [q for q in load_queue(tmp_path) if q.status == "approved"]
    assert len(approved) == 2
