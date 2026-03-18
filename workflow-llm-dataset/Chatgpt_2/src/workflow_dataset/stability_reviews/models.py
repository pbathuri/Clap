"""
M46I–M46L: Sustained deployment review — models for stability windows, decision packs, recommendations, evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StabilityDecision(str, Enum):
    """Explicit stability decision: continue, continue_with_watch, narrow, repair, pause, rollback."""
    CONTINUE = "continue"
    CONTINUE_WITH_WATCH = "continue_with_watch"
    NARROW = "narrow"
    REPAIR = "repair"
    PAUSE = "pause"
    ROLLBACK = "rollback"


@dataclass
class StabilityWindow:
    """Time window for assembling evidence: daily, weekly, or rolling N days."""
    kind: str  # daily | weekly | rolling_7 | rolling_30
    start_iso: str = ""
    end_iso: str = ""
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "start_iso": self.start_iso,
            "end_iso": self.end_iso,
            "label": self.label,
        }


@dataclass
class EvidenceBundle:
    """Assembled evidence for a stability decision: health, drift, repair, support, value, trust, scope."""
    health_summary: str = ""
    drift_signals: list[str] = field(default_factory=list)
    repair_history_summary: str = ""
    support_triage_burden: str = ""
    operator_burden: str = ""
    vertical_value_retention: str = ""
    trust_review_posture: str = ""
    production_scope_compliance: str = ""
    raw_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_summary": self.health_summary,
            "drift_signals": list(self.drift_signals),
            "repair_history_summary": self.repair_history_summary,
            "support_triage_burden": self.support_triage_burden,
            "operator_burden": self.operator_burden,
            "vertical_value_retention": self.vertical_value_retention,
            "trust_review_posture": self.trust_review_posture,
            "production_scope_compliance": self.production_scope_compliance,
            "raw_snapshot": dict(self.raw_snapshot),
        }


@dataclass
class ContinueRecommendation:
    """Recommendation to continue deployment as-is or with watch."""
    decision: str  # continue | continue_with_watch
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    confidence: str = "medium"  # low | medium | high

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
        }


@dataclass
class NarrowRecommendation:
    """Recommendation to narrow supported scope."""
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    suggested_scope_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "suggested_scope_note": self.suggested_scope_note,
        }


@dataclass
class RepairRecommendation:
    """Recommendation to run repair bundle before expanding."""
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    repair_bundle_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "repair_bundle_ref": self.repair_bundle_ref,
        }


@dataclass
class PauseRecommendation:
    """Recommendation to pause deployment."""
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    resume_condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "resume_condition": self.resume_condition,
        }


@dataclass
class RollbackRecommendation:
    """Recommendation to rollback to prior stable state."""
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    prior_stable_ref: str = ""  # e.g. review_id or checkpoint id

    def to_dict(self) -> dict[str, Any]:
        return {
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "prior_stable_ref": self.prior_stable_ref,
        }


@dataclass
class StabilityDecisionPack:
    """Stability decision pack: recommended decision, rationale, evidence bundle, and optional recommendation detail."""
    recommended_decision: str  # StabilityDecision value
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    evidence_bundle: EvidenceBundle | None = None
    continue_rec: ContinueRecommendation | None = None
    narrow_rec: NarrowRecommendation | None = None
    repair_rec: RepairRecommendation | None = None
    pause_rec: PauseRecommendation | None = None
    rollback_rec: RollbackRecommendation | None = None
    generated_at_iso: str = ""
    stability_window: StabilityWindow | None = None
    vertical_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "recommended_decision": self.recommended_decision,
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "generated_at_iso": self.generated_at_iso,
            "vertical_id": self.vertical_id,
        }
        if self.evidence_bundle:
            out["evidence_bundle"] = self.evidence_bundle.to_dict()
        if self.stability_window:
            out["stability_window"] = self.stability_window.to_dict()
        if self.continue_rec:
            out["continue_rec"] = self.continue_rec.to_dict()
        if self.narrow_rec:
            out["narrow_rec"] = self.narrow_rec.to_dict()
        if self.repair_rec:
            out["repair_rec"] = self.repair_rec.to_dict()
        if self.pause_rec:
            out["pause_rec"] = self.pause_rec.to_dict()
        if self.rollback_rec:
            out["rollback_rec"] = self.rollback_rec.to_dict()
        return out


@dataclass
class SustainedDeploymentReview:
    """A single sustained deployment review record: window, pack, and optional persistence id."""
    review_id: str
    at_iso: str
    stability_window: StabilityWindow
    decision_pack: StabilityDecisionPack
    next_scheduled_review_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "at_iso": self.at_iso,
            "stability_window": self.stability_window.to_dict(),
            "decision_pack": self.decision_pack.to_dict(),
            "next_scheduled_review_iso": self.next_scheduled_review_iso,
        }


# ----- M46L.1 Review cadences + long-run rollback policies + operator thresholds -----


class ReviewCadenceKind(str, Enum):
    """Cadence frequency for stability reviews."""
    DAILY = "daily"
    WEEKLY = "weekly"
    ROLLING_STABILITY = "rolling_stability"  # e.g. rolling 7-day window, review weekly


@dataclass
class ReviewCadence:
    """Review cadence: frequency, stability window kind, and operator-facing label."""
    cadence_id: str
    kind: str  # daily | weekly | rolling_stability
    window_kind: str  # daily | weekly | rolling_7 | rolling_30
    label: str = ""
    description: str = ""
    default_days_until_next: int = 7  # used when no last review

    def to_dict(self) -> dict[str, Any]:
        return {
            "cadence_id": self.cadence_id,
            "kind": self.kind,
            "window_kind": self.window_kind,
            "label": self.label,
            "description": self.description,
            "default_days_until_next": self.default_days_until_next,
        }


@dataclass
class RollbackPolicy:
    """Long-run rollback policy: when to recommend rollback and how to resolve prior stable ref."""
    policy_id: str
    label: str = ""
    recommend_rollback_on_guidance: bool = True  # when post-deployment guidance = rollback
    recommend_rollback_on_cohort_downgrade: bool = True
    max_blockers_before_rollback_considered: int = 0  # if blockers > this, rollback can be considered
    max_consecutive_pause_before_rollback_considered: int = 3  # N consecutive pause reviews
    prior_stable_ref_rule: str = "latest_continue_review"  # latest_continue_review | latest_checkpoint | manual
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "label": self.label,
            "recommend_rollback_on_guidance": self.recommend_rollback_on_guidance,
            "recommend_rollback_on_cohort_downgrade": self.recommend_rollback_on_cohort_downgrade,
            "max_blockers_before_rollback_considered": self.max_blockers_before_rollback_considered,
            "max_consecutive_pause_before_rollback_considered": self.max_consecutive_pause_before_rollback_considered,
            "prior_stable_ref_rule": self.prior_stable_ref_rule,
            "description": self.description,
        }


@dataclass
class StabilityThresholds:
    """Operator-facing thresholds: when to continue as-is vs watch vs narrow vs pause."""
    thresholds_id: str
    label: str = ""
    # Continue as-is: below these limits we can recommend continue (not just watch)
    max_warnings_continue_as_is: int = 0  # if warnings > this, prefer continue_with_watch
    max_triage_issues_continue_as_is: int = 0
    require_checkpoint_criteria_for_continue: bool = False  # if True, continue only when criteria_met
    # Narrow: above these we recommend narrow before continue
    min_triage_issues_narrow: int = 1  # high-severity open issues
    min_warnings_narrow: int = 3
    # Pause: above these we recommend pause (in addition to launch decision pause)
    min_blockers_pause: int = 1
    min_failed_gates_pause: int = 1  # critical gates
    # Watch: when evidence is weak or in band between continue and narrow
    use_watch_when_weak_evidence: bool = True
    use_watch_when_warnings_in_band: bool = True  # warnings > 0 and <= min_warnings_narrow
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "thresholds_id": self.thresholds_id,
            "label": self.label,
            "max_warnings_continue_as_is": self.max_warnings_continue_as_is,
            "max_triage_issues_continue_as_is": self.max_triage_issues_continue_as_is,
            "require_checkpoint_criteria_for_continue": self.require_checkpoint_criteria_for_continue,
            "min_triage_issues_narrow": self.min_triage_issues_narrow,
            "min_warnings_narrow": self.min_warnings_narrow,
            "min_blockers_pause": self.min_blockers_pause,
            "min_failed_gates_pause": self.min_failed_gates_pause,
            "use_watch_when_weak_evidence": self.use_watch_when_weak_evidence,
            "use_watch_when_warnings_in_band": self.use_watch_when_warnings_in_band,
            "description": self.description,
        }
