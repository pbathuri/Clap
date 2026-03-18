"""
M41E–M41H: Council-based evaluation — model creation, perspective scoring, disagreement, synthesis, low-evidence, conflicting outcomes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.council.models import (
    CouncilReview,
    CouncilSubject,
    CriterionScore,
    DisagreementNote,
    UncertaintyNote,
    EvidenceSummary,
    SynthesisDecision,
)
from workflow_dataset.council.perspectives import get_default_council, get_perspective, score_subject_from_perspective
from workflow_dataset.council.review import run_council_review, build_disagreement_report
from workflow_dataset.council.synthesis import synthesize_decision
from workflow_dataset.council.store import save_review, load_review, list_reviews, get_review_by_subject
from workflow_dataset.council.presets import get_preset, list_presets, get_default_preset
from workflow_dataset.council.promotion_policy import get_effective_policy, apply_policy_outcome
from workflow_dataset.council.models import CouncilPreset, PRESET_CONSERVATIVE_PRODUCTION, PRESET_BALANCED_IMPROVEMENT, PRESET_RESEARCH_MODE


def test_default_council():
    """get_default_council returns council with members for each default perspective."""
    council = get_default_council()
    assert council.council_id == "default"
    assert len(council.members) >= 5
    assert council.min_score_to_promote >= 0.5


def test_get_perspective():
    """get_perspective returns EvaluationPerspective with label."""
    p = get_perspective("safety_trust")
    assert p.perspective_id == "safety_trust"
    assert "afety" in p.label or "rust" in p.label


def test_score_subject_generic(tmp_path):
    """score_subject_from_perspective for generic subject returns CriterionScore (no ref)."""
    s = score_subject_from_perspective("exp_1", "experiment", "", "reliability", tmp_path)
    assert s.perspective_id == "reliability"
    assert 0 <= s.score <= 1.0
    assert isinstance(s.pass_threshold, bool)


def test_run_council_review_persist(tmp_path):
    """run_council_review with persist=True creates review and saves to store."""
    review = run_council_review("exp_123", "experiment", ref="exp_123", repo_root=tmp_path, persist=True)
    assert review.review_id
    assert review.subject.subject_id == "exp_123"
    assert review.subject.subject_type == "experiment"
    assert len(review.criterion_scores) >= 5
    assert review.synthesis_decision in (
        SynthesisDecision.PROMOTE.value,
        SynthesisDecision.QUARANTINE.value,
        SynthesisDecision.REJECT.value,
        SynthesisDecision.NEEDS_MORE_EVIDENCE.value,
        SynthesisDecision.PROMOTE_LIMITED_COHORT.value,
        SynthesisDecision.SAFE_EXPERIMENTAL_ONLY.value,
    )
    assert review.synthesis_reason
    path = tmp_path / "data/local/council/reviews"
    assert path.exists()
    files = list(path.glob("*.json"))
    assert len(files) >= 1


def test_load_and_list_reviews(tmp_path):
    """save_review then load_review and list_reviews return consistent data."""
    subject = CouncilSubject(subject_id="sub_1", subject_type="experiment", ref="sub_1")
    review = CouncilReview(
        review_id="cr_test1",
        subject=subject,
        at_iso="2025-01-01T12:00:00Z",
        criterion_scores=[
            CriterionScore("product_value", 0.7, "Product value", "ok", True),
            CriterionScore("safety_trust", 0.8, "Safety", "ok", True),
        ],
        synthesis_decision=SynthesisDecision.PROMOTE.value,
        synthesis_reason="All pass.",
    )
    save_review(review, tmp_path)
    loaded = load_review("cr_test1", tmp_path)
    assert loaded is not None
    assert loaded.review_id == "cr_test1"
    assert loaded.subject.subject_id == "sub_1"
    assert loaded.synthesis_decision == SynthesisDecision.PROMOTE.value
    listed = list_reviews(tmp_path, limit=10)
    assert any(r["review_id"] == "cr_test1" for r in listed)
    by_subject = get_review_by_subject("sub_1", tmp_path)
    assert by_subject is not None
    assert by_subject.review_id == "cr_test1"


def test_disagreement_report():
    """build_disagreement_report includes disagreement_notes and uncertainty_notes."""
    subject = CouncilSubject(subject_id="x", subject_type="experiment")
    review = CouncilReview(
        review_id="cr_d",
        subject=subject,
        at_iso="2025-01-01T12:00:00Z",
        criterion_scores=[
            CriterionScore("safety_trust", 0.3, "Safety", "low", False),
        ],
        disagreement_notes=[
            DisagreementNote("d1", "Safety below threshold", ["safety_trust"], "high"),
        ],
        uncertainty_notes=[
            UncertaintyNote("u1", "Low evidence", "product_value", "gather_more"),
        ],
        synthesis_decision=SynthesisDecision.QUARANTINE.value,
        synthesis_reason="Safety low.",
    )
    report = build_disagreement_report(review)
    assert report["disagreement_notes"]
    assert report["uncertainty_notes"]
    assert report["synthesis_decision"] == SynthesisDecision.QUARANTINE.value
    assert any(s["perspective_id"] == "safety_trust" for s in report["scores_below_threshold"])


def test_synthesis_low_evidence():
    """synthesize_decision with low evidence adds uncertainty and can yield needs_more_evidence."""
    subject = CouncilSubject(subject_id="low_ev", subject_type="experiment")
    review = CouncilReview(
        review_id="cr_low",
        subject=subject,
        at_iso="2025-01-01T12:00:00Z",
        criterion_scores=[
            CriterionScore("product_value", 0.7, "", "", True),
            CriterionScore("safety_trust", 0.8, "", "", True),
        ],
        evidence_summary=EvidenceSummary(source_ids=[], summary="", evidence_count=0),
    )
    out = synthesize_decision(review)
    assert out.uncertainty_notes
    assert any("evidence" in u.description.lower() for u in out.uncertainty_notes)
    assert out.synthesis_decision in (
        SynthesisDecision.NEEDS_MORE_EVIDENCE.value,
        SynthesisDecision.QUARANTINE.value,
        SynthesisDecision.PROMOTE.value,
    )


def test_synthesis_conflicting_perspectives():
    """synthesize_decision with safety fail yields reject or quarantine; disagreement visible."""
    subject = CouncilSubject(subject_id="conf", subject_type="adaptation")
    review = CouncilReview(
        review_id="cr_conf",
        subject=subject,
        at_iso="2025-01-01T12:00:00Z",
        criterion_scores=[
            CriterionScore("product_value", 0.9, "", "", True),
            CriterionScore("safety_trust", 0.3, "", "low", False),
            CriterionScore("supportability", 0.7, "", "", True),
        ],
        evidence_summary=EvidenceSummary(source_ids=["e1"], summary="", evidence_count=2),
    )
    out = synthesize_decision(review)
    assert out.synthesis_decision in (SynthesisDecision.REJECT.value, SynthesisDecision.QUARANTINE.value)
    assert out.disagreement_notes or any(not s.pass_threshold for s in out.criterion_scores if s.perspective_id == "safety_trust")


# ----- M41H.1 Council presets + promotion policies -----


def test_list_presets():
    """list_presets returns conservative_production, balanced_improvement, research_mode."""
    presets = list_presets()
    assert len(presets) >= 3
    ids = [p.preset_id for p in presets]
    assert PRESET_CONSERVATIVE_PRODUCTION in ids
    assert PRESET_BALANCED_IMPROVEMENT in ids
    assert PRESET_RESEARCH_MODE in ids


def test_get_preset():
    """get_preset returns preset by id; conservative has stricter thresholds."""
    p = get_preset(PRESET_CONSERVATIVE_PRODUCTION)
    assert p is not None
    assert p.preset_id == PRESET_CONSERVATIVE_PRODUCTION
    assert p.min_score_to_promote >= 0.7
    assert p.min_evidence_to_promote >= 3
    p2 = get_preset("nonexistent")
    assert p2 is None


def test_get_default_preset():
    """get_default_preset returns balanced_improvement."""
    p = get_default_preset()
    assert p.preset_id == PRESET_BALANCED_IMPROVEMENT


def test_effective_policy():
    """get_effective_policy returns policy with rules."""
    policy = get_effective_policy(cohort_id="", repo_root=None)
    assert policy.policy_id
    assert len(policy.rules) >= 1
    assert any(r.condition for r in policy.rules)


def test_apply_policy_outcome():
    """apply_policy_outcome returns quarantine for changes_trust_posture."""
    from workflow_dataset.council import get_effective_policy
    policy = get_effective_policy()
    out = apply_policy_outcome(policy, {"changes_trust_posture": True})
    assert out == "quarantine"
    out2 = apply_policy_outcome(policy, {})
    assert out2 is None


def test_run_council_review_with_preset(tmp_path):
    """run_council_review with preset_id uses preset (e.g. research_mode has lower min_evidence)."""
    review = run_council_review("exp_preset", "experiment", repo_root=tmp_path, persist=False, preset_id=PRESET_RESEARCH_MODE)
    assert review.synthesis_decision
    assert review.subject.subject_id == "exp_preset"
