"""
M41E–M41H: Council-based evaluation — models for multi-perspective evaluation and safe improvement decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SynthesisDecision(str, Enum):
    """Final council synthesis: promote, limited, quarantine, reject, needs evidence, safe experimental only."""
    PROMOTE = "promote"
    PROMOTE_LIMITED_COHORT = "promote_in_limited_cohort"
    QUARANTINE = "quarantine"
    REJECT = "reject"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    SAFE_EXPERIMENTAL_ONLY = "safe_only_in_experimental_surfaces"


# Perspective IDs (evaluation dimensions)
PERSPECTIVE_PRODUCT_VALUE = "product_value"
PERSPECTIVE_SAFETY_TRUST = "safety_trust"
PERSPECTIVE_SUPPORTABILITY = "supportability"
PERSPECTIVE_RELIABILITY = "reliability"
PERSPECTIVE_VERTICAL_FIT = "vertical_fit"
PERSPECTIVE_OPERATOR_BURDEN = "operator_burden"
PERSPECTIVE_ADAPTATION_RISK = "adaptation_risk"

DEFAULT_PERSPECTIVE_IDS = [
    PERSPECTIVE_PRODUCT_VALUE,
    PERSPECTIVE_SAFETY_TRUST,
    PERSPECTIVE_SUPPORTABILITY,
    PERSPECTIVE_RELIABILITY,
    PERSPECTIVE_VERTICAL_FIT,
    PERSPECTIVE_OPERATOR_BURDEN,
    PERSPECTIVE_ADAPTATION_RISK,
]


@dataclass
class EvaluationPerspective:
    """One evaluation dimension (e.g. product value, safety, supportability)."""
    perspective_id: str
    label: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "perspective_id": self.perspective_id,
            "label": self.label,
            "description": self.description,
        }


@dataclass
class CouncilMember:
    """Council 'member' representing one perspective with optional weight (for synthesis)."""
    member_id: str
    perspective_id: str
    label: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "member_id": self.member_id,
            "perspective_id": self.perspective_id,
            "label": self.label,
            "weight": self.weight,
        }


@dataclass
class CriterionScore:
    """Score from one perspective for a subject."""
    perspective_id: str
    score: float  # 0.0–1.0 or normalized
    label: str = ""
    detail: str = ""
    pass_threshold: bool = False  # True if score meets minimum for promote

    def to_dict(self) -> dict[str, Any]:
        return {
            "perspective_id": self.perspective_id,
            "score": self.score,
            "label": self.label,
            "detail": self.detail,
            "pass_threshold": self.pass_threshold,
        }


@dataclass
class DisagreementNote:
    """Explicit disagreement between perspectives or vs synthesis."""
    note_id: str
    description: str
    perspective_ids: list[str] = field(default_factory=list)
    severity: str = "medium"  # low | medium | high

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "description": self.description,
            "perspective_ids": list(self.perspective_ids),
            "severity": self.severity,
        }


@dataclass
class UncertaintyNote:
    """Explicit uncertainty (low evidence, ambiguous signal)."""
    note_id: str
    description: str
    perspective_id: str = ""
    suggested_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "description": self.description,
            "perspective_id": self.perspective_id,
            "suggested_action": self.suggested_action,
        }


@dataclass
class PromotionRecommendation:
    """Recommendation to promote (optionally with scope)."""
    recommend: bool
    scope: str = "full"  # full | limited_cohort | experimental_only
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"recommend": self.recommend, "scope": self.scope, "reason": self.reason}


@dataclass
class QuarantineRecommendation:
    """Recommendation to quarantine (hold for review)."""
    recommend: bool
    reason: str = ""
    review_by_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommend": self.recommend,
            "reason": self.reason,
            "review_by_hint": self.review_by_hint,
        }


@dataclass
class EvidenceSummary:
    """Summary of evidence used for this council review."""
    source_ids: list[str] = field(default_factory=list)
    summary: str = ""
    evidence_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_ids": list(self.source_ids),
            "summary": self.summary,
            "evidence_count": self.evidence_count,
        }


@dataclass
class CouncilSubject:
    """Subject under council review (experiment, adaptation, eval run, etc.)."""
    subject_id: str
    subject_type: str  # adaptation | eval_run | experiment | queue_tuning | trusted_routine | vertical_workflow | production_cut
    ref: str = ""  # e.g. adaptation_id, run_id
    summary: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "ref": self.ref,
            "summary": self.summary,
            "extra": dict(self.extra),
        }


@dataclass
class EvaluationCouncil:
    """Council definition: id, label, members (perspectives), default thresholds."""
    council_id: str
    label: str
    members: list[CouncilMember] = field(default_factory=list)
    min_score_to_promote: float = 0.6
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "council_id": self.council_id,
            "label": self.label,
            "members": [m.to_dict() for m in self.members],
            "min_score_to_promote": self.min_score_to_promote,
            "description": self.description,
        }


# ----- M41H.1 Council presets + promotion policies -----

PRESET_CONSERVATIVE_PRODUCTION = "conservative_production"
PRESET_BALANCED_IMPROVEMENT = "balanced_improvement"
PRESET_RESEARCH_MODE = "research_mode"

DEFAULT_PRESET_ID = PRESET_BALANCED_IMPROVEMENT


@dataclass
class CouncilPreset:
    """Council preset: thresholds and rules for conservative production, balanced improvement, or research mode."""
    preset_id: str
    label: str
    description: str = ""
    min_score_to_promote: float = 0.6
    min_evidence_to_promote: int = 2
    required_perspectives_pass: list[str] = field(default_factory=list)  # empty = all
    allow_limited_rollout: bool = True
    allow_safe_experimental_only: bool = True
    reject_if_safety_below: float = 0.4
    quarantine_if_adaptation_risk_below: float = 0.4
    quarantine_if_any_high_severity_disagreement: bool = True
    needs_evidence_if_low_evidence: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "description": self.description,
            "min_score_to_promote": self.min_score_to_promote,
            "min_evidence_to_promote": self.min_evidence_to_promote,
            "required_perspectives_pass": list(self.required_perspectives_pass),
            "allow_limited_rollout": self.allow_limited_rollout,
            "allow_safe_experimental_only": self.allow_safe_experimental_only,
            "reject_if_safety_below": self.reject_if_safety_below,
            "quarantine_if_adaptation_risk_below": self.quarantine_if_adaptation_risk_below,
            "quarantine_if_any_high_severity_disagreement": self.quarantine_if_any_high_severity_disagreement,
            "needs_evidence_if_low_evidence": self.needs_evidence_if_low_evidence,
        }


@dataclass
class PromotionPolicyRule:
    """Single rule: condition -> outcome (quarantine, reject, limited_rollout, experimental_only)."""
    rule_id: str
    condition: str  # affects_supported_surface | affects_experimental_only | changes_trust_posture | high_risk
    outcome: str  # quarantine | reject | limited_rollout | experimental_only | no_override
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"rule_id": self.rule_id, "condition": self.condition, "outcome": self.outcome, "reason": self.reason}


@dataclass
class PromotionPolicy:
    """Promotion policy tied to cohort and/or production-cut: rules for limited rollout vs quarantine vs reject."""
    policy_id: str
    label: str
    cohort_id: str = ""
    production_cut_id: str = ""
    description: str = ""
    rules: list[PromotionPolicyRule] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "label": self.label,
            "cohort_id": self.cohort_id,
            "production_cut_id": self.production_cut_id,
            "description": self.description,
            "rules": [r.to_dict() for r in self.rules],
        }


@dataclass
class CouncilReview:
    """Full council review: subject, scores per perspective, disagreement/uncertainty notes, evidence, synthesis."""
    review_id: str
    subject: CouncilSubject
    at_iso: str
    criterion_scores: list[CriterionScore] = field(default_factory=list)
    disagreement_notes: list[DisagreementNote] = field(default_factory=list)
    uncertainty_notes: list[UncertaintyNote] = field(default_factory=list)
    evidence_summary: EvidenceSummary = field(default_factory=EvidenceSummary)
    synthesis_decision: str = ""  # SynthesisDecision value
    synthesis_reason: str = ""
    promotion_recommendation: PromotionRecommendation | None = None
    quarantine_recommendation: QuarantineRecommendation | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "subject": self.subject.to_dict(),
            "at_iso": self.at_iso,
            "criterion_scores": [c.to_dict() for c in self.criterion_scores],
            "disagreement_notes": [d.to_dict() for d in self.disagreement_notes],
            "uncertainty_notes": [u.to_dict() for u in self.uncertainty_notes],
            "evidence_summary": self.evidence_summary.to_dict(),
            "synthesis_decision": self.synthesis_decision,
            "synthesis_reason": self.synthesis_reason,
            "promotion_recommendation": self.promotion_recommendation.to_dict() if self.promotion_recommendation else None,
            "quarantine_recommendation": self.quarantine_recommendation.to_dict() if self.quarantine_recommendation else None,
        }
