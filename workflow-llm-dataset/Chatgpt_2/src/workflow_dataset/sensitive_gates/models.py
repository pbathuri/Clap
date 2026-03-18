"""
M35I–M35L: Commit/send/apply gates + audit ledger models.
Sensitive action gate, candidates, sign-off, rationale, blocked reason, verification;
audit ledger entry, linked project/routine/action, approval chain, operator sign-off,
execution result, rollback/recovery note, verification outcome.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ----- Phase A: Sensitive action gate model -----

class SensitiveActionKind(str, Enum):
    """Kind of sensitive action: commit, send, apply."""
    COMMIT = "commit"
    SEND = "send"
    APPLY = "apply"


@dataclass
class SignOffRequirement:
    """Requirement for human sign-off before proceeding."""
    required: bool = True
    authority_tier_id: str = ""   # e.g. commit_or_send_candidate
    contract_ref: str = ""         # contract_id if from contract
    scope_note: str = ""


@dataclass
class ReviewRationale:
    """Operator-provided rationale for approve/reject/defer."""
    decision: str = ""   # approved | rejected | deferred
    rationale: str = ""
    operator_id: str = ""   # optional identifier
    timestamp_utc: str = ""


@dataclass
class BlockedGateReason:
    """Structured reason a gate is blocked."""
    code: str = ""   # policy_denied | approval_missing | scope_mismatch | contract_not_met | verification_failed | other
    detail: str = ""
    source_ref: str = ""   # policy_id, contract_id, etc.


@dataclass
class PostActionVerificationRequirement:
    """Requirement to verify after execution (e.g. artifact exists)."""
    required: bool = False
    kind: str = ""   # artifact_exists | outcome_recorded | manual_confirm
    target_ref: str = ""
    note: str = ""


@dataclass
class CommitCandidate:
    """Staged commit action candidate."""
    candidate_id: str = ""
    label: str = ""
    target_ref: str = ""   # path, repo, branch
    plan_ref: str = ""
    run_id: str = ""
    sign_off_requirement: SignOffRequirement | None = None
    blocked_reason: BlockedGateReason | None = None
    verification_requirement: PostActionVerificationRequirement | None = None
    created_utc: str = ""
    project_id: str = ""
    routine_id: str = ""
    contract_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "kind": SensitiveActionKind.COMMIT.value,
            "label": self.label,
            "target_ref": self.target_ref,
            "plan_ref": self.plan_ref,
            "run_id": self.run_id,
            "sign_off_requirement": _sign_off_to_dict(self.sign_off_requirement),
            "blocked_reason": _blocked_to_dict(self.blocked_reason),
            "verification_requirement": _verification_to_dict(self.verification_requirement),
            "created_utc": self.created_utc,
            "project_id": self.project_id,
            "routine_id": self.routine_id,
            "contract_id": self.contract_id,
        }


@dataclass
class SendCandidate:
    """Staged send action candidate (e.g. email, API push)."""
    candidate_id: str = ""
    label: str = ""
    target_ref: str = ""   # recipient, endpoint
    plan_ref: str = ""
    run_id: str = ""
    sign_off_requirement: SignOffRequirement | None = None
    blocked_reason: BlockedGateReason | None = None
    verification_requirement: PostActionVerificationRequirement | None = None
    created_utc: str = ""
    project_id: str = ""
    routine_id: str = ""
    contract_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "kind": SensitiveActionKind.SEND.value,
            "label": self.label,
            "target_ref": self.target_ref,
            "plan_ref": self.plan_ref,
            "run_id": self.run_id,
            "sign_off_requirement": _sign_off_to_dict(self.sign_off_requirement),
            "blocked_reason": _blocked_to_dict(self.blocked_reason),
            "verification_requirement": _verification_to_dict(self.verification_requirement),
            "created_utc": self.created_utc,
            "project_id": self.project_id,
            "routine_id": self.routine_id,
            "contract_id": self.contract_id,
        }


@dataclass
class ApplyCandidate:
    """Staged apply action candidate (e.g. apply config, deploy step)."""
    candidate_id: str = ""
    label: str = ""
    target_ref: str = ""   # environment, resource
    plan_ref: str = ""
    run_id: str = ""
    sign_off_requirement: SignOffRequirement | None = None
    blocked_reason: BlockedGateReason | None = None
    verification_requirement: PostActionVerificationRequirement | None = None
    created_utc: str = ""
    project_id: str = ""
    routine_id: str = ""
    contract_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "kind": SensitiveActionKind.APPLY.value,
            "label": self.label,
            "target_ref": self.target_ref,
            "plan_ref": self.plan_ref,
            "run_id": self.run_id,
            "sign_off_requirement": _sign_off_to_dict(self.sign_off_requirement),
            "blocked_reason": _blocked_to_dict(self.blocked_reason),
            "verification_requirement": _verification_to_dict(self.verification_requirement),
            "created_utc": self.created_utc,
            "project_id": self.project_id,
            "routine_id": self.routine_id,
            "contract_id": self.contract_id,
        }


@dataclass
class SensitiveActionGate:
    """Explicit gate for one sensitive action: candidate + status + decision."""
    gate_id: str = ""
    action_kind: str = ""   # commit | send | apply
    candidate: dict[str, Any] = field(default_factory=dict)   # CommitCandidate/SendCandidate/ApplyCandidate to_dict
    status: str = ""   # pending | approved | rejected | deferred
    review_rationale: ReviewRationale | None = None
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "action_kind": self.action_kind,
            "candidate": dict(self.candidate),
            "status": self.status,
            "review_rationale": _rationale_to_dict(self.review_rationale),
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SensitiveActionGate":
        return cls(
            gate_id=d.get("gate_id", ""),
            action_kind=d.get("action_kind", ""),
            candidate=dict(d.get("candidate") or {}),
            status=d.get("status", ""),
            review_rationale=_rationale_from_dict(d.get("review_rationale")),
            created_utc=d.get("created_utc", ""),
            updated_utc=d.get("updated_utc", ""),
        )


# ----- Phase B: Audit ledger model -----

@dataclass
class LinkedProjectRoutineAction:
    """Link to project, routine, contract, outcome."""
    project_id: str = ""
    routine_id: str = ""
    contract_id: str = ""
    outcome_id: str = ""
    run_id: str = ""
    plan_ref: str = ""


@dataclass
class AuthorityTierRef:
    """Reference to authority tier used for this action."""
    tier_id: str = ""
    name: str = ""


@dataclass
class ApprovalChainEntry:
    """One entry in the approval chain."""
    step_index: int = 0
    decision: str = ""   # approved | rejected | deferred
    timestamp_utc: str = ""
    note: str = ""
    operator_id: str = ""


@dataclass
class OperatorSignOff:
    """Operator sign-off for a sensitive action."""
    operator_id: str = ""
    timestamp_utc: str = ""
    decision: str = ""   # approved | rejected | deferred
    rationale: str = ""
    authority_tier_id: str = ""


@dataclass
class ExecutionResult:
    """Result of executing the sensitive action."""
    executed_utc: str = ""
    outcome: str = ""   # success | partial | failed | blocked | skipped
    outcome_detail: str = ""
    artifact_refs: list[str] = field(default_factory=list)
    run_id: str = ""


@dataclass
class RollbackRecoveryNote:
    """Note for rollback or recovery if applied."""
    applied: bool = False
    timestamp_utc: str = ""
    note: str = ""
    recovery_action: str = ""   # rollback | compensate | manual


@dataclass
class VerificationOutcome:
    """Outcome of post-action verification."""
    verified: bool = False
    timestamp_utc: str = ""
    kind: str = ""
    note: str = ""


@dataclass
class AuditLedgerEntry:
    """One append-only audit ledger entry for a high-trust operation."""
    entry_id: str = ""
    gate_id: str = ""
    action_kind: str = ""   # commit | send | apply
    linked: LinkedProjectRoutineAction | None = None
    authority_tier: AuthorityTierRef | None = None
    approval_chain: list[ApprovalChainEntry] = field(default_factory=list)
    sign_off: OperatorSignOff | None = None
    execution_result: ExecutionResult | None = None
    rollback_recovery: RollbackRecoveryNote | None = None
    verification: VerificationOutcome | None = None
    created_utc: str = ""
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "gate_id": self.gate_id,
            "action_kind": self.action_kind,
            "linked": _linked_to_dict(self.linked),
            "authority_tier": _tier_ref_to_dict(self.authority_tier),
            "approval_chain": [_approval_entry_to_dict(e) for e in self.approval_chain],
            "sign_off": _sign_off_ledger_to_dict(self.sign_off),
            "execution_result": _exec_result_to_dict(self.execution_result),
            "rollback_recovery": _rollback_to_dict(self.rollback_recovery),
            "verification": _verification_outcome_to_dict(self.verification),
            "created_utc": self.created_utc,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AuditLedgerEntry":
        return cls(
            entry_id=d.get("entry_id", ""),
            gate_id=d.get("gate_id", ""),
            action_kind=d.get("action_kind", ""),
            linked=_linked_from_dict(d.get("linked")),
            authority_tier=_tier_ref_from_dict(d.get("authority_tier")),
            approval_chain=[_approval_entry_from_dict(e) for e in d.get("approval_chain") or []],
            sign_off=_sign_off_ledger_from_dict(d.get("sign_off")),
            execution_result=_exec_result_from_dict(d.get("execution_result")),
            rollback_recovery=_rollback_from_dict(d.get("rollback_recovery")),
            verification=_verification_outcome_from_dict(d.get("verification")),
            created_utc=d.get("created_utc", ""),
            label=d.get("label", ""),
        )


# ----- M35L.1 Audit summaries + trust review packs -----

class AuditSummaryScope(str, Enum):
    """Scope for an audit summary."""
    PROJECT = "project"
    ROUTINE = "routine"
    AUTHORITY_TIER = "authority_tier"


@dataclass
class AuditSummary:
    """Aggregate summary of audit ledger entries by project, routine, or authority tier."""
    scope: str = ""   # project | routine | authority_tier
    scope_value: str = ""   # project_id, routine_id, or tier_id
    period_start_utc: str = ""
    period_end_utc: str = ""
    total_entries: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    deferred_count: int = 0
    by_action_kind: dict[str, int] = field(default_factory=dict)   # commit, send, apply
    execution_success_count: int = 0
    execution_failed_count: int = 0
    execution_blocked_count: int = 0
    rollback_count: int = 0
    recent_entry_ids: list[str] = field(default_factory=list)
    generated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "scope_value": self.scope_value,
            "period_start_utc": self.period_start_utc,
            "period_end_utc": self.period_end_utc,
            "total_entries": self.total_entries,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "deferred_count": self.deferred_count,
            "by_action_kind": dict(self.by_action_kind),
            "execution_success_count": self.execution_success_count,
            "execution_failed_count": self.execution_failed_count,
            "execution_blocked_count": self.execution_blocked_count,
            "rollback_count": self.rollback_count,
            "recent_entry_ids": list(self.recent_entry_ids),
            "generated_at_utc": self.generated_at_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AuditSummary":
        return cls(
            scope=d.get("scope", ""),
            scope_value=d.get("scope_value", ""),
            period_start_utc=d.get("period_start_utc", ""),
            period_end_utc=d.get("period_end_utc", ""),
            total_entries=int(d.get("total_entries", 0)),
            approved_count=int(d.get("approved_count", 0)),
            rejected_count=int(d.get("rejected_count", 0)),
            deferred_count=int(d.get("deferred_count", 0)),
            by_action_kind=dict(d.get("by_action_kind") or {}),
            execution_success_count=int(d.get("execution_success_count", 0)),
            execution_failed_count=int(d.get("execution_failed_count", 0)),
            execution_blocked_count=int(d.get("execution_blocked_count", 0)),
            rollback_count=int(d.get("rollback_count", 0)),
            recent_entry_ids=list(d.get("recent_entry_ids") or []),
            generated_at_utc=d.get("generated_at_utc", ""),
        )


@dataclass
class TrustReviewPack:
    """M35L.1: Trust review pack for periodic high-trust operator mode review."""
    pack_id: str = ""
    generated_at_utc: str = ""
    period_description: str = ""   # e.g. "last 7 days", "last 30 days"
    audit_summaries: list[AuditSummary] = field(default_factory=list)
    pending_gate_ids: list[str] = field(default_factory=list)
    pending_count: int = 0
    recent_signed_off_gate_ids: list[str] = field(default_factory=list)
    anomaly_entry_ids: list[str] = field(default_factory=list)
    next_recommended_action: str = ""
    for_operator_mode: bool = True
    label: str = ""   # e.g. "High-trust operator mode review"

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "generated_at_utc": self.generated_at_utc,
            "period_description": self.period_description,
            "audit_summaries": [s.to_dict() for s in self.audit_summaries],
            "pending_gate_ids": list(self.pending_gate_ids),
            "pending_count": self.pending_count,
            "recent_signed_off_gate_ids": list(self.recent_signed_off_gate_ids),
            "anomaly_entry_ids": list(self.anomaly_entry_ids),
            "next_recommended_action": self.next_recommended_action,
            "for_operator_mode": self.for_operator_mode,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TrustReviewPack":
        return cls(
            pack_id=d.get("pack_id", ""),
            generated_at_utc=d.get("generated_at_utc", ""),
            period_description=d.get("period_description", ""),
            audit_summaries=[AuditSummary.from_dict(s) for s in d.get("audit_summaries") or []],
            pending_gate_ids=list(d.get("pending_gate_ids") or []),
            pending_count=int(d.get("pending_count", 0)),
            recent_signed_off_gate_ids=list(d.get("recent_signed_off_gate_ids") or []),
            anomaly_entry_ids=list(d.get("anomaly_entry_ids") or []),
            next_recommended_action=d.get("next_recommended_action", ""),
            for_operator_mode=bool(d.get("for_operator_mode", True)),
            label=d.get("label", ""),
        )


# ----- Helpers for serialization -----

def _sign_off_to_dict(o: SignOffRequirement | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {
        "required": o.required,
        "authority_tier_id": o.authority_tier_id,
        "contract_ref": o.contract_ref,
        "scope_note": o.scope_note,
    }


def _blocked_to_dict(o: BlockedGateReason | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {"code": o.code, "detail": o.detail, "source_ref": o.source_ref}


def _verification_to_dict(o: PostActionVerificationRequirement | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {
        "required": o.required,
        "kind": o.kind,
        "target_ref": o.target_ref,
        "note": o.note,
    }


def _rationale_to_dict(o: ReviewRationale | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {
        "decision": o.decision,
        "rationale": o.rationale,
        "operator_id": o.operator_id,
        "timestamp_utc": o.timestamp_utc,
    }


def _rationale_from_dict(d: dict[str, Any] | None) -> ReviewRationale | None:
    if not d:
        return None
    return ReviewRationale(
        decision=d.get("decision", ""),
        rationale=d.get("rationale", ""),
        operator_id=d.get("operator_id", ""),
        timestamp_utc=d.get("timestamp_utc", ""),
    )


def _linked_to_dict(o: LinkedProjectRoutineAction | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {
        "project_id": o.project_id,
        "routine_id": o.routine_id,
        "contract_id": o.contract_id,
        "outcome_id": o.outcome_id,
        "run_id": o.run_id,
        "plan_ref": o.plan_ref,
    }


def _linked_from_dict(d: dict[str, Any] | None) -> LinkedProjectRoutineAction | None:
    if not d:
        return None
    return LinkedProjectRoutineAction(
        project_id=d.get("project_id", ""),
        routine_id=d.get("routine_id", ""),
        contract_id=d.get("contract_id", ""),
        outcome_id=d.get("outcome_id", ""),
        run_id=d.get("run_id", ""),
        plan_ref=d.get("plan_ref", ""),
    )


def _tier_ref_to_dict(o: AuthorityTierRef | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {"tier_id": o.tier_id, "name": o.name}


def _tier_ref_from_dict(d: dict[str, Any] | None) -> AuthorityTierRef | None:
    if not d:
        return None
    return AuthorityTierRef(tier_id=d.get("tier_id", ""), name=d.get("name", ""))


def _approval_entry_to_dict(o: ApprovalChainEntry) -> dict[str, Any]:
    return {
        "step_index": o.step_index,
        "decision": o.decision,
        "timestamp_utc": o.timestamp_utc,
        "note": o.note,
        "operator_id": o.operator_id,
    }


def _approval_entry_from_dict(d: dict[str, Any]) -> ApprovalChainEntry:
    return ApprovalChainEntry(
        step_index=int(d.get("step_index", 0)),
        decision=d.get("decision", ""),
        timestamp_utc=d.get("timestamp_utc", ""),
        note=d.get("note", ""),
        operator_id=d.get("operator_id", ""),
    )


def _sign_off_ledger_to_dict(o: OperatorSignOff | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {
        "operator_id": o.operator_id,
        "timestamp_utc": o.timestamp_utc,
        "decision": o.decision,
        "rationale": o.rationale,
        "authority_tier_id": o.authority_tier_id,
    }


def _sign_off_ledger_from_dict(d: dict[str, Any] | None) -> OperatorSignOff | None:
    if not d:
        return None
    return OperatorSignOff(
        operator_id=d.get("operator_id", ""),
        timestamp_utc=d.get("timestamp_utc", ""),
        decision=d.get("decision", ""),
        rationale=d.get("rationale", ""),
        authority_tier_id=d.get("authority_tier_id", ""),
    )


def _exec_result_to_dict(o: ExecutionResult | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {
        "executed_utc": o.executed_utc,
        "outcome": o.outcome,
        "outcome_detail": o.outcome_detail,
        "artifact_refs": list(o.artifact_refs),
        "run_id": o.run_id,
    }


def _exec_result_from_dict(d: dict[str, Any] | None) -> ExecutionResult | None:
    if not d:
        return None
    return ExecutionResult(
        executed_utc=d.get("executed_utc", ""),
        outcome=d.get("outcome", ""),
        outcome_detail=d.get("outcome_detail", ""),
        artifact_refs=list(d.get("artifact_refs") or []),
        run_id=d.get("run_id", ""),
    )


def _rollback_to_dict(o: RollbackRecoveryNote | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {
        "applied": o.applied,
        "timestamp_utc": o.timestamp_utc,
        "note": o.note,
        "recovery_action": o.recovery_action,
    }


def _rollback_from_dict(d: dict[str, Any] | None) -> RollbackRecoveryNote | None:
    if not d:
        return None
    return RollbackRecoveryNote(
        applied=bool(d.get("applied")),
        timestamp_utc=d.get("timestamp_utc", ""),
        note=d.get("note", ""),
        recovery_action=d.get("recovery_action", ""),
    )


def _verification_outcome_to_dict(o: VerificationOutcome | None) -> dict[str, Any]:
    if o is None:
        return {}
    return {
        "verified": o.verified,
        "timestamp_utc": o.timestamp_utc,
        "kind": o.kind,
        "note": o.note,
    }


def _verification_outcome_from_dict(d: dict[str, Any] | None) -> VerificationOutcome | None:
    if not d:
        return None
    return VerificationOutcome(
        verified=bool(d.get("verified")),
        timestamp_utc=d.get("timestamp_utc", ""),
        kind=d.get("kind", ""),
        note=d.get("note", ""),
    )
