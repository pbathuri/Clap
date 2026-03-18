"""
M50I–M50L: Tests for stable-v1 gate — evidence, gate evaluation, decision, report.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.stable_v1_gate.models import (
    StableV1Recommendation,
    GateBlocker,
    GateWarning,
    FinalEvidenceBundle,
    StableV1ReadinessGate,
    ConfidenceSummary,
    StableV1Decision,
    StableV1Report,
)
from workflow_dataset.stable_v1_gate.evidence import build_final_evidence_bundle
from workflow_dataset.stable_v1_gate.gate import evaluate_stable_v1_gate
from workflow_dataset.stable_v1_gate.decision import build_stable_v1_decision
from workflow_dataset.stable_v1_gate.report import build_stable_v1_report, explain_stable_v1_decision
from workflow_dataset.stable_v1_gate.mission_control import get_stable_v1_gate_state
from workflow_dataset.stable_v1_gate.watch_state import build_post_v1_watch_state_summary
from workflow_dataset.stable_v1_gate.carry_forward import build_roadmap_carry_forward_pack
from workflow_dataset.stable_v1_gate.models import (
    PostV1WatchStateSummary,
    RoadmapCarryForwardItem,
    RoadmapCarryForwardPack,
)


def test_gate_blocker_to_dict() -> None:
    b = GateBlocker(id="b1", summary="Test blocker", source="test", remediation_hint="Fix it")
    d = b.to_dict()
    assert d["id"] == "b1"
    assert d["summary"] == "Test blocker"
    assert d["severity"] == "blocker"


def test_gate_warning_to_dict() -> None:
    w = GateWarning(id="w1", summary="Test warning", source="test")
    d = w.to_dict()
    assert d["id"] == "w1"
    assert d["summary"] == "Test warning"


def test_final_evidence_bundle_to_dict() -> None:
    e = FinalEvidenceBundle(
        v1_contract_summary="Scope frozen.",
        production_cut_frozen=True,
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    d = e.to_dict()
    assert d["production_cut_frozen"] is True
    assert d["release_readiness_status"] == "ready"
    assert d["launch_recommended_decision"] == "launch"


def test_stable_v1_readiness_gate_passed() -> None:
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[], summary="OK")
    assert gate.passed is True
    d = gate.to_dict()
    assert d["passed"] is True
    assert d["blockers"] == []
    assert d["summary"] == "OK"


def test_stable_v1_readiness_gate_not_passed() -> None:
    b = GateBlocker(id="b1", summary="Blocker", source="test")
    gate = StableV1ReadinessGate(passed=False, blockers=[b], warnings=[], summary="Blocked")
    assert gate.passed is False
    assert len(gate.blockers) == 1
    assert gate.blockers[0].id == "b1"


def test_confidence_summary_to_dict() -> None:
    c = ConfidenceSummary(confidence="high", rationale="Good", evidence_refs=["e1"], strongest_evidence_for="x", strongest_evidence_against="y")
    d = c.to_dict()
    assert d["confidence"] == "high"
    assert d["rationale"] == "Good"
    assert "e1" in d["evidence_refs"]


def test_stable_v1_decision_to_dict() -> None:
    dec = StableV1Decision(
        recommendation=StableV1Recommendation.APPROVED.value,
        recommendation_label="Stable v1 approved",
        confidence_summary=ConfidenceSummary(rationale="All pass"),
        next_required_action="Proceed",
        generated_at_iso="2025-01-01T00:00:00Z",
    )
    d = dec.to_dict()
    assert d["recommendation"] == StableV1Recommendation.APPROVED.value
    assert d["recommendation_label"] == "Stable v1 approved"
    assert "confidence_summary" in d


def test_evaluate_stable_v1_gate_with_evidence() -> None:
    evidence = FinalEvidenceBundle(
        v1_contract_summary="Scope frozen.",
        production_cut_frozen=True,
        production_cut_vertical_id="v1",
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
        v1_ops_posture_summary="support_level=sustained",
        migration_continuity_readiness="OK",
        deploy_health_summary="validation_passed=True",
        sustained_health_summary="No major signals",
        vertical_value_retention="OK",
        drift_repair_summary="None",
    )
    gate = evaluate_stable_v1_gate(evidence=evidence)
    assert gate.passed is True
    assert len(gate.blockers) == 0


def test_evaluate_stable_v1_gate_blocked_when_cut_not_frozen() -> None:
    evidence = FinalEvidenceBundle(
        production_cut_frozen=False,
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    gate = evaluate_stable_v1_gate(evidence=evidence)
    assert gate.passed is False
    assert any(b.id == "production_cut_not_frozen" for b in gate.blockers)


def test_evaluate_stable_v1_gate_blocked_when_launch_pause() -> None:
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        production_cut_vertical_id="v1",
        release_readiness_status="ready",
        launch_recommended_decision="pause",
        stability_recommended_decision="continue",
    )
    gate = evaluate_stable_v1_gate(evidence=evidence)
    assert gate.passed is False
    assert any(b.id == "launch_decision_not_go" for b in gate.blockers)


def test_build_stable_v1_decision_approved() -> None:
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        production_cut_vertical_id="v1",
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[], summary="OK")
    decision = build_stable_v1_decision(evidence=evidence, gate=gate)
    assert decision.recommendation == StableV1Recommendation.APPROVED.value
    assert "approved" in decision.recommendation_label.lower()


def test_build_stable_v1_decision_approved_narrow() -> None:
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        production_cut_vertical_id="v1",
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    w = GateWarning(id="w1", summary="Some warning", source="test")
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[w], summary="OK with warnings")
    decision = build_stable_v1_decision(evidence=evidence, gate=gate)
    assert decision.recommendation == StableV1Recommendation.APPROVED_NARROW.value
    assert decision.narrow_condition


def test_build_stable_v1_decision_repair_required() -> None:
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        production_cut_vertical_id="v1",
        release_readiness_status="blocked",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    b = GateBlocker(id="release_readiness_blocked", summary="Blocked", source="release_readiness")
    gate = StableV1ReadinessGate(passed=False, blockers=[b], warnings=[], summary="Blocked")
    decision = build_stable_v1_decision(evidence=evidence, gate=gate)
    assert decision.recommendation == StableV1Recommendation.REPAIR_REQUIRED.value


def test_build_stable_v1_decision_scope_narrow() -> None:
    evidence = FinalEvidenceBundle(
        production_cut_frozen=False,
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    gate = StableV1ReadinessGate(passed=False, blockers=[], warnings=[], summary="Not frozen")
    decision = build_stable_v1_decision(evidence=evidence, gate=gate)
    assert decision.recommendation == StableV1Recommendation.SCOPE_NARROW.value
    assert "narrow" in decision.recommendation_label.lower() or "scope" in decision.recommendation_label.lower()


def test_build_stable_v1_report_structure() -> None:
    """Build report from explicit evidence and gate (no repo aggregation)."""
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        production_cut_vertical_id="v1",
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[], summary="OK")
    report = build_stable_v1_report(evidence=evidence, gate=gate)
    assert report.evidence is not None
    assert report.gate is not None
    assert report.decision is not None
    assert report.explain
    assert report.decision.recommendation == StableV1Recommendation.APPROVED.value
    d = report.to_dict()
    assert "evidence" in d
    assert "gate" in d
    assert "decision" in d
    assert "explain" in d


def test_explain_stable_v1_decision() -> None:
    """Explain from pre-built report."""
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[], summary="OK")
    report = build_stable_v1_report(evidence=evidence, gate=gate)
    text = explain_stable_v1_decision(report=report)
    assert "Stable v1" in text or "recommendation" in text
    assert "Gate passed" in text or "Blockers" in text


def test_get_stable_v1_gate_state() -> None:
    """State slice structure from pre-built report."""
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        production_cut_vertical_id="v1",
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[], summary="OK")
    report = build_stable_v1_report(evidence=evidence, gate=gate)
    state = get_stable_v1_gate_state(report=report)
    assert "current_stable_v1_recommendation" in state
    assert "top_final_blocker" in state
    assert "next_required_final_action" in state
    assert "gate_passed" in state
    assert "blocker_count" in state
    assert "warning_count" in state


def test_weak_evidence_scope_narrow() -> None:
    evidence = FinalEvidenceBundle(production_cut_frozen=False)
    gate = evaluate_stable_v1_gate(evidence=evidence)
    decision = build_stable_v1_decision(evidence=evidence, gate=gate)
    assert decision.recommendation == StableV1Recommendation.SCOPE_NARROW.value


# ----- M50L.1 Post-v1 watch state + roadmap carry-forward -----
def test_post_v1_watch_state_summary_model() -> None:
    s = PostV1WatchStateSummary(
        stable_v1_recommendation="stable_v1_approved",
        narrow_conditions_in_effect=["Condition A"],
        gate_warnings_summary="None.",
        experimental_summary="No experimental surfaces.",
        deferred_summary="None.",
        next_review_action="workflow-dataset stable-v1 report",
        generated_at_iso="2025-01-01T00:00:00Z",
    )
    d = s.to_dict()
    assert d["stable_v1_recommendation"] == "stable_v1_approved"
    assert d["narrow_conditions_in_effect"] == ["Condition A"]
    assert "experimental_summary" in d


def test_build_post_v1_watch_state_summary() -> None:
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        production_cut_vertical_id="v1",
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[], summary="OK")
    report = build_stable_v1_report(evidence=evidence, gate=gate)
    summary = build_post_v1_watch_state_summary(report=report)
    assert summary.stable_v1_recommendation == StableV1Recommendation.APPROVED.value
    assert summary.next_review_action
    assert summary.generated_at_iso
    d = summary.to_dict()
    assert "experimental_summary" in d
    assert "deferred_summary" in d


def test_build_post_v1_watch_state_summary_with_warnings() -> None:
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        release_readiness_status="ready",
        launch_recommended_decision="launch_narrowly",
        stability_recommended_decision="continue",
    )
    w = GateWarning(id="w1", summary="Launch narrowly", source="launch_decision_pack")
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[w], summary="OK with warnings")
    report = build_stable_v1_report(evidence=evidence, gate=gate)
    summary = build_post_v1_watch_state_summary(report=report)
    assert summary.gate_warnings_summary
    assert "warning" in summary.gate_warnings_summary.lower() or summary.gate_warnings_summary == "None."


def test_roadmap_carry_forward_item_model() -> None:
    item = RoadmapCarryForwardItem(
        item_id="roadmap_cloud",
        label="Cloud sync",
        category="roadmap",
        rationale="Deferred beyond v1",
        when_to_revisit="When in scope",
        source="roadmap",
    )
    d = item.to_dict()
    assert d["item_id"] == "roadmap_cloud"
    assert d["category"] == "roadmap"


def test_build_roadmap_carry_forward_pack() -> None:
    evidence = FinalEvidenceBundle(
        production_cut_frozen=True,
        release_readiness_status="ready",
        launch_recommended_decision="launch",
        stability_recommended_decision="continue",
    )
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[], summary="OK")
    report = build_stable_v1_report(evidence=evidence, gate=gate)
    pack = build_roadmap_carry_forward_pack(report=report)
    assert pack.pack_id == "roadmap_carry_forward_pack"
    assert pack.generated_at_iso
    assert len(pack.items) >= 2
    assert any(i.category == "roadmap" for i in pack.items)
    assert pack.summary
    d = pack.to_dict()
    assert "items" in d
    assert "experimental_count" in d
    assert "deferred_count" in d


def test_build_roadmap_carry_forward_pack_includes_deferred_from_warnings() -> None:
    w = GateWarning(id="w1", summary="Launch narrowly", source="launch_decision_pack")
    gate = StableV1ReadinessGate(passed=True, blockers=[], warnings=[w], summary="OK")
    evidence = FinalEvidenceBundle(production_cut_frozen=True, release_readiness_status="ready", launch_recommended_decision="launch", stability_recommended_decision="continue")
    report = build_stable_v1_report(evidence=evidence, gate=gate)
    pack = build_roadmap_carry_forward_pack(report=report)
    deferred = [i for i in pack.items if i.category == "deferred" and "gate_warning" in i.item_id]
    assert len(deferred) >= 1
