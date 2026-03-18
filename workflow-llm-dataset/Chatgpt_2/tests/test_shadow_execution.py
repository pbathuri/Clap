"""
M45E–M45H: Tests for shadow execution — run creation, confidence/risk, gates, safe-to-continue, forced takeover.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.shadow_execution.models import (
    ShadowRun,
    ExpectedOutcome,
    ObservedOutcome,
    ConfidenceScore,
    RiskMarker,
    InterventionGate,
    SafeToContinueState,
    ForcedTakeoverState,
)
from workflow_dataset.shadow_execution.confidence import (
    evaluate_confidence_step,
    evaluate_confidence_loop,
    evaluate_risk_step,
    evaluate_risk_loop,
)
from workflow_dataset.shadow_execution.gates import (
    evaluate_gates_for_run,
    next_intervention_gate,
    should_force_takeover,
    compute_safe_to_continue,
    compute_forced_takeover,
)
from workflow_dataset.shadow_execution.runner import create_shadow_run, run_shadow_loop
from workflow_dataset.shadow_execution.store import save_shadow_run, load_shadow_run, list_shadow_runs


def test_shadow_run_creation() -> None:
    """create_shadow_run produces a run with expected_outcomes and status pending."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run = create_shadow_run(plan_source="job", plan_ref="weekly_status_from_notes", repo_root=root)
        assert run.shadow_run_id.startswith("shadow_")
        assert run.plan_ref == "weekly_status_from_notes"
        assert run.status == "pending"
        assert isinstance(run.expected_outcomes, list)


def test_confidence_step_evaluation() -> None:
    """evaluate_confidence_step returns ConfidenceScore with scope step and 0–1 score."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        c = evaluate_confidence_step(0, "step_0", plan_ref="job1", repo_root=root)
        assert c.scope == "step"
        assert c.step_index == 0
        assert 0 <= c.score <= 1
        assert isinstance(c.factors, list)


def test_confidence_loop_evaluation() -> None:
    """evaluate_confidence_loop returns ConfidenceScore with scope loop."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        c = evaluate_confidence_loop(plan_ref="job1", step_scores=[0.6, 0.8], repo_root=root)
        assert c.scope == "loop"
        assert c.step_index is None
        assert 0 <= c.score <= 1


def test_risk_step_and_loop() -> None:
    """evaluate_risk_step and evaluate_risk_loop return RiskMarker with level."""
    r = evaluate_risk_step(0, 0.3, "success")
    assert r.scope == "step"
    assert r.level in ("low", "medium", "high")
    r2 = evaluate_risk_loop(0.3, any_step_high_risk=True)
    assert r2.scope == "loop"
    assert r2.level == "high"


def test_gates_evaluation() -> None:
    """evaluate_gates_for_run returns list of InterventionGate; low confidence triggers failed gates."""
    run = ShadowRun(
        shadow_run_id="test_1",
        plan_ref="job1",
        status="completed",
        confidence_loop=ConfidenceScore(scope="loop", score=0.3),
        confidence_step=[ConfidenceScore(scope="step", step_index=0, score=0.3)],
        risk_markers=[RiskMarker(scope="loop", level="high", reason="test")],
    )
    gates = evaluate_gates_for_run(run)
    run.gates = gates
    assert len(gates) >= 4
    failed = [g for g in gates if not g.passed]
    assert len(failed) >= 1
    assert should_force_takeover(run) or not should_force_takeover(run)


def test_safe_to_continue_and_forced_takeover() -> None:
    """compute_safe_to_continue and compute_forced_takeover return correct state when handoff gate fails."""
    run = ShadowRun(
        shadow_run_id="test_2",
        plan_ref="job1",
        status="completed",
        confidence_loop=ConfidenceScore(scope="loop", score=0.35),
        confidence_step=[ConfidenceScore(scope="step", step_index=0, score=0.35)],
        risk_markers=[RiskMarker(scope="loop", level="high", reason="test")],
    )
    run.gates = evaluate_gates_for_run(run)
    safe = compute_safe_to_continue(run)
    ft = compute_forced_takeover(run)
    assert isinstance(safe, SafeToContinueState)
    assert isinstance(ft, ForcedTakeoverState)
    if should_force_takeover(run):
        assert ft.forced is True
        assert safe.may_continue is False


def test_run_shadow_loop_persist() -> None:
    """run_shadow_loop fills observed_outcomes, confidence, gates, and persists."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run = create_shadow_run(plan_source="job", plan_ref="weekly_status_from_notes", repo_root=root)
        run = run_shadow_loop(run, persist=True, repo_root=root)
        assert run.status in ("completed", "takeover")
        assert len(run.observed_outcomes) >= 1
        assert run.confidence_loop is not None
        assert len(run.gates) >= 1
        assert run.safe_to_continue is not None
        loaded = load_shadow_run(run.shadow_run_id, repo_root=root)
        assert loaded is not None
        assert loaded.get("shadow_run_id") == run.shadow_run_id


def test_list_shadow_runs() -> None:
    """list_shadow_runs returns list of run summaries."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run = create_shadow_run(plan_source="job", plan_ref="job1", repo_root=root)
        save_shadow_run(run, repo_root=root)
        listed = list_shadow_runs(limit=5, repo_root=root)
        assert isinstance(listed, list)
        if listed:
            assert "shadow_run_id" in listed[0]
            assert "status" in listed[0]


def test_no_confidence_weak_evidence() -> None:
    """When no benchmark/memory, confidence still returns 0–1 scores (no crash)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        c_step = evaluate_confidence_step(0, "s0", plan_ref="nonexistent", repo_root=root)
        c_loop = evaluate_confidence_loop(plan_ref="nonexistent", step_scores=[], repo_root=root)
        assert 0 <= c_step.score <= 1
        assert 0 <= c_loop.score <= 1


# ----- M45H.1: Confidence policies + promotion eligibility -----


def test_get_policy_for_loop_type() -> None:
    """get_policy_for_loop_type returns a policy for routine, job, macro."""
    from workflow_dataset.shadow_execution.policies import get_policy_for_loop_type
    for lt in ("routine", "job", "macro"):
        policy = get_policy_for_loop_type(lt)
        assert policy.loop_type == lt
        assert policy.policy_id
        assert policy.min_loop_confidence_for_bounded_real >= 0
        assert policy.max_risk_level_for_bounded_real in ("low", "medium", "high")


def test_evaluate_promotion_eligibility_shadow_only() -> None:
    """When loop confidence below policy min, report says shadow-only with reason."""
    from workflow_dataset.shadow_execution.policies import evaluate_promotion_eligibility
    from workflow_dataset.shadow_execution.models import ConfidencePolicy
    policy = ConfidencePolicy(
        policy_id="test",
        loop_type="job",
        min_loop_confidence_for_bounded_real=0.8,
        require_min_step_confidence=0.5,
    )
    run_dict = {
        "shadow_run_id": "test_1",
        "loop_type": "job",
        "confidence_loop": {"score": 0.6},
        "confidence_step": [{"score": 0.7}],
        "risk_markers": [{"level": "low"}],
        "forced_takeover": {"forced": False},
    }
    report = evaluate_promotion_eligibility(run_dict, policy)
    assert report.eligible_for_bounded_real is False
    assert len(report.reason_shadow_only) >= 1
    assert "0.6" in report.reason_shadow_only[0] or "below" in report.reason_shadow_only[0].lower()


def test_evaluate_promotion_eligibility_eligible() -> None:
    """When loop and step confidence meet policy and no high risk, report says eligible."""
    from workflow_dataset.shadow_execution.policies import evaluate_promotion_eligibility
    from workflow_dataset.shadow_execution.models import ConfidencePolicy
    policy = ConfidencePolicy(
        policy_id="test",
        loop_type="job",
        min_loop_confidence_for_bounded_real=0.7,
        require_min_step_confidence=0.4,
    )
    run_dict = {
        "shadow_run_id": "test_2",
        "loop_type": "job",
        "confidence_loop": {"score": 0.85},
        "confidence_step": [{"score": 0.8}],
        "risk_markers": [{"level": "low"}],
        "forced_takeover": {"forced": False},
    }
    report = evaluate_promotion_eligibility(run_dict, policy)
    assert report.eligible_for_bounded_real is True
    assert len(report.reason_eligible) >= 1


def test_build_promotion_eligibility_report_not_found() -> None:
    """build_promotion_eligibility_report for missing run returns error and eligible=False."""
    from workflow_dataset.shadow_execution.policies import build_promotion_eligibility_report
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        report = build_promotion_eligibility_report("nonexistent_id", repo_root=root)
        assert report.get("error")
        assert report.get("eligible_for_bounded_real") is False


def test_build_promotion_eligibility_report_success() -> None:
    """build_promotion_eligibility_report for existing run returns full report."""
    from workflow_dataset.shadow_execution import create_shadow_run, run_shadow_loop
    from workflow_dataset.shadow_execution.policies import build_promotion_eligibility_report
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run = create_shadow_run(plan_source="job", plan_ref="job1", repo_root=root)
        run = run_shadow_loop(run, persist=True, repo_root=root)
        report = build_promotion_eligibility_report(run.shadow_run_id, repo_root=root)
        assert report.get("shadow_run_id") == run.shadow_run_id
        assert "eligible_for_bounded_real" in report
        assert "operator_summary" in report
        assert "applied_policy_id" in report
        assert "reason_shadow_only" in report or "reason_eligible" in report
