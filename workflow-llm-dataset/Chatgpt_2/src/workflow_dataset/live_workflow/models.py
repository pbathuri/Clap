"""
Real-time workflow model (M33E–M33H Phase A).

Explicit models for: supervised live workflow, step sequence, live step suggestion,
escalation tier, approval/checkpoint requirement, expected artifact/handoff,
blocked real-time step, workflow run state.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EscalationTier(str, Enum):
    """Bounded escalation tiers for real-time assist (low → high friction)."""
    HINT_ONLY = "hint_only"
    ACTION_CARD_SUGGESTION = "action_card_suggestion"
    DRAFT_HANDOFF_PREP = "draft_handoff_prep"
    PLANNER_GOAL_PREFILL = "planner_goal_prefill"
    SIMULATED_EXECUTION_HANDOFF = "simulated_execution_handoff"
    REVIEW_APPROVAL_ROUTING = "review_approval_routing"


class WorkflowRunState(str, Enum):
    """State of a supervised live workflow run."""
    ACTIVE = "active"
    PAUSED = "paused"
    AWAITING_CHECKPOINT = "awaiting_checkpoint"
    BLOCKED = "blocked"
    STALLED = "stalled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_WORKFLOW = "no_workflow"


class ExpectedHandoff(BaseModel):
    """Expected artifact or handoff target for a step."""
    label: str = Field(default="", description="Human-readable label")
    path_or_type: str = Field(default="", description="Path, type, or handoff target id")
    step_index: int | None = Field(default=None)
    handoff_target: str = Field(default="", description="e.g. open_view, compile_plan, executor_run")


class LiveStepSuggestion(BaseModel):
    """Single live step suggestion for real-time assist."""
    step_index: int = Field(default=0)
    label: str = Field(default="")
    description: str = Field(default="")
    step_class: str = Field(default="", description="e.g. sandbox_write, human_required")
    approval_required: bool = Field(default=False)
    checkpoint_before: bool = Field(default=False)
    expected_handoff: ExpectedHandoff | None = Field(default=None)
    escalation_tier: EscalationTier = Field(default=EscalationTier.HINT_ONLY)
    hint_text: str = Field(default="", description="Low-friction hint for this step")
    plan_ref: str = Field(default="", description="plan_id or routine_id / job_pack_id")
    provenance: str = Field(default="", description="e.g. routine:weekly_report")


class BlockedRealTimeStep(BaseModel):
    """A blocked real-time step with handoff info for planner/executor/review."""
    step_index: int = Field(default=0)
    label: str = Field(default="")
    blocked_reason: str = Field(default="")
    approval_scope: str = Field(default="")
    handoff_suggestion: str = Field(default="", description="Suggested next action: e.g. open planner, review approval")
    plan_ref: str = Field(default="")
    run_id: str = Field(default="")


class SupervisedLiveWorkflow(BaseModel):
    """Supervised live workflow: goal/routine ref, plan ref, steps, current step, escalation, state."""

    run_id: str = Field(default="", description="Stable id for this live run")
    goal_text: str = Field(default="", description="Goal or intent driving the workflow")
    plan_id: str = Field(default="", description="plan_id from planner when compiled")
    plan_ref: str = Field(default="", description="routine_id | job_pack_id | macro_id when from session/sources")
    plan_source: str = Field(default="", description="routine | job | macro | goal")

    steps: list[LiveStepSuggestion] = Field(default_factory=list)
    current_step_index: int = Field(default=0, ge=0)
    next_step_index: int | None = Field(default=None, ge=0)
    alternate_path_summary: str = Field(default="", description="Optional alternate path description")
    escalation_path_summary: str = Field(default="", description="Escalation path if blocked/stalled")

    current_escalation_tier: EscalationTier = Field(default=EscalationTier.HINT_ONLY)
    checkpoint_required_before: int | None = Field(default=None, description="Step index requiring checkpoint before proceeding")
    blocked_step: BlockedRealTimeStep | None = Field(default=None)
    state: WorkflowRunState = Field(default=WorkflowRunState.NO_WORKFLOW)

    project_hint: str = Field(default="")
    session_hint: str = Field(default="")
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")
    last_activity_utc: str = Field(default="", description="Last user or system activity for stall detection")
    bundle_id: str = Field(default="", description="Workflow bundle id if run started from a bundle")
    alternate_path_recommendations: list[dict[str, Any]] = Field(default_factory=list, description="Stronger alternate-path recommendations")

    def to_dict(self) -> dict[str, Any]:
        d = self.model_dump()
        d["current_escalation_tier"] = self.current_escalation_tier.value
        d["state"] = self.state.value
        return d


# ----- M33H.1 Workflow bundles, stall recovery, escalation explanation -----


class WorkflowBundle(BaseModel):
    """Reusable workflow bundle for common real-time workflows."""
    bundle_id: str = Field(default="", description="Stable id")
    label: str = Field(default="", description="Display name")
    description: str = Field(default="", description="Short description")
    goal_template: str = Field(default="", description="Goal text or template (e.g. 'Weekly report')")
    routine_id: str = Field(default="", description="Optional routine id to prefer")
    plan_ref: str = Field(default="", description="Optional plan_ref hint")
    alternate_goals: list[str] = Field(default_factory=list, description="Alternate goals for stronger path recommendations")
    recovery_suggestions: list[str] = Field(default_factory=list, description="Suggested recovery actions when stalled")
    tags: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")


class AlternatePathRecommendation(BaseModel):
    """Single alternate-path recommendation."""
    label: str = Field(default="")
    goal_or_ref: str = Field(default="", description="Goal text or routine_id/plan_ref")
    reason: str = Field(default="", description="Why this path is suggested")
    priority: int = Field(default=0, description="Higher = more recommended")


class StallRecoveryPath(BaseModel):
    """One recovery action when workflow is stalled."""
    action_label: str = Field(default="")
    handoff_target: str = Field(default="", description="e.g. compile_plan, queue_simulated")
    handoff_params: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="", description="Operator-facing reason for this recovery")


class StallDetectionResult(BaseModel):
    """Result of stall detection: stalled flag, reason, recovery paths, alternate paths."""
    stalled: bool = Field(default=False)
    reason: str = Field(default="", description="Operator-facing explanation of why stalled")
    detected_at_utc: str = Field(default="")
    suggested_recovery_paths: list[StallRecoveryPath] = Field(default_factory=list)
    alternate_paths: list[AlternatePathRecommendation] = Field(default_factory=list)
    idle_seconds: float = Field(default=0, description="Idle time used for detection if applicable")


class EscalationExplanation(BaseModel):
    """Operator-facing explanation of why escalation happened."""
    from_tier: str = Field(default="")
    to_tier: str = Field(default="")
    reason_code: str = Field(default="", description="e.g. user_requested, stall_detected, blocked_step")
    operator_message: str = Field(default="", description="Human-readable why escalation happened")
    suggested_action: str = Field(default="", description="What to do at the new tier")
