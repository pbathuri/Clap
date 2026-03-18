"""
M35E–M35H: Personal operator mode models.
M35H.1: Responsibility bundles, pause state, revocation, work-impact explanation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResponsibilityKind(str, Enum):
    """Kind of delegated responsibility."""
    RECURRING_SUMMARY = "recurring_summary"
    APPROVAL_SWEEP = "approval_sweep"
    REFRESH_STATE = "refresh_state"
    STAGE_DRAFTS = "stage_drafts"
    FOLLOW_UP_QUEUE = "follow_up_queue"
    MORNING_CONTINUITY = "morning_continuity"
    RESUME_CONTINUITY = "resume_continuity"


class DelegatedResponsibility(BaseModel):
    """One delegated responsibility: project/pack/routine, authority, review gates, stop/escalation."""

    responsibility_id: str = Field(default="")
    kind: ResponsibilityKind = Field(default=ResponsibilityKind.RECURRING_SUMMARY)
    label: str = Field(default="")
    description: str = Field(default="")
    project_id: str = Field(default="")
    pack_id: str = Field(default="")
    routine_id: str = Field(default="")
    authority_tier_id: str = Field(default="", description="Placeholder for Pane 1")
    contract_ref: str = Field(default="")
    review_gates: list[str] = Field(default_factory=list, description="e.g. before_real, before_send")
    stop_conditions: list[str] = Field(default_factory=list)
    escalation_conditions: list[str] = Field(default_factory=list)
    workflow_ref: str = Field(default="", description="Linked automation workflow_id or plan_ref")
    trigger_ref: str = Field(default="", description="Linked trigger_id if any")
    enabled: bool = Field(default=True)
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")


class OperatorModeProfile(BaseModel):
    """Operator mode profile: on/off, scope, default gates."""

    profile_id: str = Field(default="")
    label: str = Field(default="")
    enabled: bool = Field(default=False)
    scope_project_ids: list[str] = Field(default_factory=list)
    scope_pack_ids: list[str] = Field(default_factory=list)
    default_review_gates: list[str] = Field(default_factory=list)
    is_default: bool = Field(default=False)
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")


class SuspensionRevocationState(BaseModel):
    """Aggregate state: suspended and revoked responsibility ids with reasons."""

    suspended_ids: list[str] = Field(default_factory=list)
    suspended_reasons: dict[str, str] = Field(default_factory=dict, description="responsibility_id -> reason")
    revoked_ids: list[str] = Field(default_factory=list)
    revoked_reasons: dict[str, str] = Field(default_factory=dict)
    updated_utc: str = Field(default="")


class OperatorModeSummary(BaseModel):
    """Summary for CLI/mission control: active, suspended, revoked, next action, awaiting review, escalation."""

    active_responsibility_ids: list[str] = Field(default_factory=list)
    suspended_responsibility_ids: list[str] = Field(default_factory=list)
    revoked_responsibility_ids: list[str] = Field(default_factory=list)
    next_governed_action_id: str = Field(default="")
    next_governed_action_label: str = Field(default="")
    next_gate: str = Field(default="", description="background | supervised | approval")
    awaiting_review_responsibility_ids: list[str] = Field(default_factory=list)
    top_escalation_candidate_id: str = Field(default="")
    top_escalation_reason: str = Field(default="")


# ----- M35H.1 Responsibility bundles -----


class ResponsibilityBundle(BaseModel):
    """Reusable bundle of delegated responsibilities (e.g. founder_morning_ops)."""

    bundle_id: str = Field(default="")
    label: str = Field(default="")
    description: str = Field(default="")
    responsibility_ids: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")


# ----- M35H.1 Emergency / safe pause -----


class PauseKind(str, Enum):
    """Type of pause."""
    NONE = "none"
    EMERGENCY = "emergency"
    SAFE = "safe"


class PauseState(BaseModel):
    """Current pause state: none, emergency (all stop), or safe (bounded continue)."""

    kind: PauseKind = Field(default=PauseKind.NONE)
    reason: str = Field(default="")
    started_utc: str = Field(default="")
    expires_utc: str = Field(default="", description="Optional; empty = until cleared")
    safe_continue_responsibility_ids: list[str] = Field(
        default_factory=list,
        description="For safe pause: only these responsibilities may continue",
    )
    updated_utc: str = Field(default="")


# ----- M35H.1 Revocation -----


class RevocationRecord(BaseModel):
    """One revocation event: responsibility or bundle, reason, at."""

    revocation_id: str = Field(default="")
    responsibility_id: str = Field(default="", description="Set if single responsibility revoked")
    bundle_id: str = Field(default="", description="Set if bundle revoked (all its responsibilities)")
    reason: str = Field(default="")
    revoked_at_utc: str = Field(default="")
    revoked_responsibility_ids: list[str] = Field(default_factory=list, description="Resolved list of responsibility ids")


# ----- M35H.1 Work-impact explanation -----


class WorkImpactExplanation(BaseModel):
    """Clear explanation: what work will stop, continue, or require human takeover."""

    what_stops: list[str] = Field(default_factory=list, description="Responsibility ids or labels that will stop")
    what_continues: list[str] = Field(default_factory=list, description="Responsibility ids or labels that will continue")
    what_requires_human: list[str] = Field(
        default_factory=list,
        description="Items that need human takeover or review",
    )
    pause_active: bool = Field(default=False)
    pause_kind: str = Field(default="")
    revoked_count: int = Field(default=0)
    summary: str = Field(default="", description="One-line operator-facing summary")
    generated_at_utc: str = Field(default="")


class PauseRevocationReport(BaseModel):
    """Report produced by pause/revocation flow: state + impact explanation."""

    pause_state: PauseState = Field(default_factory=lambda: PauseState())
    revocation_records: list[RevocationRecord] = Field(default_factory=list)
    impact: WorkImpactExplanation = Field(default_factory=WorkImpactExplanation)
    report_generated_at_utc: str = Field(default="")
