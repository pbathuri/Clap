"""
M47I–M47L: Quality signals + operator guidance — quality signal generation, ambiguity, ready-to-act, blocked recovery, weak guidance.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.quality_guidance.models import (
    ClarityScore,
    ConfidenceWithEvidence,
    AmbiguityWarning,
    ReadyToActSignal,
    NeedsReviewSignal,
    StrongNextStepSignal,
    WeakGuidanceWarning,
    QualitySignal,
    GuidanceItem,
    GuidanceKind,
)
from workflow_dataset.quality_guidance.signals import build_quality_signals
from workflow_dataset.quality_guidance.guidance import (
    next_best_action_guidance,
    blocked_state_guidance,
    resume_guidance,
)
from workflow_dataset.quality_guidance.surfaces import (
    ready_now_states,
    not_safe_yet_states,
    ambiguity_report,
    weak_guidance_report,
    next_recommended_guidance_improvement,
)
from workflow_dataset.quality_guidance.store import (
    save_latest_guidance,
    get_guidance_by_id,
    list_latest_guide_ids,
)


def test_clarity_score_to_dict():
    c = ClarityScore(0.8, "Specific action.", ["mission_control"])
    d = c.to_dict()
    assert d["score"] == 0.8
    assert "Specific" in d["reason"]
    assert "mission_control" in d["evidence_refs"]


def test_confidence_with_evidence_to_dict():
    c = ConfidenceWithEvidence("low", ["evidence_a"], "Evidence is weak.")
    d = c.to_dict()
    assert d["level"] == "low"
    assert d["disclaimer"] == "Evidence is weak."


def test_ambiguity_warning_to_dict():
    a = AmbiguityWarning("Intent unclear.", "Specify project id.", "conversational")
    d = a.to_dict()
    assert "Intent" in d["message"]
    assert "project" in d["suggested_clarification"]


def test_ready_to_act_signal_to_dict():
    r = ReadyToActSignal("Resume run", "executor resume", "Run paused at checkpoint.", ["executor"])
    d = r.to_dict()
    assert d["label"] == "Resume run"
    assert d["action_ref"] == "executor resume"


def test_quality_signal_to_dict():
    q = QualitySignal(
        clarity=ClarityScore(0.9, "Clear.", []),
        confidence=ConfidenceWithEvidence("high", [], ""),
        ready_to_act=ReadyToActSignal("Do X", "cmd", "Why.", []),
    )
    d = q.to_dict()
    assert d["clarity"]["score"] == 0.9
    assert d["ready_to_act"]["label"] == "Do X"


def test_guidance_item_to_dict():
    q = QualitySignal(
        clarity=ClarityScore(0.7, "", []),
        confidence=ConfidenceWithEvidence("medium", [], ""),
    )
    g = GuidanceItem(
        guide_id="guide_next_abc",
        kind=GuidanceKind.NEXT_ACTION.value,
        summary="Next: build",
        rationale="Pending proposals need review.",
        quality_signal=q,
        action_ref="devlab show-proposal",
    )
    d = g.to_dict()
    assert d["guide_id"] == "guide_next_abc"
    assert d["kind"] == "next_action"
    assert "build" in d["summary"]


def test_build_quality_signals_returns_dict(tmp_path):
    out = build_quality_signals(tmp_path)
    assert isinstance(out, dict)
    assert "next_action_signal" in out
    assert "ambiguity_warnings" in out
    assert "weak_guidance_warnings" in out
    assert "strongest_ready_to_act" in out or "next_action_signal" in out


def test_ambiguity_report_structure(tmp_path):
    report = ambiguity_report(tmp_path)
    assert "ambiguity_count" in report
    assert "warnings" in report
    assert "summary" in report
    assert isinstance(report["warnings"], list)


def test_weak_guidance_report_structure(tmp_path):
    report = weak_guidance_report(tmp_path)
    assert "weak_guidance_count" in report
    assert "weak_guidance_warnings" in report
    assert "weakest_guidance_surface" in report
    assert "summary" in report


def test_ready_now_states_returns_list(tmp_path):
    states = ready_now_states(tmp_path)
    assert isinstance(states, list)
    for s in states:
        assert "label" in s or "rationale" in s


def test_not_safe_yet_states_returns_list(tmp_path):
    states = not_safe_yet_states(tmp_path)
    assert isinstance(states, list)


def test_next_recommended_guidance_improvement_returns_dict(tmp_path):
    imp = next_recommended_guidance_improvement(tmp_path)
    assert "priority" in imp
    assert "message" in imp
    assert "suggested_action" in imp


def test_next_best_action_guidance_returns_item_or_none(tmp_path):
    g = next_best_action_guidance(tmp_path)
    if g:
        assert g.guide_id
        assert g.kind == GuidanceKind.NEXT_ACTION.value
        assert g.quality_signal.clarity.score >= 0
        assert g.quality_signal.confidence.level in ("low", "medium", "high")


def test_blocked_state_guidance_may_return_none(tmp_path):
    g = blocked_state_guidance(repo_root=tmp_path)
    if g:
        assert g.kind == GuidanceKind.BLOCKED_STATE.value
        assert g.quality_signal.clarity


def test_resume_guidance_may_return_none(tmp_path):
    g = resume_guidance(tmp_path)
    if g:
        assert g.kind == GuidanceKind.RESUME.value


def test_store_save_and_get_by_id(tmp_path):
    from workflow_dataset.quality_guidance.models import QualitySignal
    q = QualitySignal(
        clarity=ClarityScore(0.8, "", []),
        confidence=ConfidenceWithEvidence("medium", [], ""),
    )
    item = GuidanceItem(
        guide_id="guide_test_123",
        kind="next_action",
        summary="Test",
        rationale="Test rationale.",
        quality_signal=q,
    )
    save_latest_guidance([item], tmp_path)
    found = get_guidance_by_id("guide_test_123", tmp_path)
    assert found is not None
    assert found.get("guide_id") == "guide_test_123"
    ids = list_latest_guide_ids(tmp_path)
    assert "guide_test_123" in ids


def test_low_evidence_next_action_has_weak_warning(tmp_path):
    """When next action is hold with no urgent signal, weak guidance warning is present in signals."""
    signals = build_quality_signals(tmp_path)
    next_sig = signals.get("next_action_signal")
    if next_sig and next_sig.get("strong_next_step", {}).get("step_label") == "hold":
        weak = next_sig.get("weak_guidance_warnings", [])
        assert len(weak) >= 1 or next_sig.get("confidence", {}).get("level") == "low"


# ----- M47L.1 Guidance presets + recovery packs + operator summary -----


def test_guidance_preset_defaults():
    from workflow_dataset.quality_guidance.presets import get_default_presets, get_preset_for
    presets = get_default_presets()
    assert len(presets) >= 3
    ids = [p.preset_id for p in presets]
    assert "concise" in ids
    assert "operator_first" in ids
    assert "review_heavy" in ids
    p = get_preset_for("concise")
    assert p is not None
    assert p.max_rationale_chars == 120
    assert get_preset_for("nonexistent") is None


def test_preset_load_save(tmp_path):
    from workflow_dataset.quality_guidance.presets import load_active_preset, save_active_preset, get_preset_for
    path = save_active_preset("review_heavy", tmp_path)
    assert path.exists()
    active = load_active_preset(tmp_path)
    assert active.preset_id == "review_heavy"
    assert active.emphasize_review is True


def test_apply_preset_to_guidance():
    from workflow_dataset.quality_guidance.models import QualitySignal
    from workflow_dataset.quality_guidance.presets import get_preset_for, apply_preset_to_guidance
    preset = get_preset_for("concise")
    assert preset is not None
    q = QualitySignal(
        clarity=ClarityScore(0.8, "", []),
        confidence=ConfidenceWithEvidence("medium", [], ""),
    )
    item = GuidanceItem(
        guide_id="g1",
        kind="next_action",
        summary="Next: build",
        rationale="Pending proposals need operator review; apply or reject.",
        quality_signal=q,
        action_ref="devlab show-proposal",
    )
    summary, rationale = apply_preset_to_guidance(item, preset)
    assert "Next: build" in summary or "build" in summary
    assert len(rationale) <= 121 or rationale == item.rationale


def test_recovery_pack_defaults():
    from workflow_dataset.quality_guidance.recovery_packs import (
        get_default_recovery_packs,
        get_recovery_pack_for_failure_pattern,
        get_recovery_pack_for_vertical,
    )
    packs = get_default_recovery_packs()
    assert len(packs) >= 2
    pack = get_recovery_pack_for_failure_pattern("executor_blocked")
    assert pack is not None
    assert pack.pack_id == "executor_blocked"
    assert "retry" in pack.what_we_recommend.lower() or "skip" in pack.what_we_recommend.lower()
    assert pack.what_we_need_from_user
    pack2 = get_recovery_pack_for_vertical("founder_operator_core")
    assert pack2 is not None
    assert pack2.vertical_id == "founder_operator_core" or pack2.vertical_id == ""


def test_operator_summary_structure(tmp_path):
    from workflow_dataset.quality_guidance.operator_summary import build_operator_summary
    from workflow_dataset.quality_guidance.models import OperatorFacingSummary
    s = build_operator_summary(tmp_path)
    assert isinstance(s, OperatorFacingSummary)
    assert s.what_system_knows is not None
    assert s.what_it_recommends is not None
    assert s.what_it_needs_from_user is not None
    assert "preset_id" in s.to_dict()
    assert "recovery_pack_id" in s.to_dict()


def test_operator_summary_with_failure_pattern(tmp_path):
    from workflow_dataset.quality_guidance.operator_summary import build_operator_summary
    s = build_operator_summary(tmp_path, failure_pattern="executor_blocked")
    assert s.recovery_pack_id == "executor_blocked"
    assert "retry" in s.what_it_recommends.lower() or "skip" in s.what_it_recommends.lower() or "blocked" in s.what_system_knows.lower()
