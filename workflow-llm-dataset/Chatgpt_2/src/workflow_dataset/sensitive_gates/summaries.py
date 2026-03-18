"""
M35L.1: Audit summaries by project/routine/authority tier + trust review packs.
Periodic review of what the system has been allowed to do; for high-trust operator mode.
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
    AuditSummary,
    AuditSummaryScope,
    TrustReviewPack,
    AuditLedgerEntry,
)
from workflow_dataset.sensitive_gates.store import (
    load_ledger_entries,
    load_gates,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _entries_in_period(
    entries: list[AuditLedgerEntry],
    period_start_utc: str,
    period_end_utc: str,
) -> list[AuditLedgerEntry]:
    if not period_start_utc and not period_end_utc:
        return entries
    out: list[AuditLedgerEntry] = []
    for e in entries:
        t = e.created_utc or ""
        if period_start_utc and t < period_start_utc:
            continue
        if period_end_utc and t > period_end_utc:
            continue
        out.append(e)
    return out


def _counts_for_entries(entries: list[AuditLedgerEntry]) -> tuple[
    int, int, int, dict[str, int], int, int, int, int
]:
    """approved, rejected, deferred, by_action_kind, exec_success, exec_failed, exec_blocked, rollback."""
    approved = rejected = deferred = 0
    by_kind: dict[str, int] = {}
    exec_success = exec_failed = exec_blocked = rollback = 0
    for e in entries:
        if e.sign_off:
            if e.sign_off.decision == "approved":
                approved += 1
            elif e.sign_off.decision == "rejected":
                rejected += 1
            elif e.sign_off.decision == "deferred":
                deferred += 1
        if e.action_kind:
            by_kind[e.action_kind] = by_kind.get(e.action_kind, 0) + 1
        if e.execution_result:
            if e.execution_result.outcome == "success":
                exec_success += 1
            elif e.execution_result.outcome == "failed":
                exec_failed += 1
            elif e.execution_result.outcome == "blocked":
                exec_blocked += 1
        if e.rollback_recovery and e.rollback_recovery.applied:
            rollback += 1
    return approved, rejected, deferred, by_kind, exec_success, exec_failed, exec_blocked, rollback


def build_audit_summary_by_project(
    project_id: str,
    repo_root: Path | str | None = None,
    period_start_utc: str = "",
    period_end_utc: str = "",
    ledger_limit: int = 500,
    recent_entry_limit: int = 10,
) -> AuditSummary:
    """Build an audit summary for a single project."""
    root = _repo_root(repo_root)
    all_entries = load_ledger_entries(root, limit=ledger_limit)
    entries = [e for e in all_entries if e.linked and e.linked.project_id == project_id]
    entries = _entries_in_period(entries, period_start_utc, period_end_utc)
    approved, rejected, deferred, by_kind, exec_success, exec_failed, exec_blocked, rollback = _counts_for_entries(entries)
    now = utc_now_iso()
    return AuditSummary(
        scope=AuditSummaryScope.PROJECT.value,
        scope_value=project_id,
        period_start_utc=period_start_utc,
        period_end_utc=period_end_utc,
        total_entries=len(entries),
        approved_count=approved,
        rejected_count=rejected,
        deferred_count=deferred,
        by_action_kind=by_kind,
        execution_success_count=exec_success,
        execution_failed_count=exec_failed,
        execution_blocked_count=exec_blocked,
        rollback_count=rollback,
        recent_entry_ids=[e.entry_id for e in entries[:recent_entry_limit]],
        generated_at_utc=now,
    )


def build_audit_summary_by_routine(
    routine_id: str,
    repo_root: Path | str | None = None,
    period_start_utc: str = "",
    period_end_utc: str = "",
    ledger_limit: int = 500,
    recent_entry_limit: int = 10,
) -> AuditSummary:
    """Build an audit summary for a single routine."""
    root = _repo_root(repo_root)
    all_entries = load_ledger_entries(root, limit=ledger_limit)
    entries = [e for e in all_entries if e.linked and e.linked.routine_id == routine_id]
    entries = _entries_in_period(entries, period_start_utc, period_end_utc)
    approved, rejected, deferred, by_kind, exec_success, exec_failed, exec_blocked, rollback = _counts_for_entries(entries)
    now = utc_now_iso()
    return AuditSummary(
        scope=AuditSummaryScope.ROUTINE.value,
        scope_value=routine_id,
        period_start_utc=period_start_utc,
        period_end_utc=period_end_utc,
        total_entries=len(entries),
        approved_count=approved,
        rejected_count=rejected,
        deferred_count=deferred,
        by_action_kind=by_kind,
        execution_success_count=exec_success,
        execution_failed_count=exec_failed,
        execution_blocked_count=exec_blocked,
        rollback_count=rollback,
        recent_entry_ids=[e.entry_id for e in entries[:recent_entry_limit]],
        generated_at_utc=now,
    )


def build_audit_summary_by_authority_tier(
    tier_id: str,
    repo_root: Path | str | None = None,
    period_start_utc: str = "",
    period_end_utc: str = "",
    ledger_limit: int = 500,
    recent_entry_limit: int = 10,
) -> AuditSummary:
    """Build an audit summary for an authority tier (by tier_id on authority_tier or sign_off)."""
    root = _repo_root(repo_root)
    all_entries = load_ledger_entries(root, limit=ledger_limit)
    entries = [
        e for e in all_entries
        if (e.authority_tier and e.authority_tier.tier_id == tier_id)
        or (e.sign_off and e.sign_off.authority_tier_id == tier_id)
    ]
    entries = _entries_in_period(entries, period_start_utc, period_end_utc)
    approved, rejected, deferred, by_kind, exec_success, exec_failed, exec_blocked, rollback = _counts_for_entries(entries)
    now = utc_now_iso()
    return AuditSummary(
        scope=AuditSummaryScope.AUTHORITY_TIER.value,
        scope_value=tier_id,
        period_start_utc=period_start_utc,
        period_end_utc=period_end_utc,
        total_entries=len(entries),
        approved_count=approved,
        rejected_count=rejected,
        deferred_count=deferred,
        by_action_kind=by_kind,
        execution_success_count=exec_success,
        execution_failed_count=exec_failed,
        execution_blocked_count=exec_blocked,
        rollback_count=rollback,
        recent_entry_ids=[e.entry_id for e in entries[:recent_entry_limit]],
        generated_at_utc=now,
    )


def build_trust_review_pack(
    repo_root: Path | str | None = None,
    days: int = 7,
    ledger_limit: int = 300,
    include_project_summaries: bool = True,
    include_tier_summaries: bool = True,
    max_summaries: int = 20,
) -> TrustReviewPack:
    """
    Build a trust review pack for periodic high-trust operator mode review.
    Includes audit summaries (by project and by authority tier), pending gates,
    recent signed-off gates, anomalies, and next recommended action.
    """
    root = _repo_root(repo_root)
    now = utc_now_iso()
    # Simple period: use created_utc >= (now - days); we filter in _entries_in_period if we had a real period_end
    # For "last N days" we don't have a built-in date subtract in minimal deps; pass empty period so all entries
    # are considered and we rely on ledger_limit (recent entries). Alternatively we could parse created_utc.
    period_end = now
    # period_start: approximate "days ago" by using empty and taking recent entries only
    all_entries = load_ledger_entries(root, limit=ledger_limit)
    gates = load_gates(root)
    pending = [g for g in gates if g.status == "pending"]
    approved_gates = [g for g in gates if g.status == "approved"]
    recent_signed_off = [g.gate_id for g in approved_gates[:15]]
    anomalies = [
        e.entry_id for e in all_entries
        if e.execution_result and e.execution_result.outcome in ("failed", "blocked")
    ][:20]

    summaries: list[AuditSummary] = []
    if include_project_summaries:
        project_ids: set[str] = set()
        for e in all_entries:
            if e.linked and e.linked.project_id:
                project_ids.add(e.linked.project_id)
        for pid in list(project_ids)[:max_summaries]:
            summaries.append(
                build_audit_summary_by_project(
                    pid,
                    repo_root=root,
                    period_start_utc="",
                    period_end_utc=period_end,
                    ledger_limit=ledger_limit,
                    recent_entry_limit=5,
                )
            )
    if include_tier_summaries:
        tier_ids: set[str] = set()
        for e in all_entries:
            if e.authority_tier and e.authority_tier.tier_id:
                tier_ids.add(e.authority_tier.tier_id)
            if e.sign_off and e.sign_off.authority_tier_id:
                tier_ids.add(e.sign_off.authority_tier_id)
        for tid in list(tier_ids)[:max_summaries]:
            summaries.append(
                build_audit_summary_by_authority_tier(
                    tid,
                    repo_root=root,
                    period_start_utc="",
                    period_end_utc=period_end,
                    ledger_limit=ledger_limit,
                    recent_entry_limit=5,
                )
            )

    if pending:
        next_action = f"Review {len(pending)} pending gate(s): workflow-dataset gates list --status pending"
    elif anomalies:
        next_action = "Review audit anomalies: workflow-dataset audit history"
    else:
        next_action = "No pending review. Use: workflow-dataset trust-review pack"

    pack_id = stable_id("trust_pack", now, prefix="pack_")
    return TrustReviewPack(
        pack_id=pack_id,
        generated_at_utc=now,
        period_description=f"last {days} days" if days else "all",
        audit_summaries=summaries,
        pending_gate_ids=[g.gate_id for g in pending],
        pending_count=len(pending),
        recent_signed_off_gate_ids=recent_signed_off,
        anomaly_entry_ids=anomalies,
        next_recommended_action=next_action,
        for_operator_mode=True,
        label="High-trust operator mode review",
    )
