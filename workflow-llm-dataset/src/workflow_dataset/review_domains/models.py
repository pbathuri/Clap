"""
M48E–M48H Phase A: Review domain model.
Review domain, approval domain, review participant role, escalation route,
multi-review requirement, sensitive action domain, domain-specific audit trail, blocked cross-domain action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ParticipantCapability(str, Enum):
    """What a participant may do in a domain."""
    OBSERVE = "observe"
    REVIEW = "review"   # comment, suggest; may or may not approve
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"


@dataclass
class ReviewParticipantRole:
    """Role that may participate in a review domain (observer, reviewer, approver, etc.)."""
    role_id: str = ""   # e.g. operator, reviewer, approver, auditor
    capabilities: list[str] = field(default_factory=lambda: [ParticipantCapability.OBSERVE.value])
    display_name: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "capabilities": list(self.capabilities),
            "display_name": self.display_name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReviewParticipantRole":
        return cls(
            role_id=d.get("role_id", ""),
            capabilities=list(d.get("capabilities") or []),
            display_name=d.get("display_name", ""),
            description=d.get("description", ""),
        )


@dataclass
class EscalationRoute:
    """Route to escalate to a higher-trust reviewer or domain."""
    target_domain_id: str = ""   # or empty for "same domain, different role"
    target_role_id: str = ""
    trigger_condition: str = ""   # e.g. self_approve_blocked | sensitivity_threshold | manual
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_domain_id": self.target_domain_id,
            "target_role_id": self.target_role_id,
            "trigger_condition": self.trigger_condition,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EscalationRoute":
        return cls(
            target_domain_id=d.get("target_domain_id", ""),
            target_role_id=d.get("target_role_id", ""),
            trigger_condition=d.get("trigger_condition", ""),
            description=d.get("description", ""),
        )


@dataclass
class MultiReviewRequirement:
    """Requirement for multiple distinct reviewers/approvers."""
    min_reviewers: int = 1
    min_approvers: int = 1
    distinct_roles_required: bool = False   # approvers must be different roles
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_reviewers": self.min_reviewers,
            "min_approvers": self.min_approvers,
            "distinct_roles_required": self.distinct_roles_required,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MultiReviewRequirement":
        return cls(
            min_reviewers=int(d.get("min_reviewers", 1)),
            min_approvers=int(d.get("min_approvers", 1)),
            distinct_roles_required=bool(d.get("distinct_roles_required", False)),
            description=d.get("description", ""),
        )


@dataclass
class ReviewDomain:
    """A named domain for grouping review/approval context (e.g. operator routine, sensitive gate)."""
    domain_id: str = ""
    name: str = ""
    description: str = ""
    scope_note: str = ""   # what actions/artifacts fall under this domain
    allowed_roles: list[ReviewParticipantRole] = field(default_factory=list)
    escalation_routes: list[EscalationRoute] = field(default_factory=list)
    multi_review: MultiReviewRequirement | None = None
    self_approve_blocked: bool = False   # initiator role cannot approve
    linked_authority_tier_ids: list[str] = field(default_factory=list)   # trust tier alignment

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "name": self.name,
            "description": self.description,
            "scope_note": self.scope_note,
            "allowed_roles": [r.to_dict() for r in self.allowed_roles],
            "escalation_routes": [e.to_dict() for e in self.escalation_routes],
            "multi_review": self.multi_review.to_dict() if self.multi_review else None,
            "self_approve_blocked": self.self_approve_blocked,
            "linked_authority_tier_ids": list(self.linked_authority_tier_ids),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReviewDomain":
        mr = d.get("multi_review")
        return cls(
            domain_id=d.get("domain_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            scope_note=d.get("scope_note", ""),
            allowed_roles=[ReviewParticipantRole.from_dict(x) for x in (d.get("allowed_roles") or [])],
            escalation_routes=[EscalationRoute.from_dict(x) for x in (d.get("escalation_routes") or [])],
            multi_review=MultiReviewRequirement.from_dict(mr) if mr else None,
            self_approve_blocked=bool(d.get("self_approve_blocked", False)),
            linked_authority_tier_ids=list(d.get("linked_authority_tier_ids") or []),
        )


@dataclass
class ApprovalDomain:
    """Subset of a review domain that defines approval boundaries (who may approve, escalation)."""
    approval_domain_id: str = ""
    review_domain_id: str = ""
    name: str = ""
    allowed_approver_role_ids: list[str] = field(default_factory=list)
    min_approvers: int = 1
    escalation_route: EscalationRoute | None = None
    self_approve_blocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_domain_id": self.approval_domain_id,
            "review_domain_id": self.review_domain_id,
            "name": self.name,
            "allowed_approver_role_ids": list(self.allowed_approver_role_ids),
            "min_approvers": self.min_approvers,
            "escalation_route": self.escalation_route.to_dict() if self.escalation_route else None,
            "self_approve_blocked": self.self_approve_blocked,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ApprovalDomain":
        er = d.get("escalation_route")
        return cls(
            approval_domain_id=d.get("approval_domain_id", ""),
            review_domain_id=d.get("review_domain_id", ""),
            name=d.get("name", ""),
            allowed_approver_role_ids=list(d.get("allowed_approver_role_ids") or []),
            min_approvers=int(d.get("min_approvers", 1)),
            escalation_route=EscalationRoute.from_dict(er) if er else None,
            self_approve_blocked=bool(d.get("self_approve_blocked", False)),
        )


@dataclass
class SensitiveActionDomain:
    """Maps sensitive action kinds (commit/send/apply, production_repair, etc.) to a review domain."""
    action_kind: str = ""   # commit | send | apply | production_repair | trusted_routine_audit | adaptation_promotion
    review_domain_id: str = ""
    approval_domain_id: str = ""
    sensitivity_label: str = ""   # e.g. high, critical

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_kind": self.action_kind,
            "review_domain_id": self.review_domain_id,
            "approval_domain_id": self.approval_domain_id,
            "sensitivity_label": self.sensitivity_label,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SensitiveActionDomain":
        return cls(
            action_kind=d.get("action_kind", ""),
            review_domain_id=d.get("review_domain_id", ""),
            approval_domain_id=d.get("approval_domain_id", ""),
            sensitivity_label=d.get("sensitivity_label", ""),
        )


@dataclass
class DomainAuditTrace:
    """Domain-specific audit trail entry (references existing ledger; adds domain context)."""
    trace_id: str = ""
    domain_id: str = ""
    gate_id: str = ""
    entry_id: str = ""   # AuditLedgerEntry.entry_id
    action_kind: str = ""
    timestamp_utc: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "domain_id": self.domain_id,
            "gate_id": self.gate_id,
            "entry_id": self.entry_id,
            "action_kind": self.action_kind,
            "timestamp_utc": self.timestamp_utc,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DomainAuditTrace":
        return cls(
            trace_id=d.get("trace_id", ""),
            domain_id=d.get("domain_id", ""),
            gate_id=d.get("gate_id", ""),
            entry_id=d.get("entry_id", ""),
            action_kind=d.get("action_kind", ""),
            timestamp_utc=d.get("timestamp_utc", ""),
            summary=d.get("summary", ""),
        )


@dataclass
class BlockedCrossDomainAction:
    """Record of an action blocked because it crosses domain boundaries or role is not allowed."""
    block_id: str = ""
    action_ref: str = ""   # gate_id, queue_id, etc.
    source_domain_id: str = ""
    attempted_domain_id: str = ""
    role_id: str = ""
    reason_code: str = ""   # cross_domain_not_allowed | role_not_in_domain | self_approve_blocked | escalation_required
    detail: str = ""
    timestamp_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "action_ref": self.action_ref,
            "source_domain_id": self.source_domain_id,
            "attempted_domain_id": self.attempted_domain_id,
            "role_id": self.role_id,
            "reason_code": self.reason_code,
            "detail": self.detail,
            "timestamp_utc": self.timestamp_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BlockedCrossDomainAction":
        return cls(
            block_id=d.get("block_id", ""),
            action_ref=d.get("action_ref", ""),
            source_domain_id=d.get("source_domain_id", ""),
            attempted_domain_id=d.get("attempted_domain_id", ""),
            role_id=d.get("role_id", ""),
            reason_code=d.get("reason_code", ""),
            detail=d.get("detail", ""),
            timestamp_utc=d.get("timestamp_utc", ""),
        )


# ----- M48H.1: Domain policies + escalation packs -----


@dataclass
class ReviewDomainPolicy:
    """
    Policy for a review domain: separation of duties, initiator cannot approve, rationale.
    Makes explicit why approvals require distinct roles.
    """
    policy_id: str = ""
    domain_id: str = ""
    name: str = ""
    description: str = ""
    separation_of_duties_required: bool = False
    initiator_cannot_approve: bool = False
    min_distinct_approvers: int = 1
    policy_rationale: str = ""   # why this policy (e.g. "Sensitive actions require a second party sign-off.")
    scope_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "domain_id": self.domain_id,
            "name": self.name,
            "description": self.description,
            "separation_of_duties_required": self.separation_of_duties_required,
            "initiator_cannot_approve": self.initiator_cannot_approve,
            "min_distinct_approvers": self.min_distinct_approvers,
            "policy_rationale": self.policy_rationale,
            "scope_note": self.scope_note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReviewDomainPolicy":
        return cls(
            policy_id=d.get("policy_id", ""),
            domain_id=d.get("domain_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            separation_of_duties_required=bool(d.get("separation_of_duties_required", False)),
            initiator_cannot_approve=bool(d.get("initiator_cannot_approve", False)),
            min_distinct_approvers=int(d.get("min_distinct_approvers", 1)),
            policy_rationale=d.get("policy_rationale", ""),
            scope_note=d.get("scope_note", ""),
        )


@dataclass
class EscalationPackEntry:
    """One entry in an escalation pack: action/domain + route + trigger."""
    action_kind: str = ""   # commit | send | apply | production_repair | etc.
    domain_id: str = ""     # review domain this applies to
    target_role_id: str = ""
    trigger_condition: str = ""   # self_approve_blocked | sensitivity_threshold | manual
    description: str = ""
    step_order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_kind": self.action_kind,
            "domain_id": self.domain_id,
            "target_role_id": self.target_role_id,
            "trigger_condition": self.trigger_condition,
            "description": self.description,
            "step_order": self.step_order,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EscalationPackEntry":
        return cls(
            action_kind=d.get("action_kind", ""),
            domain_id=d.get("domain_id", ""),
            target_role_id=d.get("target_role_id", ""),
            trigger_condition=d.get("trigger_condition", ""),
            description=d.get("description", ""),
            step_order=int(d.get("step_order", 0)),
        )


@dataclass
class EscalationPack:
    """Pack of escalation steps for sensitive actions; one pack can cover multiple actions/domains."""
    pack_id: str = ""
    name: str = ""
    description: str = ""
    entries: list[EscalationPackEntry] = field(default_factory=list)
    sensitivity_label: str = ""   # high | critical (applies when action matches)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "name": self.name,
            "description": self.description,
            "entries": [e.to_dict() for e in self.entries],
            "sensitivity_label": self.sensitivity_label,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EscalationPack":
        return cls(
            pack_id=d.get("pack_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            entries=[EscalationPackEntry.from_dict(x) for x in (d.get("entries") or [])],
            sensitivity_label=d.get("sensitivity_label", ""),
        )
