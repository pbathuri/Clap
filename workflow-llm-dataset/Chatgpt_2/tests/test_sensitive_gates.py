"""
M35I–M35L: Tests for sensitive action gates + audit ledger.
Gate creation, sign-off/reject/defer flows, ledger entry, project linkage, rollback note, blocked gate.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from workflow_dataset.sensitive_gates.models import (
    SensitiveActionKind,
    SensitiveActionGate,
    CommitCandidate,
    SignOffRequirement,
    ReviewRationale,
    BlockedGateReason,
    AuditLedgerEntry,
    LinkedProjectRoutineAction,
    ExecutionResult,
    RollbackRecoveryNote,
    AuditSummary,
    AuditSummaryScope,
    TrustReviewPack,
)
from workflow_dataset.sensitive_gates.store import (
    load_gates,
    save_gates,
    get_gate,
    upsert_gate,
    append_ledger_entry,
    load_ledger_entries,
    ledger_by_project,
)
from workflow_dataset.sensitive_gates.flows import (
    stage_candidate,
    review_candidate,
    record_execution_result,
    record_rollback_recovery,
    query_ledger_history,
)
from workflow_dataset.sensitive_gates.summaries import (
    build_audit_summary_by_project,
    build_audit_summary_by_routine,
    build_audit_summary_by_authority_tier,
    build_trust_review_pack,
)


def test_gate_creation(tmp_path: Path) -> None:
    """Stage a commit candidate creates a pending gate."""
    gate = stage_candidate(
        action_kind="commit",
        label="Commit docs to main",
        target_ref="main",
        project_id="founder_case_alpha",
        repo_root=tmp_path,
    )
    assert gate.gate_id.startswith("gate_")
    assert gate.action_kind == "commit"
    assert gate.status == "pending"
    assert gate.candidate.get("label") == "Commit docs to main"
    assert gate.candidate.get("project_id") == "founder_case_alpha"

    gates = load_gates(tmp_path)
    assert len(gates) == 1
    assert gates[0].gate_id == gate.gate_id


def test_sign_off_approve_flow(tmp_path: Path) -> None:
    """Approve gate records rationale and appends to ledger."""
    gate = stage_candidate(
        action_kind="send",
        label="Send weekly report",
        target_ref="stakeholders",
        repo_root=tmp_path,
    )
    updated = review_candidate(
        gate.gate_id,
        "approved",
        rationale="Reviewed content; safe to send.",
        repo_root=tmp_path,
    )
    assert updated is not None
    assert updated.status == "approved"
    assert updated.review_rationale and updated.review_rationale.decision == "approved"
    assert "safe to send" in (updated.review_rationale.rationale or "")

    entries = load_ledger_entries(tmp_path, limit=10)
    assert len(entries) >= 1
    assert any(e.gate_id == gate.gate_id for e in entries)
    entry = next(e for e in entries if e.gate_id == gate.gate_id)
    assert entry.sign_off and entry.sign_off.decision == "approved"


def test_reject_defer_flow(tmp_path: Path) -> None:
    """Reject and defer record decision and ledger."""
    gate = stage_candidate(
        action_kind="apply",
        label="Apply config to prod",
        target_ref="prod",
        repo_root=tmp_path,
    )
    review_candidate(gate.gate_id, "rejected", rationale="Not ready for prod", repo_root=tmp_path)
    g = get_gate(gate.gate_id, tmp_path)
    assert g and g.status == "rejected"

    gate2 = stage_candidate(
        action_kind="commit",
        label="Commit WIP",
        target_ref="feature",
        repo_root=tmp_path,
    )
    review_candidate(gate2.gate_id, "deferred", rationale="Will do after review", repo_root=tmp_path)
    g2 = get_gate(gate2.gate_id, tmp_path)
    assert g2 and g2.status == "deferred"


def test_audit_ledger_entry_creation(tmp_path: Path) -> None:
    """Approve creates ledger entry with sign-off and linked project."""
    gate = stage_candidate(
        action_kind="commit",
        label="Ship feature X",
        project_id="proj_alpha",
        routine_id="routine_daily",
        repo_root=tmp_path,
    )
    review_candidate(gate.gate_id, "approved", rationale="LGTM", repo_root=tmp_path)
    entries = query_ledger_history(repo_root=tmp_path, limit=5)
    assert len(entries) >= 1
    e = entries[0]
    assert e.gate_id == gate.gate_id
    assert e.linked and e.linked.project_id == "proj_alpha"
    assert e.linked.routine_id == "routine_daily"


def test_project_linkage(tmp_path: Path) -> None:
    """Ledger can be queried by project_id."""
    gate = stage_candidate(
        action_kind="commit",
        label="Commit A",
        project_id="founder_case_alpha",
        repo_root=tmp_path,
    )
    review_candidate(gate.gate_id, "approved", rationale="OK", repo_root=tmp_path)
    by_proj = ledger_by_project("founder_case_alpha", tmp_path)
    assert len(by_proj) >= 1
    assert all(e.linked and e.linked.project_id == "founder_case_alpha" for e in by_proj)


def test_rollback_recovery_note(tmp_path: Path) -> None:
    """record_rollback_recovery appends ledger entry with rollback note."""
    gate = stage_candidate(
        action_kind="apply",
        label="Apply migration",
        repo_root=tmp_path,
    )
    entry = record_rollback_recovery(
        gate.gate_id,
        note="Reverted due to failure in step 2",
        recovery_action="rollback",
        repo_root=tmp_path,
    )
    assert entry is not None
    assert entry.rollback_recovery and entry.rollback_recovery.applied
    assert "Reverted" in entry.rollback_recovery.note
    entries = load_ledger_entries(tmp_path, limit=5)
    assert any(e.rollback_recovery for e in entries)


def test_blocked_gate_behavior(tmp_path: Path) -> None:
    """Gate can be created with blocked reason."""
    gate = stage_candidate(
        action_kind="commit",
        label="Commit blocked",
        blocked_code="policy_denied",
        blocked_detail="Policy requires review",
        repo_root=tmp_path,
    )
    assert gate.candidate.get("blocked_reason", {}).get("code") == "policy_denied"
    assert "Policy requires review" in gate.candidate.get("blocked_reason", {}).get("detail", "")


def test_record_execution_result(tmp_path: Path) -> None:
    """record_execution_result appends ledger entry with outcome."""
    gate = stage_candidate(
        action_kind="send",
        label="Send report",
        repo_root=tmp_path,
    )
    review_candidate(gate.gate_id, "approved", rationale="OK", repo_root=tmp_path)
    entry = record_execution_result(
        gate.gate_id,
        outcome="success",
        outcome_detail="Delivered",
        artifact_refs=["report.pdf"],
        repo_root=tmp_path,
    )
    assert entry is not None
    assert entry.execution_result and entry.execution_result.outcome == "success"
    assert "report.pdf" in (entry.execution_result.artifact_refs or [])


def test_sensitive_action_gate_from_dict() -> None:
    """SensitiveActionGate round-trip to_dict/from_dict."""
    gate = SensitiveActionGate(
        gate_id="gate_abc",
        action_kind="commit",
        candidate={"label": "Test", "project_id": "p1"},
        status="pending",
        created_utc="2025-01-01T00:00:00Z",
        updated_utc="2025-01-01T00:00:00Z",
    )
    d = gate.to_dict()
    gate2 = SensitiveActionGate.from_dict(d)
    assert gate2.gate_id == gate.gate_id
    assert gate2.candidate.get("label") == "Test"


def test_audit_ledger_entry_from_dict() -> None:
    """AuditLedgerEntry round-trip to_dict/from_dict."""
    entry = AuditLedgerEntry(
        entry_id="audit_1",
        gate_id="gate_1",
        action_kind="commit",
        linked=LinkedProjectRoutineAction(project_id="p1", routine_id="r1"),
        execution_result=ExecutionResult(outcome="success", executed_utc="2025-01-01T00:00:00Z"),
        created_utc="2025-01-01T00:00:00Z",
        label="Commit docs",
    )
    d = entry.to_dict()
    entry2 = AuditLedgerEntry.from_dict(d)
    assert entry2.entry_id == entry.entry_id
    assert entry2.linked and entry2.linked.project_id == "p1"
    assert entry2.execution_result and entry2.execution_result.outcome == "success"


# ----- M35L.1 Audit summaries + trust review packs -----


def test_audit_summary_by_project(tmp_path: Path) -> None:
    """Audit summary by project aggregates ledger entries for that project."""
    gate = stage_candidate(
        action_kind="commit",
        label="Ship feature",
        project_id="proj_alpha",
        repo_root=tmp_path,
    )
    review_candidate(gate.gate_id, "approved", rationale="OK", repo_root=tmp_path)
    summary = build_audit_summary_by_project("proj_alpha", repo_root=tmp_path)
    assert summary.scope == AuditSummaryScope.PROJECT.value
    assert summary.scope_value == "proj_alpha"
    assert summary.total_entries >= 1
    assert summary.approved_count >= 1
    assert "commit" in summary.by_action_kind or summary.by_action_kind


def test_audit_summary_by_authority_tier(tmp_path: Path) -> None:
    """Audit summary by authority tier aggregates by tier."""
    gate = stage_candidate(
        action_kind="send",
        label="Send report",
        repo_root=tmp_path,
    )
    review_candidate(gate.gate_id, "approved", rationale="OK", repo_root=tmp_path)
    summary = build_audit_summary_by_authority_tier("commit_or_send_candidate", repo_root=tmp_path)
    assert summary.scope == AuditSummaryScope.AUTHORITY_TIER.value
    assert summary.scope_value == "commit_or_send_candidate"


def test_trust_review_pack(tmp_path: Path) -> None:
    """Trust review pack includes pending gates, summaries, anomalies, next action."""
    pack = build_trust_review_pack(repo_root=tmp_path, days=7)
    assert pack.pack_id.startswith("pack_")
    assert pack.generated_at_utc
    assert pack.period_description
    assert pack.for_operator_mode is True
    assert pack.next_recommended_action
    assert "pending" in pack.next_recommended_action.lower() or "review" in pack.next_recommended_action.lower() or "audit" in pack.next_recommended_action.lower() or "No pending" in pack.next_recommended_action


def test_audit_summary_roundtrip() -> None:
    """AuditSummary to_dict/from_dict round-trip."""
    s = AuditSummary(
        scope="project",
        scope_value="p1",
        total_entries=5,
        approved_count=3,
        by_action_kind={"commit": 2, "send": 1},
        generated_at_utc="2025-01-01T00:00:00Z",
    )
    d = s.to_dict()
    s2 = AuditSummary.from_dict(d)
    assert s2.scope_value == s.scope_value
    assert s2.total_entries == s.total_entries
    assert s2.by_action_kind == s.by_action_kind


def test_trust_review_pack_roundtrip() -> None:
    """TrustReviewPack to_dict/from_dict round-trip."""
    pack = TrustReviewPack(
        pack_id="pack_abc",
        generated_at_utc="2025-01-01T00:00:00Z",
        period_description="last 7 days",
        pending_gate_ids=["gate_1"],
        pending_count=1,
        next_recommended_action="Review 1 pending gate",
        label="High-trust operator mode review",
    )
    d = pack.to_dict()
    pack2 = TrustReviewPack.from_dict(d)
    assert pack2.pack_id == pack.pack_id
    assert pack2.pending_count == pack.pending_count
    assert pack2.next_recommended_action == pack.next_recommended_action
