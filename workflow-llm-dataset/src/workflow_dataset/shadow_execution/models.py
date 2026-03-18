"""
M45E–M45H Phase A: Shadow execution run, expected/observed outcomes, confidence, risk, intervention gates,
safe-to-continue and forced-takeover state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GateType(str, Enum):
    """Intervention gate type."""
    MUST_REVIEW_NEXT_STEP = "must_review_next_step"
    MUST_STOP_LOOP = "must_stop_loop"
    MAY_CONTINUE_SHADOW_ONLY = "may_continue_shadow_only"
    MAY_CONTINUE_BOUNDED_REAL = "may_continue_bounded_real"
    MUST_DOWNGRADE_PROFILE = "must_downgrade_profile"
    MUST_HANDOFF_HUMAN = "must_handoff_human"


@dataclass
class ExpectedOutcome:
    """Expected outcome for one step in a shadow run."""
    step_index: int = 0
    step_id: str = ""
    label: str = ""
    expected_artifact: str = ""
    expected_status: str = ""  # success | blocked | skip
    success_criteria: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "step_id": self.step_id,
            "label": self.label,
            "expected_artifact": self.expected_artifact,
            "expected_status": self.expected_status,
            "success_criteria": self.success_criteria,
        }


@dataclass
class ObservedOutcome:
    """Observed outcome for one step after shadow/simulate execution."""
    step_index: int = 0
    step_id: str = ""
    observed_status: str = ""  # success | blocked | error | skip
    observed_artifact: str = ""
    drift_summary: str = ""
    matched_expected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "step_id": self.step_id,
            "observed_status": self.observed_status,
            "observed_artifact": self.observed_artifact,
            "drift_summary": self.drift_summary,
            "matched_expected": self.matched_expected,
        }


@dataclass
class ConfidenceScore:
    """Confidence score for a step or the whole loop (0–1)."""
    scope: str = ""  # step | loop
    step_index: int | None = None
    score: float = 0.0
    factors: list[str] = field(default_factory=list)
    degraded_penalty: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "step_index": self.step_index,
            "score": self.score,
            "factors": list(self.factors),
            "degraded_penalty": self.degraded_penalty,
        }


@dataclass
class RiskMarker:
    """Risk marker for a step or loop."""
    scope: str = ""
    step_index: int | None = None
    level: str = ""  # low | medium | high
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "step_index": self.step_index,
            "level": self.level,
            "reason": self.reason,
        }


@dataclass
class GateFailureReason:
    """Reason a gate failed (why intervention is required)."""
    gate_type: str = ""
    reason: str = ""
    threshold_crossed: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_type": self.gate_type,
            "reason": self.reason,
            "threshold_crossed": self.threshold_crossed,
        }


@dataclass
class InterventionGate:
    """One intervention gate evaluation result."""
    gate_type: str = ""
    passed: bool = True
    failure_reason: GateFailureReason | None = None
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_type": self.gate_type,
            "passed": self.passed,
            "failure_reason": self.failure_reason.to_dict() if self.failure_reason else None,
            "recommended_action": self.recommended_action,
        }


@dataclass
class SafeToContinueState:
    """State when run may continue (shadow only or bounded real)."""
    may_continue: bool = True
    mode_allowed: str = ""  # shadow_only | bounded_real
    next_gate_type: str = ""
    conditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "may_continue": self.may_continue,
            "mode_allowed": self.mode_allowed,
            "next_gate_type": self.next_gate_type,
            "conditions": list(self.conditions),
        }


@dataclass
class ForcedTakeoverState:
    """State when run must hand off to human immediately."""
    forced: bool = False
    reason: str = ""
    failed_gate_type: str = ""
    handoff_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "forced": self.forced,
            "reason": self.reason,
            "failed_gate_type": self.failed_gate_type,
            "handoff_summary": self.handoff_summary,
        }


@dataclass
class ShadowRun:
    """One shadow execution run: plan ref, steps, expected/observed, confidence, risk, gates."""
    shadow_run_id: str = ""
    plan_source: str = ""
    plan_ref: str = ""
    loop_type: str = ""  # routine | job | macro
    status: str = ""  # pending | running | completed | stopped | takeover
    current_step_index: int = 0
    expected_outcomes: list[ExpectedOutcome] = field(default_factory=list)
    observed_outcomes: list[ObservedOutcome] = field(default_factory=list)
    confidence_step: list[ConfidenceScore] = field(default_factory=list)
    confidence_loop: ConfidenceScore | None = None
    risk_markers: list[RiskMarker] = field(default_factory=list)
    gates: list[InterventionGate] = field(default_factory=list)
    safe_to_continue: SafeToContinueState | None = None
    forced_takeover: ForcedTakeoverState | None = None
    timestamp_start: str = ""
    timestamp_end: str = ""
    executor_run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "shadow_run_id": self.shadow_run_id,
            "plan_source": self.plan_source,
            "plan_ref": self.plan_ref,
            "loop_type": self.loop_type,
            "status": self.status,
            "current_step_index": self.current_step_index,
            "expected_outcomes": [e.to_dict() for e in self.expected_outcomes],
            "observed_outcomes": [o.to_dict() for o in self.observed_outcomes],
            "confidence_step": [c.to_dict() for c in self.confidence_step],
            "confidence_loop": self.confidence_loop.to_dict() if self.confidence_loop else None,
            "risk_markers": [r.to_dict() for r in self.risk_markers],
            "gates": [g.to_dict() for g in self.gates],
            "safe_to_continue": self.safe_to_continue.to_dict() if self.safe_to_continue else None,
            "forced_takeover": self.forced_takeover.to_dict() if self.forced_takeover else None,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "executor_run_id": self.executor_run_id,
        }


# ----- M45H.1: Confidence policies + promotion eligibility -----


@dataclass
class ConfidencePolicy:
    """Confidence policy by loop type: rules for shadow-only vs eligible for bounded real."""
    policy_id: str = ""
    loop_type: str = ""  # routine | job | macro
    label: str = ""
    min_loop_confidence_for_bounded_real: float = 0.75
    max_risk_level_for_bounded_real: str = "medium"  # high -> not eligible
    require_min_step_confidence: float = 0.4
    allow_high_risk: bool = False
    operator_summary_shadow_only: str = ""
    operator_summary_eligible: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "loop_type": self.loop_type,
            "label": self.label,
            "min_loop_confidence_for_bounded_real": self.min_loop_confidence_for_bounded_real,
            "max_risk_level_for_bounded_real": self.max_risk_level_for_bounded_real,
            "require_min_step_confidence": self.require_min_step_confidence,
            "allow_high_risk": self.allow_high_risk,
            "operator_summary_shadow_only": self.operator_summary_shadow_only,
            "operator_summary_eligible": self.operator_summary_eligible,
        }


@dataclass
class PromotionEligibilityReport:
    """Operator-facing report: why loop remains shadow-only or is eligible for bounded real."""
    shadow_run_id: str = ""
    eligible_for_bounded_real: bool = False
    reason_shadow_only: list[str] = field(default_factory=list)
    reason_eligible: list[str] = field(default_factory=list)
    applied_policy_id: str = ""
    applied_policy_label: str = ""
    operator_summary: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shadow_run_id": self.shadow_run_id,
            "eligible_for_bounded_real": self.eligible_for_bounded_real,
            "reason_shadow_only": list(self.reason_shadow_only),
            "reason_eligible": list(self.reason_eligible),
            "applied_policy_id": self.applied_policy_id,
            "applied_policy_label": self.applied_policy_label,
            "operator_summary": self.operator_summary,
            "details": dict(self.details),
        }
