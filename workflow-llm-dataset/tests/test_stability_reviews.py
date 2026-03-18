"""
M46I–M46L: Sustained deployment reviews — decision-pack generation, evidence bundle, decision outcomes, history.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.stability_reviews.models import (
    StabilityDecision,
    StabilityWindow,
    EvidenceBundle,
    StabilityDecisionPack,
    ContinueRecommendation,
    NarrowRecommendation,
    RepairRecommendation,
    PauseRecommendation,
    RollbackRecommendation,
    SustainedDeploymentReview,
)
from workflow_dataset.stability_reviews.pack_builder import build_stability_decision_pack
from workflow_dataset.stability_reviews.decisions import build_decision_output, explain_stability_decision
from workflow_dataset.stability_reviews.store import (
    save_review,
    load_latest_review,
    list_reviews,
    get_review_by_id,
)


def test_stability_window_to_dict():
    w = StabilityWindow(kind="rolling_7", start_iso="2025-01-01T00:00:00Z", end_iso="2025-01-08T00:00:00Z", label="Last 7 days")
    d = w.to_dict()
    assert d["kind"] == "rolling_7"
    assert d["start_iso"] == "2025-01-01T00:00:00Z"
    assert d["label"] == "Last 7 days"


def test_evidence_bundle_to_dict():
    e = EvidenceBundle(
        health_summary="Blockers: 0. Warnings: 1.",
        drift_signals=["Degraded state."],
        support_triage_burden="Open issues: 2.",
    )
    d = e.to_dict()
    assert "Blockers" in d["health_summary"]
    assert d["drift_signals"] == ["Degraded state."]
    assert "Open issues" in d["support_triage_burden"]


def test_continue_recommendation_to_dict():
    r = ContinueRecommendation(
        decision=StabilityDecision.CONTINUE_WITH_WATCH.value,
        rationale="Evidence weak; watch.",
        evidence_refs=["evidence_bundle"],
        confidence="low",
    )
    d = r.to_dict()
    assert d["decision"] == "continue_with_watch"
    assert d["confidence"] == "low"


def test_decision_pack_to_dict():
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.CONTINUE.value,
        rationale="All clear.",
        evidence_refs=["launch_decision_pack"],
        evidence_bundle=EvidenceBundle(health_summary="OK"),
        generated_at_iso="2025-01-01T12:00:00Z",
        vertical_id="test",
    )
    d = pack.to_dict()
    assert d["recommended_decision"] == "continue"
    assert d["evidence_bundle"]["health_summary"] == "OK"
    assert d["vertical_id"] == "test"


def test_build_decision_output_continue():
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.CONTINUE.value,
        rationale="No blockers.",
        evidence_refs=["evidence_bundle"],
        continue_rec=ContinueRecommendation(
            decision=StabilityDecision.CONTINUE.value,
            rationale="No blockers; continue as-is.",
            evidence_refs=["evidence_bundle"],
            confidence="medium",
        ),
        generated_at_iso="2025-01-01T12:00:00Z",
    )
    out = build_decision_output(pack)
    assert out["decision"] == "continue"
    assert out["label"] == "Continue as-is"
    assert "rationale" in out
    assert "evidence_links" in out
    assert "recommended_actions" in out
    assert len(out["recommended_actions"]) >= 1


def test_build_decision_output_narrow():
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.NARROW.value,
        rationale="High-severity issues.",
        narrow_rec=NarrowRecommendation(
            rationale="Narrow scope until triaged.",
            evidence_refs=["post_deployment_guidance"],
            suggested_scope_note="Current cohort only.",
        ),
        generated_at_iso="2025-01-01T12:00:00Z",
    )
    out = build_decision_output(pack)
    assert out["decision"] == "narrow"
    assert out["label"] == "Narrow supported scope"
    assert "Current cohort only" in out["recommended_actions"][0]


def test_build_decision_output_repair():
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.REPAIR.value,
        rationale="Blockers present.",
        repair_rec=RepairRecommendation(
            rationale="Run repair bundle.",
            evidence_refs=["launch_decision_pack"],
            repair_bundle_ref="workflow-dataset launch-decision pack",
        ),
        generated_at_iso="2025-01-01T12:00:00Z",
    )
    out = build_decision_output(pack)
    assert out["decision"] == "repair"
    assert out["label"] == "Run repair bundle"
    assert "launch-decision" in out["recommended_actions"][0]


def test_build_decision_output_pause():
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.PAUSE.value,
        rationale="Launch decision is pause.",
        pause_rec=PauseRecommendation(
            rationale="Blockers; pause.",
            evidence_refs=["launch_decision_pack"],
            resume_condition="Resolve blockers and re-run stability-reviews generate.",
        ),
        generated_at_iso="2025-01-01T12:00:00Z",
    )
    out = build_decision_output(pack)
    assert out["decision"] == "pause"
    assert out["label"] == "Pause deployment"
    assert "Resolve blockers" in " ".join(out["recommended_actions"])


def test_build_decision_output_rollback():
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.ROLLBACK.value,
        rationale="Guidance=rollback.",
        rollback_rec=RollbackRecommendation(
            rationale="Cohort health recommends downgrade.",
            evidence_refs=["post_deployment_guidance"],
            prior_stable_ref="review-2025-01-01",
        ),
        generated_at_iso="2025-01-01T12:00:00Z",
    )
    out = build_decision_output(pack)
    assert out["decision"] == "rollback"
    assert out["label"] == "Rollback to prior stable state"
    assert "review-2025-01-01" in out["recommended_actions"][0]


def test_decision_output_unknown_fallback():
    pack = StabilityDecisionPack(
        recommended_decision="unknown",
        rationale="Fallback.",
        generated_at_iso="2025-01-01T12:00:00Z",
    )
    out = build_decision_output(pack)
    assert out["decision"] == "unknown"
    assert out["label"] == "Unknown"
    assert "stability-decision explain" in out["recommended_actions"][0]


def test_explain_stability_decision_with_pack():
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.CONTINUE.value,
        rationale="All clear.",
        evidence_refs=["evidence_bundle"],
        generated_at_iso="2025-01-01T12:00:00Z",
    )
    text = explain_stability_decision(pack=pack)
    assert "continue" in text.lower()
    assert "Rationale" in text
    assert "Recommended actions" in text


def test_pack_generation_returns_pack(tmp_path):
    """build_stability_decision_pack returns a StabilityDecisionPack with evidence and decision."""
    pack = build_stability_decision_pack(tmp_path, window_kind="rolling_7")
    assert isinstance(pack, StabilityDecisionPack)
    assert pack.recommended_decision in (
        StabilityDecision.CONTINUE.value,
        StabilityDecision.CONTINUE_WITH_WATCH.value,
        StabilityDecision.NARROW.value,
        StabilityDecision.REPAIR.value,
        StabilityDecision.PAUSE.value,
        StabilityDecision.ROLLBACK.value,
    )
    assert pack.rationale
    assert pack.generated_at_iso
    assert pack.stability_window is not None
    assert pack.stability_window.kind in ("rolling_7", "daily", "weekly", "rolling_30")
    assert pack.evidence_bundle is not None
    assert isinstance(pack.evidence_bundle, EvidenceBundle)


def test_evidence_bundle_composition(tmp_path):
    """Pack evidence bundle is composed from health, posture, and raw_snapshot."""
    pack = build_stability_decision_pack(tmp_path, window_kind="daily")
    assert pack.evidence_bundle is not None
    eb = pack.evidence_bundle
    assert hasattr(eb, "health_summary")
    assert hasattr(eb, "drift_signals")
    assert hasattr(eb, "support_triage_burden")
    assert hasattr(eb, "raw_snapshot")
    assert isinstance(eb.raw_snapshot, dict)
    # raw_snapshot should contain at least launch/guidance keys when no error
    if "error" not in str(eb.raw_snapshot):
        assert "launch_recommended_decision" in eb.raw_snapshot or "guidance" in eb.raw_snapshot


def test_no_review_weak_evidence_valid_decision(tmp_path):
    """Pack generation yields a valid stability decision (continue / watch / narrow / repair / pause / rollback)."""
    pack = build_stability_decision_pack(tmp_path, window_kind="rolling_7")
    valid = {e.value for e in StabilityDecision}
    assert pack.recommended_decision in valid, f"got {pack.recommended_decision}"


def test_store_save_and_load_latest(tmp_path):
    """save_review and load_latest_review round-trip."""
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.CONTINUE.value,
        rationale="Test.",
        evidence_refs=[],
        generated_at_iso="2025-01-01T12:00:00Z",
        stability_window=StabilityWindow(kind="rolling_7", label="Last 7 days"),
    )
    review = SustainedDeploymentReview(
        review_id="test-review-1",
        at_iso="2025-01-01T12:00:00Z",
        stability_window=pack.stability_window,
        decision_pack=pack,
        next_scheduled_review_iso="2025-01-08T00:00:00Z",
    )
    save_review(review, tmp_path)
    latest = load_latest_review(tmp_path)
    assert latest is not None
    assert latest.get("review_id") == "test-review-1"
    assert latest.get("decision_pack", {}).get("recommended_decision") == "continue"


def test_list_reviews_newest_first(tmp_path):
    """list_reviews returns newest first."""
    w = StabilityWindow(kind="rolling_7", label="Last 7 days")
    for i in range(3):
        pack = StabilityDecisionPack(
            recommended_decision=StabilityDecision.CONTINUE.value,
            rationale=f"Review {i}",
            generated_at_iso=f"2025-01-0{i+1}T12:00:00Z",
            stability_window=w,
        )
        review = SustainedDeploymentReview(
            review_id=f"review-{i}",
            at_iso=f"2025-01-0{i+1}T12:00:00Z",
            stability_window=w,
            decision_pack=pack,
        )
        save_review(review, tmp_path)
    reviews = list_reviews(tmp_path, limit=10)
    assert len(reviews) == 3
    assert reviews[0]["review_id"] == "review-2"
    assert reviews[2]["review_id"] == "review-0"


def test_get_review_by_id(tmp_path):
    """get_review_by_id returns the matching review."""
    w = StabilityWindow(kind="rolling_7", label="Last 7 days")
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.REPAIR.value,
        rationale="Repair test.",
        generated_at_iso="2025-01-01T12:00:00Z",
        stability_window=w,
    )
    review = SustainedDeploymentReview(
        review_id="find-me",
        at_iso="2025-01-01T12:00:00Z",
        stability_window=w,
        decision_pack=pack,
    )
    save_review(review, tmp_path)
    found = get_review_by_id("find-me", tmp_path)
    assert found is not None
    assert found["review_id"] == "find-me"
    assert found["decision_pack"]["recommended_decision"] == "repair"
    assert get_review_by_id("nonexistent", tmp_path) is None


def test_contradictory_evidence_handling():
    """Decision output still has rationale and evidence_links when pack has multiple recommendation types."""
    pack = StabilityDecisionPack(
        recommended_decision=StabilityDecision.REPAIR.value,
        rationale="Repair wins over continue due to blockers.",
        evidence_refs=["launch_decision_pack", "post_deployment_guidance"],
        repair_rec=RepairRecommendation(
            rationale="Blockers present.",
            evidence_refs=["launch_decision_pack"],
            repair_bundle_ref="workflow-dataset launch-decision pack",
        ),
        continue_rec=ContinueRecommendation(
            decision=StabilityDecision.CONTINUE.value,
            rationale="Would continue if no blockers.",
            evidence_refs=[],
            confidence="low",
        ),
        generated_at_iso="2025-01-01T12:00:00Z",
    )
    out = build_decision_output(pack)
    assert out["decision"] == "repair"
    assert "evidence_links" in out
    assert "rationale" in out


# ----- M46L.1 Review cadences -----


def test_default_cadences():
    from workflow_dataset.stability_reviews.cadences import get_default_cadences, get_cadence_for
    cadences = get_default_cadences()
    assert len(cadences) >= 3
    ids = [c.cadence_id for c in cadences]
    assert "daily" in ids
    assert "weekly" in ids
    assert "rolling_stability" in ids
    assert get_cadence_for("daily").window_kind == "daily"
    assert get_cadence_for("rolling_stability").window_kind == "rolling_7"
    assert get_cadence_for("nonexistent") is None


def test_next_review_due_iso():
    from workflow_dataset.stability_reviews.cadences import get_cadence_for, next_review_due_iso
    cadence = get_cadence_for("weekly")
    assert cadence is not None
    due = next_review_due_iso(cadence, last_review_at_iso="2025-01-01T12:00:00Z")
    assert "2025-01-08" in due
    due_default = next_review_due_iso(cadence, last_review_at_iso=None)
    assert due_default


def test_load_save_active_cadence(tmp_path):
    from workflow_dataset.stability_reviews.cadences import (
        load_active_cadence,
        save_active_cadence,
        get_cadence_for,
    )
    path = save_active_cadence("daily", tmp_path)
    assert path.exists()
    active = load_active_cadence(tmp_path)
    assert active.cadence_id == "daily"
    save_active_cadence("rolling_stability", tmp_path)
    active2 = load_active_cadence(tmp_path)
    assert active2.cadence_id == "rolling_stability"


# ----- M46L.1 Rollback policy -----


def test_rollback_policy_evaluate():
    from workflow_dataset.stability_reviews.rollback_policy import (
        get_default_rollback_policy,
        evaluate_rollback_policy,
    )
    policy = get_default_rollback_policy()
    should, reason = evaluate_rollback_policy(policy, "rollback", False, 0, 0)
    assert should is True
    assert "rollback" in reason.lower() or "guidance" in reason.lower()
    should2, _ = evaluate_rollback_policy(policy, "continue", True, 0, 0)
    assert should2 is True
    should3, _ = evaluate_rollback_policy(policy, "continue", False, 0, 0)
    assert should3 is False


def test_resolve_prior_stable_ref():
    from workflow_dataset.stability_reviews.rollback_policy import (
        get_default_rollback_policy,
        resolve_prior_stable_ref,
    )
    policy = get_default_rollback_policy()
    reviews = [
        {"review_id": "r3", "decision_pack": {"recommended_decision": "pause"}},
        {"review_id": "r2", "decision_pack": {"recommended_decision": "continue"}},
        {"review_id": "r1", "decision_pack": {"recommended_decision": "repair"}},
    ]
    ref = resolve_prior_stable_ref(policy, reviews)
    assert ref == "r2"


def test_load_save_rollback_policy(tmp_path):
    from workflow_dataset.stability_reviews.rollback_policy import (
        load_rollback_policy,
        save_rollback_policy,
        get_default_rollback_policy,
    )
    policy = get_default_rollback_policy()
    path = save_rollback_policy(policy, tmp_path)
    assert path.exists()
    loaded = load_rollback_policy(tmp_path)
    assert loaded.policy_id == policy.policy_id
    assert loaded.prior_stable_ref_rule == policy.prior_stable_ref_rule


# ----- M46L.1 Thresholds -----


def test_apply_thresholds_continue_as_is():
    from workflow_dataset.stability_reviews.thresholds import get_default_thresholds, apply_thresholds
    th = get_default_thresholds()
    out = apply_thresholds(
        th,
        blocker_count=0,
        warning_count=0,
        failed_gates_count=0,
        triage_issues=0,
        checkpoint_criteria_met=True,
        health_summary_has_signals=True,
    )
    assert out["band"] == "continue_as_is"
    assert out.get("overrides_continue")


def test_apply_thresholds_watch():
    from workflow_dataset.stability_reviews.thresholds import get_default_thresholds, apply_thresholds
    th = get_default_thresholds()
    out = apply_thresholds(
        th,
        blocker_count=0,
        warning_count=1,
        failed_gates_count=0,
        triage_issues=0,
        checkpoint_criteria_met=True,
        health_summary_has_signals=True,
    )
    assert out["band"] == "continue_with_watch"
    assert out.get("overrides_watch")


def test_apply_thresholds_narrow():
    from workflow_dataset.stability_reviews.thresholds import get_default_thresholds, apply_thresholds
    th = get_default_thresholds()
    out = apply_thresholds(
        th,
        blocker_count=0,
        warning_count=0,
        failed_gates_count=0,
        triage_issues=2,
        checkpoint_criteria_met=True,
        health_summary_has_signals=True,
    )
    assert out["band"] == "narrow"
    assert out.get("overrides_narrow")


def test_apply_thresholds_pause():
    from workflow_dataset.stability_reviews.thresholds import get_default_thresholds, apply_thresholds
    th = get_default_thresholds()
    out = apply_thresholds(
        th,
        blocker_count=1,
        warning_count=0,
        failed_gates_count=0,
        triage_issues=0,
        checkpoint_criteria_met=True,
        health_summary_has_signals=True,
    )
    assert out["band"] == "pause"
    assert out.get("overrides_pause")


def test_load_save_thresholds(tmp_path):
    from workflow_dataset.stability_reviews.thresholds import (
        load_thresholds,
        save_thresholds,
        get_default_thresholds,
    )
    th = get_default_thresholds()
    path = save_thresholds(th, tmp_path)
    assert path.exists()
    loaded = load_thresholds(tmp_path)
    assert loaded.thresholds_id == th.thresholds_id
    assert loaded.min_blockers_pause == th.min_blockers_pause
