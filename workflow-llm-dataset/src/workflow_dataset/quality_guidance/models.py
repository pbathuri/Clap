"""
M47I–M47L: Quality signal and guidance models — clarity, confidence, ambiguity, ready-to-act, needs-review, weak guidance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GuidanceKind(str, Enum):
    """Kind of guidance item."""
    NEXT_ACTION = "next_action"
    REVIEW_NEEDED = "review_needed"
    BLOCKED_STATE = "blocked_state"
    RESUME = "resume"
    OPERATOR_ROUTINE = "operator_routine"
    SUPPORT_RECOVERY = "support_recovery"


@dataclass
class ClarityScore:
    """Score 0–1 for how clear the guidance is; 0 = ambiguous, 1 = unambiguous."""
    score: float
    reason: str = ""
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass
class ConfidenceWithEvidence:
    """Confidence level with explicit evidence links; do not fake high confidence when evidence is weak."""
    level: str  # low | medium | high
    evidence_refs: list[str] = field(default_factory=list)
    disclaimer: str = ""  # e.g. "Evidence is weak; recommendations are generic."

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "evidence_refs": list(self.evidence_refs),
            "disclaimer": self.disclaimer,
        }


@dataclass
class AmbiguityWarning:
    """Warning when guidance or intent is ambiguous."""
    message: str
    suggested_clarification: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "suggested_clarification": self.suggested_clarification,
            "source": self.source,
        }


@dataclass
class ReadyToActSignal:
    """Signal that the operator can act now on a specific item."""
    label: str
    action_ref: str = ""  # command or ref
    rationale: str = ""
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "action_ref": self.action_ref,
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass
class NeedsReviewSignal:
    """Signal that something needs operator review before proceeding."""
    label: str
    ref: str = ""
    priority: str = "medium"  # low | medium | high
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "ref": self.ref,
            "priority": self.priority,
            "rationale": self.rationale,
        }


@dataclass
class StrongNextStepSignal:
    """Single strong next step with rationale and evidence."""
    step_label: str
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    command_or_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_label": self.step_label,
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "command_or_ref": self.command_or_ref,
        }


@dataclass
class WeakGuidanceWarning:
    """Warning when current guidance is generic or low-evidence."""
    message: str
    improvement_hint: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "improvement_hint": self.improvement_hint,
            "source": self.source,
        }


@dataclass
class QualitySignal:
    """Aggregate quality signal for a guidance surface: clarity, confidence, optional warnings."""
    clarity: ClarityScore
    confidence: ConfidenceWithEvidence
    ambiguity_warnings: list[AmbiguityWarning] = field(default_factory=list)
    weak_guidance_warnings: list[WeakGuidanceWarning] = field(default_factory=list)
    ready_to_act: ReadyToActSignal | None = None
    needs_review: NeedsReviewSignal | None = None
    strong_next_step: StrongNextStepSignal | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "clarity": self.clarity.to_dict(),
            "confidence": self.confidence.to_dict(),
            "ambiguity_warnings": [w.to_dict() for w in self.ambiguity_warnings],
            "weak_guidance_warnings": [w.to_dict() for w in self.weak_guidance_warnings],
        }
        if self.ready_to_act:
            out["ready_to_act"] = self.ready_to_act.to_dict()
        if self.needs_review:
            out["needs_review"] = self.needs_review.to_dict()
        if self.strong_next_step:
            out["strong_next_step"] = self.strong_next_step.to_dict()
        return out


@dataclass
class GuidanceItem:
    """Single guidance item with id, kind, summary, rationale, and quality signal."""
    guide_id: str
    kind: str  # GuidanceKind value
    summary: str
    rationale: str
    quality_signal: QualitySignal
    action_ref: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    vertical_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "guide_id": self.guide_id,
            "kind": self.kind,
            "summary": self.summary,
            "rationale": self.rationale,
            "quality_signal": self.quality_signal.to_dict(),
            "action_ref": self.action_ref,
            "evidence_refs": list(self.evidence_refs),
            "vertical_id": self.vertical_id,
        }


# ----- M47L.1 Guidance presets + recovery guidance packs + operator summary -----


class GuidancePresetKind(str, Enum):
    """Preset style for formatting guidance."""
    CONCISE = "concise"
    OPERATOR_FIRST = "operator_first"
    REVIEW_HEAVY = "review_heavy"


@dataclass
class GuidancePreset:
    """Guidance preset: controls how summary/rationale are presented (concise, operator-first, review-heavy)."""
    preset_id: str
    kind: str  # concise | operator_first | review_heavy
    label: str = ""
    max_rationale_chars: int = 0  # 0 = no truncation
    emphasize_commands: bool = True
    emphasize_review: bool = False
    lead_with_recommendation: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "kind": self.kind,
            "label": self.label,
            "max_rationale_chars": self.max_rationale_chars,
            "emphasize_commands": self.emphasize_commands,
            "emphasize_review": self.emphasize_review,
            "lead_with_recommendation": self.lead_with_recommendation,
            "description": self.description,
        }


@dataclass
class RecoveryGuidancePack:
    """Recovery guidance pack for a vertical or failure pattern: what we know, recommend, need from user."""
    pack_id: str
    vertical_id: str = ""
    label: str = ""
    failure_patterns: list[str] = field(default_factory=list)  # e.g. "blocked_onboarding", "executor_blocked"
    what_we_know: str = ""
    what_we_recommend: str = ""
    what_we_need_from_user: str = ""
    commands: list[str] = field(default_factory=list)
    escalation_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "vertical_id": self.vertical_id,
            "label": self.label,
            "failure_patterns": list(self.failure_patterns),
            "what_we_know": self.what_we_know,
            "what_we_recommend": self.what_we_recommend,
            "what_we_need_from_user": self.what_we_need_from_user,
            "commands": list(self.commands),
            "escalation_ref": self.escalation_ref,
        }


@dataclass
class OperatorFacingSummary:
    """Operator-facing summary: what the system knows, what it recommends, what it needs from the user."""
    what_system_knows: str = ""
    what_it_recommends: str = ""
    what_it_needs_from_user: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    preset_id: str = ""
    recovery_pack_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "what_system_knows": self.what_system_knows,
            "what_it_recommends": self.what_it_recommends,
            "what_it_needs_from_user": self.what_it_needs_from_user,
            "evidence_refs": list(self.evidence_refs),
            "preset_id": self.preset_id,
            "recovery_pack_id": self.recovery_pack_id,
        }
