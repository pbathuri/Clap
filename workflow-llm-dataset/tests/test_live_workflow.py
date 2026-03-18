"""
M33E–M33H: Supervised real-time workflow — models, step generation, escalation, state, handoff.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.live_workflow.models import (
    SupervisedLiveWorkflow,
    LiveStepSuggestion,
    EscalationTier,
    WorkflowRunState,
    BlockedRealTimeStep,
    ExpectedHandoff,
)
from workflow_dataset.live_workflow.step_generator import generate_live_workflow_steps
from workflow_dataset.live_workflow.escalation import (
    get_escalation_tiers,
    next_escalation_tier,
    build_handoff_for_tier,
)
from workflow_dataset.live_workflow.state import get_live_workflow_run, save_live_workflow_run


def test_escalation_tiers_order():
    """Escalation tiers are ordered hint → … → review."""
    tiers = get_escalation_tiers()
    assert tiers[0] == EscalationTier.HINT_ONLY
    assert EscalationTier.REVIEW_APPROVAL_ROUTING in tiers
    assert tiers.index(EscalationTier.ACTION_CARD_SUGGESTION) < tiers.index(EscalationTier.PLANNER_GOAL_PREFILL)


def test_next_escalation_tier():
    """Next tier advances; at top returns None."""
    assert next_escalation_tier(EscalationTier.HINT_ONLY) == EscalationTier.ACTION_CARD_SUGGESTION
    assert next_escalation_tier(EscalationTier.ACTION_CARD_SUGGESTION) == EscalationTier.DRAFT_HANDOFF_PREP
    assert next_escalation_tier(EscalationTier.REVIEW_APPROVAL_ROUTING) is None


def test_build_handoff_for_tier():
    """Handoff params are aligned with HandoffTarget (string) and have expected keys."""
    step = LiveStepSuggestion(
        step_index=0,
        label="Run report",
        hint_text="Run the weekly report job",
        escalation_tier=EscalationTier.HINT_ONLY,
    )
    run = SupervisedLiveWorkflow(
        run_id="lwr_test",
        goal_text="Weekly report",
        plan_ref="weekly_report",
        plan_source="job",
        steps=[step],
        current_step_index=0,
        state=WorkflowRunState.ACTIVE,
    )
    h = build_handoff_for_tier(EscalationTier.HINT_ONLY, step, run)
    assert "handoff_params" in h
    assert h.get("handoff_params", {}).get("hint") == "Run the weekly report job"

    h2 = build_handoff_for_tier(EscalationTier.PLANNER_GOAL_PREFILL, step, run)
    assert h2.get("handoff_target") == "compile_plan"
    assert "goal" in h2.get("handoff_params", {})

    h3 = build_handoff_for_tier(EscalationTier.REVIEW_APPROVAL_ROUTING, step, run)
    assert h3.get("handoff_target") == "approval_studio"


def test_generate_live_workflow_no_goal():
    """No goal -> no_workflow state, empty steps."""
    run = generate_live_workflow_steps(goal_text="", repo_root=Path("/nonexistent"))
    assert run.state == WorkflowRunState.NO_WORKFLOW
    assert len(run.steps) == 0
    assert run.run_id


def test_generate_live_workflow_with_goal(tmp_path):
    """With goal, planner is invoked; we get steps or no_match reasoning step."""
    run = generate_live_workflow_steps(goal_text="Unknown goal xyz no match", repo_root=tmp_path)
    # No jobs/routines under tmp_path -> planner returns reasoning step or empty
    assert run.run_id
    assert run.goal_text == "Unknown goal xyz no match"
    # Either no steps (no_workflow if compile fails) or at least one (reasoning or job step)
    if run.state != WorkflowRunState.NO_WORKFLOW:
        assert len(run.steps) >= 0
        if run.steps:
            assert run.steps[0].escalation_tier == EscalationTier.HINT_ONLY


def test_supervised_live_workflow_to_dict():
    """SupervisedLiveWorkflow.to_dict() serializes state and escalation as string values."""
    run = SupervisedLiveWorkflow(
        run_id="lwr_1",
        goal_text="Test",
        state=WorkflowRunState.ACTIVE,
        current_escalation_tier=EscalationTier.HINT_ONLY,
    )
    d = run.to_dict()
    assert d["state"] == "active"
    assert d["current_escalation_tier"] == "hint_only"


def test_blocked_step_handoff():
    """Blocked step has handoff_suggestion for planner/approval."""
    blocked = BlockedRealTimeStep(
        step_index=0,
        label="Blocked job",
        blocked_reason="Policy blocks this step",
        handoff_suggestion="Open planner or approval studio to resolve.",
        run_id="lwr_b",
    )
    run = SupervisedLiveWorkflow(
        run_id="lwr_b",
        goal_text="Blocked goal",
        steps=[],
        state=WorkflowRunState.BLOCKED,
        blocked_step=blocked,
    )
    assert run.blocked_step and run.blocked_step.blocked_reason == "Policy blocks this step"
    assert "planner" in run.blocked_step.handoff_suggestion.lower() or "approval" in run.blocked_step.handoff_suggestion.lower()


def test_state_save_load(tmp_path):
    """Save and load live workflow run."""
    run = SupervisedLiveWorkflow(
        run_id="lwr_save",
        goal_text="Save test",
        plan_ref="p1",
        steps=[
            LiveStepSuggestion(step_index=0, label="Step 1", escalation_tier=EscalationTier.HINT_ONLY),
        ],
        current_step_index=0,
        next_step_index=None,
        state=WorkflowRunState.ACTIVE,
    )
    save_live_workflow_run(run, repo_root=tmp_path)
    loaded = get_live_workflow_run(repo_root=tmp_path)
    assert loaded is not None
    assert loaded.run_id == run.run_id
    assert loaded.goal_text == run.goal_text
    assert len(loaded.steps) == 1
    assert loaded.steps[0].label == "Step 1"
    assert loaded.state == WorkflowRunState.ACTIVE


def test_empty_no_workflow_behavior():
    """No run saved -> get_live_workflow_run returns None."""
    loaded = get_live_workflow_run(repo_root=Path("/nonexistent_sentinel_path_12345"))
    assert loaded is None


def test_safe_handoff_targets_explicit():
    """Escalation handoffs use explicit targets (compile_plan, queue_simulated, approval_studio)."""
    step = LiveStepSuggestion(step_index=0, label="S", escalation_tier=EscalationTier.HINT_ONLY)
    run = SupervisedLiveWorkflow(run_id="r", goal_text="G", plan_ref="P", steps=[step], state=WorkflowRunState.ACTIVE)
    for tier in (EscalationTier.PLANNER_GOAL_PREFILL, EscalationTier.SIMULATED_EXECUTION_HANDOFF, EscalationTier.REVIEW_APPROVAL_ROUTING):
        h = build_handoff_for_tier(tier, step, run)
        assert "handoff_target" in h
        assert h["handoff_target"] in ("", "compile_plan", "queue_simulated", "approval_studio", "prefill_command", "create_draft")


# ----- M33H.1 Workflow bundles, stall recovery, escalation explanation -----


def test_workflow_bundle_model():
    """WorkflowBundle has expected fields."""
    from workflow_dataset.live_workflow.models import WorkflowBundle
    b = WorkflowBundle(
        bundle_id="test_bundle",
        label="Test",
        goal_template="Weekly report",
        alternate_goals=["Status", "Update"],
        recovery_suggestions=["Run planner compile"],
    )
    assert b.bundle_id == "test_bundle"
    assert len(b.alternate_goals) == 2
    assert len(b.recovery_suggestions) == 1


def test_bundles_save_and_list(tmp_path):
    """Save a bundle and list bundle ids."""
    from workflow_dataset.live_workflow.models import WorkflowBundle
    from workflow_dataset.live_workflow.bundles import save_bundle, list_bundle_ids, get_bundle
    b = WorkflowBundle(bundle_id="tmp_bundle", label="Tmp", goal_template="Tmp goal", alternate_goals=["Alt"])
    path = save_bundle(b, repo_root=tmp_path)
    assert path.exists()
    ids = list_bundle_ids(repo_root=tmp_path)
    assert "tmp_bundle" in ids
    loaded = get_bundle("tmp_bundle", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.label == "Tmp"
    assert loaded.alternate_goals == ["Alt"]


def test_stall_detection_not_stalled():
    """When idle time is below threshold, stalled is False."""
    from workflow_dataset.live_workflow.stall import detect_stall
    from workflow_dataset.utils.dates import utc_now_iso
    run = SupervisedLiveWorkflow(
        run_id="r",
        goal_text="G",
        steps=[LiveStepSuggestion(step_index=0, label="S")],
        state=WorkflowRunState.ACTIVE,
        updated_utc=utc_now_iso(),
    )
    result = detect_stall(run, idle_threshold_seconds=3600.0)
    assert result.stalled is False
    assert "No stall" in result.reason or result.reason == "No stall detected."


def test_stall_detection_stalled():
    """When idle time exceeds threshold, stalled is True and recovery paths are suggested."""
    from workflow_dataset.live_workflow.stall import detect_stall
    run = SupervisedLiveWorkflow(
        run_id="r",
        goal_text="G",
        steps=[LiveStepSuggestion(step_index=0, label="Step one")],
        state=WorkflowRunState.ACTIVE,
        updated_utc="2020-01-01T00:00:00Z",
        created_utc="2020-01-01T00:00:00Z",
    )
    result = detect_stall(run, idle_threshold_seconds=60.0, now_utc="2020-01-01T00:15:00Z")
    assert result.stalled is True
    assert result.idle_seconds >= 60.0
    assert len(result.suggested_recovery_paths) >= 1


def test_escalation_explanation():
    """Escalation explanation returns operator message and suggested action."""
    from workflow_dataset.live_workflow.escalation import explain_escalation
    expl = explain_escalation(
        EscalationTier.HINT_ONLY,
        EscalationTier.ACTION_CARD_SUGGESTION,
        reason_code="user_requested",
        step_label="Run report",
    )
    assert expl.from_tier == "hint_only"
    assert expl.to_tier == "action_card_suggestion"
    assert expl.reason_code == "user_requested"
    assert len(expl.operator_message) > 0
    assert len(expl.suggested_action) > 0


def test_generate_with_bundle_id(tmp_path):
    """Generate run from bundle_id uses bundle goal_template and alternate_path_recommendations."""
    from workflow_dataset.live_workflow.models import WorkflowBundle
    from workflow_dataset.live_workflow.bundles import save_bundle
    b = WorkflowBundle(
        bundle_id="test_goal_bundle",
        label="Test goal",
        goal_template="Unknown goal from bundle xyz",
        alternate_goals=["Alt A", "Alt B"],
    )
    save_bundle(b, repo_root=tmp_path)
    run = generate_live_workflow_steps(bundle_id="test_goal_bundle", repo_root=tmp_path)
    assert run.run_id
    assert run.bundle_id == "test_goal_bundle"
    assert run.goal_text == "Unknown goal from bundle xyz"
    assert len(run.alternate_path_recommendations) >= 2
    assert any("Alt" in str(a.get("label", "")) for a in run.alternate_path_recommendations)
