"""
M35I–M35L: Gate + ledger flows — stage candidate, review (approve/reject/defer),
record execution result, record rollback/recovery, query ledger history.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

from workflow_dataset.sensitive_gates.models import (
    SensitiveActionGate,
    SensitiveActionKind,
    CommitCandidate,
    SendCandidate,
    ApplyCandidate,
    SignOffRequirement,
    ReviewRationale,
    BlockedGateReason,
    PostActionVerificationRequirement,
    AuditLedgerEntry,
    LinkedProjectRoutineAction,
    AuthorityTierRef,
    ApprovalChainEntry,
    OperatorSignOff,
    ExecutionResult,
    RollbackRecoveryNote,
    VerificationOutcome,
)
from workflow_dataset.sensitive_gates.store import (
    load_gates,
    upsert_gate,
    get_gate,
    append_ledger_entry,
    load_ledger_entries,
    ledger_by_project,
    ledger_by_gate_id,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def stage_candidate(
    action_kind: str,
    label: str,
    target_ref: str = "",
    plan_ref: str = "",
    run_id: str = "",
    project_id: str = "",
    routine_id: str = "",
    contract_id: str = "",
    sign_off_required: bool = True,
    authority_tier_id: str = "commit_or_send_candidate",
    contract_ref: str = "",
    blocked_code: str = "",
    blocked_detail: str = "",
    verification_required: bool = False,
    verification_kind: str = "",
    repo_root: Path | str | None = None,
) -> SensitiveActionGate:
    """Stage a sensitive action candidate and create a pending gate."""
    root = _repo_root(repo_root)
    now = utc_now_iso()
    gate_id = stable_id("gate", action_kind, label, now, prefix="gate_")

    sign_off = SignOffRequirement(
        required=sign_off_required,
        authority_tier_id=authority_tier_id,
        contract_ref=contract_ref or contract_id,
        scope_note="Explicit approval required for " + action_kind,
    ) if sign_off_required else None

    blocked = None
    if blocked_code or blocked_detail:
        blocked = BlockedGateReason(code=blocked_code or "other", detail=blocked_detail, source_ref=contract_ref or "")

    verification = None
    if verification_required:
        verification = PostActionVerificationRequirement(
            required=True,
            kind=verification_kind or "artifact_exists",
            target_ref=target_ref,
            note="Verify after execution",
        )

    candidate_dict: dict[str, Any]
    if action_kind == SensitiveActionKind.COMMIT.value:
        c = CommitCandidate(
            candidate_id=stable_id("cand", gate_id, prefix="cand_"),
            label=label,
            target_ref=target_ref,
            plan_ref=plan_ref,
            run_id=run_id,
            sign_off_requirement=sign_off,
            blocked_reason=blocked,
            verification_requirement=verification,
            created_utc=now,
            project_id=project_id,
            routine_id=routine_id,
            contract_id=contract_id,
        )
        candidate_dict = c.to_dict()
    elif action_kind == SensitiveActionKind.SEND.value:
        c = SendCandidate(
            candidate_id=stable_id("cand", gate_id, prefix="cand_"),
            label=label,
            target_ref=target_ref,
            plan_ref=plan_ref,
            run_id=run_id,
            sign_off_requirement=sign_off,
            blocked_reason=blocked,
            verification_requirement=verification,
            created_utc=now,
            project_id=project_id,
            routine_id=routine_id,
            contract_id=contract_id,
        )
        candidate_dict = c.to_dict()
    else:
        c = ApplyCandidate(
            candidate_id=stable_id("cand", gate_id, prefix="cand_"),
            label=label,
            target_ref=target_ref,
            plan_ref=plan_ref,
            run_id=run_id,
            sign_off_requirement=sign_off,
            blocked_reason=blocked,
            verification_requirement=verification,
            created_utc=now,
            project_id=project_id,
            routine_id=routine_id,
            contract_id=contract_id,
        )
        candidate_dict = c.to_dict()

    gate = SensitiveActionGate(
        gate_id=gate_id,
        action_kind=action_kind,
        candidate=candidate_dict,
        status="pending",
        created_utc=now,
        updated_utc=now,
    )
    upsert_gate(gate, root)
    return gate


def review_candidate(
    gate_id: str,
    decision: str,
    rationale: str = "",
    operator_id: str = "",
    authority_tier_id: str = "",
    append_to_ledger: bool = True,
    repo_root: Path | str | None = None,
) -> SensitiveActionGate | None:
    """Approve, reject, or defer a gate; record rationale; optionally append to ledger."""
    root = _repo_root(repo_root)
    gate = get_gate(gate_id, root)
    if not gate:
        return None
    now = utc_now_iso()
    gate.review_rationale = ReviewRationale(
        decision=decision,
        rationale=rationale,
        operator_id=operator_id,
        timestamp_utc=now,
    )
    gate.status = decision
    gate.updated_utc = now
    upsert_gate(gate, root)

    if append_to_ledger:
        linked = LinkedProjectRoutineAction(
            project_id=gate.candidate.get("project_id", ""),
            routine_id=gate.candidate.get("routine_id", ""),
            contract_id=gate.candidate.get("contract_id", ""),
            run_id=gate.candidate.get("run_id", ""),
            plan_ref=gate.candidate.get("plan_ref", ""),
        )
        sign_off = OperatorSignOff(
            operator_id=operator_id,
            timestamp_utc=now,
            decision=decision,
            rationale=rationale,
            authority_tier_id=authority_tier_id or "commit_or_send_candidate",
        )
        entry = AuditLedgerEntry(
            entry_id=stable_id("audit", gate_id, now, prefix="audit_"),
            gate_id=gate_id,
            action_kind=gate.action_kind,
            linked=linked,
            authority_tier=AuthorityTierRef(tier_id=authority_tier_id, name=""),
            approval_chain=[ApprovalChainEntry(step_index=0, decision=decision, timestamp_utc=now, note=rationale, operator_id=operator_id)],
            sign_off=sign_off,
            created_utc=now,
            label=gate.candidate.get("label", gate_id),
        )
        append_ledger_entry(entry, root)

    return gate


def record_execution_result(
    gate_id: str,
    outcome: str,
    outcome_detail: str = "",
    artifact_refs: list[str] | None = None,
    run_id: str = "",
    repo_root: Path | str | None = None,
) -> AuditLedgerEntry | None:
    """Append a ledger entry recording execution result for an approved gate."""
    root = _repo_root(repo_root)
    gate = get_gate(gate_id, root)
    if not gate:
        return None
    now = utc_now_iso()
    linked = LinkedProjectRoutineAction(
        project_id=gate.candidate.get("project_id", ""),
        routine_id=gate.candidate.get("routine_id", ""),
        contract_id=gate.candidate.get("contract_id", ""),
        run_id=run_id or gate.candidate.get("run_id", ""),
        plan_ref=gate.candidate.get("plan_ref", ""),
    )
    exec_result = ExecutionResult(
        executed_utc=now,
        outcome=outcome,
        outcome_detail=outcome_detail,
        artifact_refs=artifact_refs or [],
        run_id=run_id or gate.candidate.get("run_id", ""),
    )
    entry = AuditLedgerEntry(
        entry_id=stable_id("audit", gate_id, "exec", now, prefix="audit_"),
        gate_id=gate_id,
        action_kind=gate.action_kind,
        linked=linked,
        sign_off=gate.review_rationale and OperatorSignOff(
            decision=gate.review_rationale.decision,
            rationale=gate.review_rationale.rationale,
            timestamp_utc=gate.review_rationale.timestamp_utc,
            operator_id=gate.review_rationale.operator_id,
        ),
        execution_result=exec_result,
        created_utc=now,
        label=gate.candidate.get("label", gate_id),
    )
    append_ledger_entry(entry, root)
    return entry


def record_rollback_recovery(
    gate_id: str,
    note: str,
    recovery_action: str = "rollback",
    repo_root: Path | str | None = None,
) -> AuditLedgerEntry | None:
    """Append a ledger entry with rollback/recovery note."""
    root = _repo_root(repo_root)
    gate = get_gate(gate_id, root)
    if not gate:
        return None
    now = utc_now_iso()
    rollback = RollbackRecoveryNote(applied=True, timestamp_utc=now, note=note, recovery_action=recovery_action)
    linked = LinkedProjectRoutineAction(
        project_id=gate.candidate.get("project_id", ""),
        routine_id=gate.candidate.get("routine_id", ""),
        contract_id=gate.candidate.get("contract_id", ""),
        run_id=gate.candidate.get("run_id", ""),
        plan_ref=gate.candidate.get("plan_ref", ""),
    )
    entry = AuditLedgerEntry(
        entry_id=stable_id("audit", gate_id, "rollback", now, prefix="audit_"),
        gate_id=gate_id,
        action_kind=gate.action_kind,
        linked=linked,
        rollback_recovery=rollback,
        created_utc=now,
        label=gate.candidate.get("label", gate_id) + " (rollback/recovery)",
    )
    append_ledger_entry(entry, root)
    return entry


def query_ledger_history(
    repo_root: Path | str | None = None,
    project_id: str | None = None,
    gate_id: str | None = None,
    limit: int = 100,
) -> list[AuditLedgerEntry]:
    """Query ledger: by project_id, by gate_id, or full history."""
    root = _repo_root(repo_root)
    if gate_id:
        return ledger_by_gate_id(gate_id, root)
    if project_id:
        return ledger_by_project(project_id, root, limit=limit)
    return load_ledger_entries(root, limit=limit)
