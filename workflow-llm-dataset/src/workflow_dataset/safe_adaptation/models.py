"""
M38I–M38L: Safe adaptation and boundary models — adaptation candidate, surface types,
quarantine state, cohort boundary check, evidence bundle, review decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ----- Surface adaptation classification (align with cohort SUPPORT_*) -----
ADAPTATION_SURFACE_SUPPORTED = "supported"
ADAPTATION_SURFACE_EXPERIMENTAL = "experimental"
ADAPTATION_SURFACE_BLOCKED = "blocked"

# ----- Review status -----
ADAPTATION_STATUS_PENDING = "pending"
ADAPTATION_STATUS_ACCEPTED = "accepted"
ADAPTATION_STATUS_REJECTED = "rejected"
ADAPTATION_STATUS_QUARANTINED = "quarantined"
ADAPTATION_STATUS_BLOCKED = "blocked"


class ReviewDecisionKind(str, Enum):
    """Outcome of a review."""
    ACCEPT = "accept"
    REJECT = "reject"
    QUARANTINE = "quarantine"


@dataclass
class AdaptationEvidenceBundle:
    """Bundle of evidence refs (triage evidence_ids, optional correction_ids) backing an adaptation candidate."""
    evidence_ids: list[str] = field(default_factory=list)
    correction_ids: list[str] = field(default_factory=list)
    session_ids: list[str] = field(default_factory=list)
    summary: str = ""
    evidence_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_ids": list(self.evidence_ids),
            "correction_ids": list(self.correction_ids),
            "session_ids": list(self.session_ids),
            "summary": self.summary,
            "evidence_count": self.evidence_count,
        }


@dataclass
class CohortBoundaryCheck:
    """Result of boundary evaluation for one candidate."""
    candidate_id: str = ""
    cohort_id: str = ""
    affects_supported_surface: bool = False
    affects_experimental_surface: bool = False
    affects_blocked_surface: bool = False
    safe_for_cohort: bool = False
    changes_trust_posture: bool = False
    experimental_only: bool = False
    must_quarantine: bool = False
    reasons: list[str] = field(default_factory=list)
    allowed_surfaces: list[str] = field(default_factory=list)
    blocked_surfaces: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "cohort_id": self.cohort_id,
            "affects_supported_surface": self.affects_supported_surface,
            "affects_experimental_surface": self.affects_experimental_surface,
            "affects_blocked_surface": self.affects_blocked_surface,
            "safe_for_cohort": self.safe_for_cohort,
            "changes_trust_posture": self.changes_trust_posture,
            "experimental_only": self.experimental_only,
            "must_quarantine": self.must_quarantine,
            "reasons": list(self.reasons),
            "allowed_surfaces": list(self.allowed_surfaces),
            "blocked_surfaces": list(self.blocked_surfaces),
        }


@dataclass
class ReviewDecision:
    """Record of a review: accept, reject, or quarantine; rationale and optional behavior delta."""
    decision_id: str = ""
    candidate_id: str = ""
    decision: str = ""  # accept | reject | quarantine
    rationale: str = ""
    behavior_delta_summary: str = ""
    reviewed_at_utc: str = ""
    reviewed_by: str = ""  # e.g. operator, cli

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "candidate_id": self.candidate_id,
            "decision": self.decision,
            "rationale": self.rationale,
            "behavior_delta_summary": self.behavior_delta_summary,
            "reviewed_at_utc": self.reviewed_at_utc,
            "reviewed_by": self.reviewed_by,
        }


@dataclass
class QuarantineState:
    """State of a quarantined candidate: reason and optional review-by date."""
    candidate_id: str = ""
    reason: str = ""
    quarantined_at_utc: str = ""
    review_recommended_by_utc: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "reason": self.reason,
            "quarantined_at_utc": self.quarantined_at_utc,
            "review_recommended_by_utc": self.review_recommended_by_utc,
            "notes": self.notes,
        }


# ----- Typed wrappers for surface-specific adaptation (for clarity in boundary logic) -----


@dataclass
class SupportedSurfaceAdaptation:
    """Adaptation that applies only to surfaces in the cohort's supported list."""
    candidate_id: str = ""
    surface_ids: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "surface_ids": list(self.surface_ids),
            "summary": self.summary,
        }


@dataclass
class ExperimentalSurfaceAdaptation:
    """Adaptation that applies only to surfaces in the cohort's experimental list (no promotion to supported)."""
    candidate_id: str = ""
    surface_ids: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "surface_ids": list(self.surface_ids),
            "summary": self.summary,
        }


@dataclass
class BlockedAdaptation:
    """Adaptation that cannot be applied (touches blocked surface or fails boundary check)."""
    candidate_id: str = ""
    reason: str = ""
    blocked_surface_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "reason": self.reason,
            "blocked_surface_ids": list(self.blocked_surface_ids),
        }


@dataclass
class AdaptationCandidate:
    """One adaptation candidate from real-user evidence; reviewable; apply only within boundaries."""
    adaptation_id: str = ""
    cohort_id: str = ""
    affected_surface_ids: list[str] = field(default_factory=list)
    surface_type: str = ADAPTATION_SURFACE_EXPERIMENTAL  # supported | experimental (never blocked on create)
    target_type: str = ""   # e.g. preference, output_style, routine_ordering, trigger_suppression
    target_id: str = ""
    before_value: Any = None
    after_value: Any = None
    evidence: AdaptationEvidenceBundle = field(default_factory=AdaptationEvidenceBundle)
    risk_level: str = "low"  # low | medium | high
    review_status: str = ADAPTATION_STATUS_PENDING
    created_at_utc: str = ""
    updated_at_utc: str = ""
    summary: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "adaptation_id": self.adaptation_id,
            "cohort_id": self.cohort_id,
            "affected_surface_ids": list(self.affected_surface_ids),
            "surface_type": self.surface_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "evidence": self.evidence.to_dict(),
            "risk_level": self.risk_level,
            "review_status": self.review_status,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            "summary": self.summary,
            "extra": dict(self.extra),
        }
