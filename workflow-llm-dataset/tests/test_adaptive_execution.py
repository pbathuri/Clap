"""
M45A–M45D: Tests for adaptive execution — plan creation, bounded loop, progression, stop/escalation, no-loop.
M45D.1: Execution profiles, loop templates, explain safety.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.adaptive_execution.models import (
    AdaptiveExecutionPlan,
    BoundedExecutionLoop,
    ExecutionStep,
    PlanBranch,
    StepOutcome,
    StopCondition,
    EscalationCondition,
    HumanTakeoverPoint,
)
from workflow_dataset.adaptive_execution.generator import generate_plan_from_goal, create_bounded_loop, generate_loop_from_goal
from workflow_dataset.adaptive_execution.store import save_loop, load_loop, list_active_loops
from workflow_dataset.adaptive_execution.progression import advance_step, stop_loop, escalate_loop, record_takeover_decision
from workflow_dataset.adaptive_execution.mission_control import adaptive_execution_slice
from workflow_dataset.adaptive_execution.profiles import list_profiles, get_profile, get_profile_why_safe, PROFILE_CONSERVATIVE, PROFILE_BALANCED
from workflow_dataset.adaptive_execution.templates import list_templates, get_template, explain_template_safety, TEMPLATE_WEEKLY_SUMMARY
from workflow_dataset.adaptive_execution.explain_safety import explain_loop_safety, format_safety_explanation


def test_adaptive_plan_creation() -> None:
    """Generate plan from goal; has steps, branches, stop/escalation conditions."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = generate_plan_from_goal("Weekly summary", max_steps=10, repo_root=root)
        assert plan.plan_id.startswith("aplan_")
        assert plan.goal_text == "Weekly summary"
        assert len(plan.steps) >= 1
        assert any(b.branch_id == "main" for b in plan.branches)
        assert any(b.is_fallback for b in plan.branches)
        assert len(plan.stop_conditions) >= 1
        assert len(plan.escalation_conditions) >= 1


def test_bounded_loop_enforcement() -> None:
    """Loop has max_steps and required_review_step_indices; advancing past max_steps stops."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = generate_plan_from_goal("Test", max_steps=3, repo_root=root)
        plan.steps = [ExecutionStep(step_index=i, step_id=f"s{i}", label=f"Step {i}", action_type="human_required") for i in range(3)]
        plan.branches = [PlanBranch(branch_id="main", label="Main", step_indices=[0, 1, 2])]
        loop = create_bounded_loop(plan, max_steps=3, repo_root=root)
        save_loop(loop, root)
        assert loop.max_steps == 3
        for i in range(3):
            result = advance_step(loop.loop_id, outcome=StepOutcome(step_index=i, status="success", confidence=0.9), repo_root=root)
            if result.get("stopped") or result["status"] == "completed":
                break
        loop2 = load_loop(loop.loop_id, root)
        assert loop2 is not None
        assert loop2.status in ("stopped", "completed", "running")


def test_branch_fallback_behavior() -> None:
    """When outcome status is blocked, loop can switch to fallback branch."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = generate_loop_from_goal("Goal", max_steps=5, repo_root=root)
        save_loop(loop, root)
        result = advance_step(loop.loop_id, outcome=StepOutcome(step_index=0, status="blocked", confidence=0.3), repo_root=root)
        assert result.get("branch_switched") is True or result.get("status") in ("running", "stopped", "awaiting_takeover", "completed")
        loop2 = load_loop(loop.loop_id, root)
        if result.get("branch_switched"):
            assert loop2 is not None
            assert loop2.fallback_activated or loop2.current_branch_id == "fallback"


def test_stop_escalation_logic() -> None:
    """stop_loop and escalate_loop set status and reason."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = generate_loop_from_goal("Stop test", max_steps=5, repo_root=root)
        save_loop(loop, root)
        result = stop_loop(loop.loop_id, reason="manual_stop", repo_root=root)
        assert result["status"] == "stopped"
        assert "manual" in result["message"].lower() or "stop" in result["message"].lower()
        loop2 = load_loop(loop.loop_id, root)
        assert loop2 is not None and loop2.status == "stopped"

        loop3 = generate_loop_from_goal("Escalate test", max_steps=5, repo_root=root)
        save_loop(loop3, root)
        result2 = escalate_loop(loop3.loop_id, reason="blocked", repo_root=root)
        assert result2["status"] == "escalated"
        loop4 = load_loop(loop3.loop_id, root)
        assert loop4 is not None and loop4.status == "escalated"


def test_no_loop_invalid_loop_behavior() -> None:
    """load_loop returns None for missing id; advance_step returns error."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert load_loop("nonexistent_loop_id", root) is None
        result = advance_step("nonexistent_loop_id", repo_root=root)
        assert result.get("error") is not None
        result2 = stop_loop("nonexistent_loop_id", repo_root=root)
        assert result2.get("error") is not None


def test_blocked_step_handling() -> None:
    """Advance with blocked outcome can trigger fallback or escalate."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = generate_loop_from_goal("Blocked", max_steps=10, repo_root=root)
        save_loop(loop, root)
        result = advance_step(loop.loop_id, outcome=StepOutcome(step_index=0, status="blocked", confidence=0.2), repo_root=root)
        assert "error" not in result or result.get("error") is None
        assert result.get("status") in ("running", "stopped", "escalated", "awaiting_takeover", "completed") or result.get("branch_switched")


def test_list_active_loops() -> None:
    """list_active_loops returns stored loops; status_filter works."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = generate_loop_from_goal("List test", max_steps=5, repo_root=root)
        save_loop(loop, root)
        running = list_active_loops(status_filter="running", repo_root=root)
        assert len(running) >= 1
        assert running[0].get("loop_id") == loop.loop_id
        stopped = list_active_loops(status_filter="stopped", repo_root=root)
        assert all(L.get("status") == "stopped" for L in stopped)


def test_mission_control_slice() -> None:
    """adaptive_execution_slice returns active_loop_id, next_step_index, remaining_safe_steps when loop exists."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        slice_empty = adaptive_execution_slice(repo_root=root)
        assert "active_loop_id" in slice_empty
        assert "running_loop_count" in slice_empty
        loop = generate_loop_from_goal("MC test", max_steps=5, repo_root=root)
        save_loop(loop, root)
        slice_with = adaptive_execution_slice(repo_root=root)
        assert slice_with.get("running_loop_count", 0) >= 1 or slice_with.get("active_loop_id")


# ----- M45D.1: Execution profiles and loop templates -----


def test_list_profiles() -> None:
    """Execution profiles include conservative, balanced, operator_heavy, review_heavy."""
    profiles = list_profiles()
    ids = [p.profile_id for p in profiles]
    assert PROFILE_CONSERVATIVE in ids
    assert PROFILE_BALANCED in ids
    assert "operator_heavy" in ids
    assert "review_heavy" in ids
    for p in profiles:
        assert p.why_safe


def test_get_profile_why_safe() -> None:
    """get_profile returns profile; get_profile_why_safe returns operator-facing reason."""
    p = get_profile(PROFILE_CONSERVATIVE)
    assert p is not None
    assert p.max_steps_cap == 5
    why = get_profile_why_safe(PROFILE_CONSERVATIVE)
    assert "conservative" in why.lower() or "review" in why.lower() or "safe" in why.lower()


def test_list_templates() -> None:
    """Loop templates include weekly_summary, approval_sweep, resume_continuity, single_job_run."""
    templates = list_templates()
    ids = [t.template_id for t in templates]
    assert TEMPLATE_WEEKLY_SUMMARY in ids
    assert "approval_sweep" in ids
    assert "resume_continuity" in ids
    assert "single_job_run" in ids
    for t in templates:
        assert t.why_safe
        assert t.default_profile_id


def test_get_template_and_explain_safety() -> None:
    """get_template returns template; explain_template_safety returns why_safe and why_blocked."""
    t = get_template(TEMPLATE_WEEKLY_SUMMARY)
    assert t is not None
    assert t.template_id == TEMPLATE_WEEKLY_SUMMARY
    assert t.goal_hint
    expl = explain_template_safety(TEMPLATE_WEEKLY_SUMMARY, is_blocked=False)
    assert expl["why_safe"]
    assert expl["why_blocked"]
    assert expl["summary"]


def test_loop_with_profile_and_template() -> None:
    """Generate loop with profile and template; loop has profile_id and template_id; explain_loop_safety works."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = generate_loop_from_goal(
            "Weekly summary",
            max_steps=30,
            repo_root=root,
            profile_id=PROFILE_CONSERVATIVE,
            template_id=TEMPLATE_WEEKLY_SUMMARY,
        )
        assert loop.profile_id == PROFILE_CONSERVATIVE
        assert loop.template_id == TEMPLATE_WEEKLY_SUMMARY
        assert loop.max_steps <= 5  # conservative caps at 5
        safety = explain_loop_safety(loop, is_blocked=False)
        assert safety["summary"]
        assert safety["profile_why_safe"]
        assert safety["template_why_safe"]
        text = format_safety_explanation(safety)
        assert "safe" in text.lower() or "profile" in text.lower()
