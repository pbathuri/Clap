"""
M45A: Adaptive execution model — plan, bounded loop, step, branch, outcome, triggers, stop/escalation, takeover.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ----- Step outcome -----

@dataclass
class StepOutcome:
    """Outcome of executing one step: status, artifact, confidence, drift."""
    step_index: int = 0
    step_id: str = ""
    status: str = ""  # success | blocked | error | skip
    artifact: str = ""
    confidence: float = 0.0
    drift_summary: str = ""
    matched_expected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "step_id": self.step_id,
            "status": self.status,
            "artifact": self.artifact,
            "confidence": self.confidence,
            "drift_summary": self.drift_summary,
            "matched_expected": self.matched_expected,
        }


# ----- Adaptation trigger -----

@dataclass
class AdaptationTrigger:
    """When to adapt: outcome type, confidence threshold, or condition id."""
    trigger_id: str = ""
    kind: str = ""  # outcome_status | confidence_below | condition_met | manual
    outcome_status: str = ""  # e.g. blocked, error
    confidence_threshold: float = 0.0
    condition_ref: str = ""
    branch_to_id: str = ""  # plan_branch_id or fallback label
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "kind": self.kind,
            "outcome_status": self.outcome_status,
            "confidence_threshold": self.confidence_threshold,
            "condition_ref": self.condition_ref,
            "branch_to_id": self.branch_to_id,
            "reason": self.reason,
        }


# ----- Stop / escalation / takeover -----

@dataclass
class StopCondition:
    """Condition that stops the loop (no more steps)."""
    condition_id: str = ""
    kind: str = ""  # max_steps_reached | manual_stop | confidence_below | blocked_step | policy_violation
    description: str = ""
    step_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "kind": self.kind,
            "description": self.description,
            "step_index": self.step_index,
        }


@dataclass
class EscalationCondition:
    """Condition that escalates to human (loop pauses, operator must act)."""
    condition_id: str = ""
    kind: str = ""  # blocked | policy_change | approval_required | confidence_below
    description: str = ""
    step_index: int | None = None
    handoff_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "kind": self.kind,
            "description": self.description,
            "step_index": self.step_index,
            "handoff_reason": self.handoff_reason,
        }


@dataclass
class HumanTakeoverPoint:
    """Explicit point where human must approve or take over before continuing."""
    step_index: int = 0
    label: str = ""
    gate_kind: str = ""  # approval | review | handoff
    required_approval: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "label": self.label,
            "gate_kind": self.gate_kind,
            "required_approval": self.required_approval,
            "reason": self.reason,
        }


# ----- Plan branch -----

@dataclass
class PlanBranch:
    """One branch or path in an adaptive plan (e.g. main, fallback, human_only)."""
    branch_id: str = ""
    label: str = ""
    description: str = ""
    step_indices: list[int] = field(default_factory=list)  # ordered step indices in this branch
    is_fallback: bool = False
    is_human_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "label": self.label,
            "description": self.description,
            "step_indices": list(self.step_indices),
            "is_fallback": self.is_fallback,
            "is_human_only": self.is_human_only,
        }


# ----- Execution step (adaptive) -----

@dataclass
class ExecutionStep:
    """One step in an adaptive execution plan; can be shared across branches."""
    step_index: int = 0
    step_id: str = ""
    label: str = ""
    action_type: str = ""  # job_run | adapter_action | macro_step | human_required
    action_ref: str = ""
    trust_level: str = ""
    approval_required: bool = False
    checkpoint_before: bool = False
    allowed: bool = True
    expected_artifact: str = ""
    blocked_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "step_id": self.step_id,
            "label": self.label,
            "action_type": self.action_type,
            "action_ref": self.action_ref,
            "trust_level": self.trust_level,
            "approval_required": self.approval_required,
            "checkpoint_before": self.checkpoint_before,
            "allowed": self.allowed,
            "expected_artifact": self.expected_artifact,
            "blocked_reason": self.blocked_reason,
        }


# ----- Adaptive execution plan -----

@dataclass
class AdaptiveExecutionPlan:
    """Plan that can branch and adapt: steps, branches, triggers, stop/escalation, takeover points."""
    plan_id: str = ""
    goal_text: str = ""
    steps: list[ExecutionStep] = field(default_factory=list)
    branches: list[PlanBranch] = field(default_factory=list)
    default_branch_id: str = ""
    fallback_branch_id: str = ""
    adaptation_triggers: list[AdaptationTrigger] = field(default_factory=list)
    stop_conditions: list[StopCondition] = field(default_factory=list)
    escalation_conditions: list[EscalationCondition] = field(default_factory=list)
    human_takeover_points: list[HumanTakeoverPoint] = field(default_factory=list)
    allowed_action_refs: list[str] = field(default_factory=list)
    forbidden_action_refs: list[str] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal_text": self.goal_text,
            "steps": [s.to_dict() for s in self.steps],
            "branches": [b.to_dict() for b in self.branches],
            "default_branch_id": self.default_branch_id,
            "fallback_branch_id": self.fallback_branch_id,
            "adaptation_triggers": [t.to_dict() for t in self.adaptation_triggers],
            "stop_conditions": [c.to_dict() for c in self.stop_conditions],
            "escalation_conditions": [c.to_dict() for c in self.escalation_conditions],
            "human_takeover_points": [h.to_dict() for h in self.human_takeover_points],
            "allowed_action_refs": list(self.allowed_action_refs),
            "forbidden_action_refs": list(self.forbidden_action_refs),
            "sources_used": list(self.sources_used),
            "created_at": self.created_at,
        }


# ----- M45D.1: Execution profile -----

@dataclass
class ExecutionProfile:
    """
    Execution profile: presets for max_steps, review density, trust mode.
    conservative: low max_steps, review every step, simulate-first.
    balanced: moderate max_steps, checkpoints from plan.
    operator_heavy: higher max_steps, fewer mandatory reviews, for trusted operator flows.
    review_heavy: lower max_steps, review at every step, for high-stakes workflows.
    """
    profile_id: str = ""
    label: str = ""
    description: str = ""
    max_steps_cap: int = 20
    review_every_n_steps: int = 0  # 0 = use plan checkpoints only
    require_review_before_first_step: bool = False
    trust_mode: str = ""  # simulate_first | approval_required | trusted_bounded
    why_safe: str = ""  # operator-facing: why this profile is safe to use
    when_blocked: str = ""  # when this profile would be blocked or downgraded

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "description": self.description,
            "max_steps_cap": self.max_steps_cap,
            "review_every_n_steps": self.review_every_n_steps,
            "require_review_before_first_step": self.require_review_before_first_step,
            "trust_mode": self.trust_mode,
            "why_safe": self.why_safe,
            "when_blocked": self.when_blocked,
        }


# ----- M45D.1: Loop template -----

@dataclass
class LoopTemplate:
    """
    Loop template for common bounded workflows: goal hint, default profile, required approvals,
    operator-facing why_safe and why_blocked explanations.
    """
    template_id: str = ""
    label: str = ""
    description: str = ""
    goal_hint: str = ""  # e.g. "Weekly summary", "Approval sweep"
    default_profile_id: str = ""
    required_approval_scopes: list[str] = field(default_factory=list)  # e.g. checkpoint_before_real, approval_registry
    max_steps_default: int = 10
    why_safe: str = ""  # operator-facing: why this template is safe when used as intended
    why_blocked: str = ""  # operator-facing: when/why this template would be blocked

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "label": self.label,
            "description": self.description,
            "goal_hint": self.goal_hint,
            "default_profile_id": self.default_profile_id,
            "required_approval_scopes": list(self.required_approval_scopes),
            "max_steps_default": self.max_steps_default,
            "why_safe": self.why_safe,
            "why_blocked": self.why_blocked,
        }


# ----- Bounded execution loop -----

@dataclass
class BoundedExecutionLoop:
    """One running instance of a bounded adaptive loop: plan ref, state, step index, branch, stop/escalation."""
    loop_id: str = ""
    plan_id: str = ""
    plan: AdaptiveExecutionPlan | None = None
    status: str = ""  # running | paused | awaiting_takeover | stopped | escalated | completed
    current_step_index: int = 0
    current_branch_id: str = ""
    max_steps: int = 0
    steps_executed: int = 0
    required_review_step_indices: list[int] = field(default_factory=list)
    outcomes: list[StepOutcome] = field(default_factory=list)
    stop_reason: str = ""
    escalation_reason: str = ""
    next_takeover_step_index: int | None = None
    fallback_activated: bool = False
    created_at: str = ""
    updated_at: str = ""
    profile_id: str = ""  # M45D.1: execution profile used
    template_id: str = ""  # M45D.1: loop template used, if any

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "plan_id": self.plan_id,
            "status": self.status,
            "current_step_index": self.current_step_index,
            "current_branch_id": self.current_branch_id,
            "max_steps": self.max_steps,
            "steps_executed": self.steps_executed,
            "required_review_step_indices": list(self.required_review_step_indices),
            "outcomes": [o.to_dict() for o in self.outcomes],
            "stop_reason": self.stop_reason,
            "escalation_reason": self.escalation_reason,
            "next_takeover_step_index": self.next_takeover_step_index,
            "fallback_activated": self.fallback_activated,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "profile_id": self.profile_id,
            "template_id": self.template_id,
            "plan": self.plan.to_dict() if self.plan else None,
        }
