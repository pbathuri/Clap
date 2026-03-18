"""
M48I–M48L: Governed operator mode and delegation-safety models.
Binds operator mode to role and review domains; delegated scope, boundaries, suspension/revocation triggers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GovernedOperatorStatus(str, Enum):
    """Status of a governed delegation."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    REAUTHORIZATION_NEEDED = "reauthorization_needed"


@dataclass
class GovernedOperatorMode:
    """Governed operator mode: binding of operator mode to role and review domain."""
    mode_id: str = ""
    label: str = ""
    role_id: str = ""  # e.g. operator, reviewer, approver
    review_domain_id: str = ""
    authority_tier_id: str = ""
    allowed_scope_ids: list[str] = field(default_factory=list)
    enabled: bool = True
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "label": self.label,
            "role_id": self.role_id,
            "review_domain_id": self.review_domain_id,
            "authority_tier_id": self.authority_tier_id,
            "allowed_scope_ids": list(self.allowed_scope_ids),
            "enabled": self.enabled,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }


@dataclass
class DelegatedScope:
    """Explicit delegated scope: domain, role, routines, trust posture."""
    scope_id: str = ""
    label: str = ""
    review_domain_id: str = ""
    role_id: str = ""
    routine_ids: list[str] = field(default_factory=list)
    responsibility_ids: list[str] = field(default_factory=list)  # link to operator_mode responsibilities
    authority_tier_id: str = ""
    trust_preset_id: str = ""
    allowed_action_classes: list[str] = field(default_factory=list)
    forbidden_action_classes: list[str] = field(default_factory=list)
    status: str = GovernedOperatorStatus.ACTIVE.value
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_id": self.scope_id,
            "label": self.label,
            "review_domain_id": self.review_domain_id,
            "role_id": self.role_id,
            "routine_ids": list(self.routine_ids),
            "responsibility_ids": list(self.responsibility_ids),
            "authority_tier_id": self.authority_tier_id,
            "trust_preset_id": self.trust_preset_id,
            "allowed_action_classes": list(self.allowed_action_classes),
            "forbidden_action_classes": list(self.forbidden_action_classes),
            "status": self.status,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }


@dataclass
class DelegatedActionBoundary:
    """What may vs may not be done within a delegated scope."""
    boundary_id: str = ""
    scope_id: str = ""
    permitted_action_classes: list[str] = field(default_factory=list)
    excluded_action_classes: list[str] = field(default_factory=list)
    permitted_targets: list[str] = field(default_factory=list)  # path patterns or resource ids; empty = no extra restriction
    excluded_targets: list[str] = field(default_factory=list)
    require_approval_before: list[str] = field(default_factory=list)  # e.g. before_real, commit_or_send
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "scope_id": self.scope_id,
            "permitted_action_classes": list(self.permitted_action_classes),
            "excluded_action_classes": list(self.excluded_action_classes),
            "permitted_targets": list(self.permitted_targets),
            "excluded_targets": list(self.excluded_targets),
            "require_approval_before": list(self.require_approval_before),
            "created_utc": self.created_utc,
        }


@dataclass
class DelegationSafeLoop:
    """Delegation-safe loop: ties loop/responsibility to governed scope, domain, role; continuation only where allowed."""
    loop_id: str = ""
    scope_id: str = ""
    responsibility_id: str = ""
    review_domain_id: str = ""
    role_id: str = ""
    supervised_continuation_allowed: bool = False
    continuation_requires_approval: bool = True
    trust_preset_id: str = ""
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "scope_id": self.scope_id,
            "responsibility_id": self.responsibility_id,
            "review_domain_id": self.review_domain_id,
            "role_id": self.role_id,
            "supervised_continuation_allowed": self.supervised_continuation_allowed,
            "continuation_requires_approval": self.continuation_requires_approval,
            "trust_preset_id": self.trust_preset_id,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }


class TriggerKind(str, Enum):
    """Kind of suspension or revocation trigger."""
    POLICY_BREACH = "policy_breach"
    CONFIDENCE_BOUNDARY = "confidence_boundary"
    DOMAIN_CONFLICT = "domain_conflict"
    UNSAFE_AUTHORITY_STATE = "unsafe_authority_state"
    MANUAL = "manual"


@dataclass
class SuspensionTrigger:
    """Condition that can trigger suspension of a delegated loop/scope."""
    trigger_id: str = ""
    kind: str = TriggerKind.MANUAL.value
    scope_id: str = ""
    condition_ref: str = ""  # e.g. policy_id, confidence_threshold_id
    description: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "kind": self.kind,
            "scope_id": self.scope_id,
            "condition_ref": self.condition_ref,
            "description": self.description,
            "created_utc": self.created_utc,
        }


@dataclass
class RevocationTrigger:
    """Condition that can trigger revocation of a delegated scope."""
    trigger_id: str = ""
    kind: str = TriggerKind.MANUAL.value
    scope_id: str = ""
    condition_ref: str = ""
    description: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "kind": self.kind,
            "scope_id": self.scope_id,
            "condition_ref": self.condition_ref,
            "description": self.description,
            "created_utc": self.created_utc,
        }


@dataclass
class GovernedContinuationApproval:
    """Approval required to continue a suspended delegated loop (domain/role-aware)."""
    approval_id: str = ""
    loop_id: str = ""
    scope_id: str = ""
    review_domain_id: str = ""
    approver_role_id: str = ""
    approved_at_utc: str = ""
    reason: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "loop_id": self.loop_id,
            "scope_id": self.scope_id,
            "review_domain_id": self.review_domain_id,
            "approver_role_id": self.approver_role_id,
            "approved_at_utc": self.approved_at_utc,
            "reason": self.reason,
            "created_utc": self.created_utc,
        }


@dataclass
class OperatorModeDomainConflict:
    """Record of operator-mode action conflicting with domain or cross-domain rule."""
    conflict_id: str = ""
    scope_id: str = ""
    action_ref: str = ""
    source_domain_id: str = ""
    attempted_domain_id: str = ""
    role_id: str = ""
    reason_code: str = ""  # cross_domain_not_allowed | role_not_in_domain | scope_revoked | other
    detail: str = ""
    timestamp_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "scope_id": self.scope_id,
            "action_ref": self.action_ref,
            "source_domain_id": self.source_domain_id,
            "attempted_domain_id": self.attempted_domain_id,
            "role_id": self.role_id,
            "reason_code": self.reason_code,
            "detail": self.detail,
            "timestamp_utc": self.timestamp_utc,
        }


@dataclass
class DelegationExplanation:
    """Operator-facing explanation: why delegation is allowed, paused, or revoked."""
    scope_id: str = ""
    status: str = ""
    allowed: bool = False
    reason: str = ""
    detail: str = ""
    recommendation: str = ""
    generated_at_utc: str = ""
    suggested_playbook_id: str = ""
    guidance_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_id": self.scope_id,
            "status": self.status,
            "allowed": self.allowed,
            "reason": self.reason,
            "detail": self.detail,
            "recommendation": self.recommendation,
            "generated_at_utc": self.generated_at_utc,
            "suggested_playbook_id": self.suggested_playbook_id,
            "guidance_summary": self.guidance_summary,
        }


# ----- M48L.1 Delegation presets + reauthorization playbooks -----


@dataclass
class DelegationPreset:
    """Preset for governed delegation: narrow trusted routine, supervised operator, maintenance-only, etc."""
    preset_id: str = ""
    label: str = ""
    description: str = ""
    authority_tier_id: str = ""
    trust_preset_id: str = ""
    allowed_action_classes: list[str] = field(default_factory=list)
    forbidden_action_classes: list[str] = field(default_factory=list)
    default_review_domain_id: str = ""
    default_role_id: str = ""
    max_routine_ids: int = 0  # 0 = no limit; >0 suggests narrowing to this many routines
    when_to_use: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "description": self.description,
            "authority_tier_id": self.authority_tier_id,
            "trust_preset_id": self.trust_preset_id,
            "allowed_action_classes": list(self.allowed_action_classes),
            "forbidden_action_classes": list(self.forbidden_action_classes),
            "default_review_domain_id": self.default_review_domain_id,
            "default_role_id": self.default_role_id,
            "max_routine_ids": self.max_routine_ids,
            "when_to_use": self.when_to_use,
            "created_utc": self.created_utc,
        }


@dataclass
class ReauthorizationPlaybook:
    """Playbook for reauthorizing after suspend or revoke: steps, when to use, outcome."""
    playbook_id: str = ""
    label: str = ""
    description: str = ""
    situation: str = ""  # suspended | revoked | reauthorization_needed | policy_breach
    steps: list[str] = field(default_factory=list)
    when_to_use: str = ""
    outcome_note: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "label": self.label,
            "description": self.description,
            "situation": self.situation,
            "steps": list(self.steps),
            "when_to_use": self.when_to_use,
            "outcome_note": self.outcome_note,
            "created_utc": self.created_utc,
        }


@dataclass
class SuspensionRevocationGuidance:
    """Operator-facing guidance: what happens when a scope is suspended or revoked, and what to do next."""
    scope_id: str = ""
    status: str = ""
    what_happens: str = ""
    what_stops: list[str] = field(default_factory=list)
    what_continues: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    suggested_playbook_id: str = ""
    suggested_playbook_label: str = ""
    generated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_id": self.scope_id,
            "status": self.status,
            "what_happens": self.what_happens,
            "what_stops": list(self.what_stops),
            "what_continues": list(self.what_continues),
            "next_steps": list(self.next_steps),
            "suggested_playbook_id": self.suggested_playbook_id,
            "suggested_playbook_label": self.suggested_playbook_label,
            "generated_at_utc": self.generated_at_utc,
        }
