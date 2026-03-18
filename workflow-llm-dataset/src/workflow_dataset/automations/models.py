"""
M34A–M34D: Trigger and recurring workflow definition models.

Explicit trigger kinds, scope, conditions, debounce/repeat, policy/trust, retention.
Recurring workflow: id, project/pack/routine, triggers, goal, execution mode, stop conditions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TriggerKind(str, Enum):
    """Kind of automation trigger."""
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    PROJECT_STATE = "project_state"
    IDLE_RESUME = "idle_resume"
    APPROVAL_AVAILABLE = "approval_available"
    ARTIFACT_UPDATED = "artifact_updated"
    RECURRING_DIGEST = "recurring_digest"


class TriggerDefinition(BaseModel):
    """One bounded automation trigger definition."""

    trigger_id: str = Field(default="", description="Stable id")
    kind: TriggerKind = Field(default=TriggerKind.TIME_BASED)
    label: str = Field(default="", description="Display name")
    scope: str = Field(default="global", description="global | project:<id> | pack:<id> | routine:<id>")
    enabled: bool = Field(default=True)
    condition: dict[str, Any] = Field(default_factory=dict, description="Kind-specific: cron_expression, project_id, artifact_pattern, idle_seconds, etc.")
    debounce_seconds: float = Field(default=0, description="Min seconds between fires")
    repeat_limit_per_day: int = Field(default=0, description="0 = no limit")
    required_policy_trust: str = Field(default="simulate", description="simulate | approval_required | trusted")
    retention_days: int = Field(default=30, description="History retention")
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")
    last_matched_utc: str = Field(default="")
    match_count: int = Field(default=0)


class RecurringWorkflowDefinition(BaseModel):
    """One recurring workflow definition: triggers, goal, execution mode, stop conditions."""

    workflow_id: str = Field(default="", description="Stable id")
    label: str = Field(default="")
    description: str = Field(default="")
    project_id: str = Field(default="", description="Optional associated project")
    pack_id: str = Field(default="", description="Optional value pack")
    routine_id: str = Field(default="", description="Optional routine id")
    trigger_ids: list[str] = Field(default_factory=list, description="Trigger definitions that can start this workflow")
    planner_goal: str = Field(default="", description="Goal text for planner compile")
    plan_ref: str = Field(default="", description="Alternative: routine_id or job_pack_id for plan source")
    plan_source: str = Field(default="goal", description="goal | routine | job")
    execution_mode: str = Field(default="simulate", description="simulate | real | simulate_then_real")
    stop_conditions: list[str] = Field(default_factory=list, description="e.g. artifact_produced, step_count_max, manual_stop")
    artifact_expectations: list[str] = Field(default_factory=list, description="Expected outputs")
    approval_points: list[int] = Field(default_factory=list, description="Step indices requiring approval")
    review_destination: str = Field(default="", description="e.g. inbox_studio, review_studio")
    enabled: bool = Field(default=True)
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")


class TriggerMatchResult(BaseModel):
    """Result of evaluating one trigger: matched, reason, blocked/suppressed."""
    trigger_id: str = Field(default="")
    workflow_id: str = Field(default="", description="Workflow this trigger is tied to if any")
    matched: bool = Field(default=False)
    reason: str = Field(default="")
    blocked: bool = Field(default=False)
    blocked_reason: str = Field(default="")
    suppressed: bool = Field(default=False)
    suppressed_reason: str = Field(default="")
    evaluated_at_utc: str = Field(default="")


class TriggerEvaluationSummary(BaseModel):
    """Summary of trigger evaluation: active, suppressed, blocked, last matched, next scheduled."""
    active_trigger_ids: list[str] = Field(default_factory=list)
    suppressed_trigger_ids: list[str] = Field(default_factory=list)
    blocked_trigger_ids: list[str] = Field(default_factory=list)
    last_matched_trigger_id: str = Field(default="")
    last_matched_utc: str = Field(default="")
    next_scheduled_workflow_id: str = Field(default="", description="Next recurring workflow by schedule if any")
    next_scheduled_utc: str = Field(default="")
    awaiting_review_workflow_ids: list[str] = Field(default_factory=list)
    matches: list[TriggerMatchResult] = Field(default_factory=list)


# ----- M34D.1 Automation templates + guardrail profiles -----


class AutomationTemplateKind(str, Enum):
    """Built-in automation template kinds."""
    MORNING_DIGEST = "morning_digest"
    BLOCKED_WORK_FOLLOW_UP = "blocked_work_follow_up"
    APPROVAL_SWEEP = "approval_sweep"
    END_OF_DAY_WRAP = "end_of_day_wrap"


class AutomationTemplate(BaseModel):
    """Reusable automation template: default trigger + workflow shape."""
    template_id: str = Field(default="")
    kind: AutomationTemplateKind = Field(default=AutomationTemplateKind.MORNING_DIGEST)
    label: str = Field(default="")
    description: str = Field(default="")
    default_trigger_kind: str = Field(default="recurring_digest", description="TriggerKind value")
    default_trigger_condition: dict[str, Any] = Field(default_factory=dict)
    default_trigger_scope: str = Field(default="global")
    default_planner_goal: str = Field(default="")
    default_plan_ref: str = Field(default="")
    default_execution_mode: str = Field(default="simulate")
    default_stop_conditions: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")


class GuardrailProfileKind(str, Enum):
    """Guardrail profile presets."""
    STRICT = "strict"
    SUPERVISED = "supervised"
    BOUNDED_RECURRING = "bounded_recurring"


class SuppressionRule(BaseModel):
    """One rule for suppressing or blocking a trigger under a guardrail profile."""
    rule_id: str = Field(default="")
    description: str = Field(default="", description="Operator-facing rule description")
    trigger_kind_filter: str = Field(default="", description="Apply only to this trigger kind (empty = all)")
    condition_type: str = Field(default="", description="e.g. outside_schedule, no_approval, exceeds_daily_cap")
    action: str = Field(default="suppress", description="suppress | block")
    reason: str = Field(default="", description="Operator-facing reason when applied")
    params: dict[str, Any] = Field(default_factory=dict, description="e.g. max_per_day, allowed_hours")


class GuardrailProfile(BaseModel):
    """Guardrail profile: suppression rules and allowed behavior."""
    profile_id: str = Field(default="")
    kind: GuardrailProfileKind = Field(default=GuardrailProfileKind.SUPERVISED)
    label: str = Field(default="")
    description: str = Field(default="")
    suppression_rules: list[SuppressionRule] = Field(default_factory=list)
    allowed_trigger_kinds: list[str] = Field(default_factory=list, description="Empty = all allowed")
    require_approval_for_real: bool = Field(default=True)
    max_recurring_per_day: int = Field(default=0, description="0 = no cap")
    is_default: bool = Field(default=False, description="Use as active profile when no override")
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")
