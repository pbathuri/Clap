"""
M27E–M27H: Approval queue — enqueue proposals, approve/reject/defer, persist history.
M27H.1: Batch approval, prioritization, defer with reason/revisit.
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
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]

from workflow_dataset.supervised_loop.models import (
    ApprovalQueueItem,
    QueuedAction,
    OperatorPolicy,
    RISK_ORDER,
)
from workflow_dataset.supervised_loop.store import (
    load_queue,
    save_queue,
    append_queue_history,
    load_operator_policy,
)


def enqueue_proposal(
    action: QueuedAction,
    cycle_id: str = "",
    repo_root: Path | str | None = None,
) -> ApprovalQueueItem:
    """Add a proposed action to the queue as pending. Returns the new queue item."""
    items = load_queue(repo_root)
    qid = stable_id("q", action.action_id, utc_now_iso(), prefix="q_")
    item = ApprovalQueueItem(
        queue_id=qid,
        action=action,
        status="pending",
        cycle_id=cycle_id,
    )
    items.append(item)
    save_queue(items, repo_root)
    return item


def list_pending(repo_root: Path | str | None = None) -> list[ApprovalQueueItem]:
    """Return queue items with status pending."""
    return [q for q in load_queue(repo_root) if q.status == "pending"]


def _risk_index(risk_level: str) -> int:
    """Lower index = lower risk (for sort). Unknown -> 1 (medium)."""
    return RISK_ORDER.index(risk_level) if risk_level in RISK_ORDER else 1


def list_pending_sorted(
    repo_root: Path | str | None = None,
    policy: OperatorPolicy | None = None,
) -> list[ApprovalQueueItem]:
    """
    Return pending items sorted for clearer prioritization:
    1) Always-manual-review first (so operator sees them at top)
    2) Then by risk (low first, so low-risk can be batch-approved)
    3) Then by created_at (older first)
    """
    if policy is None:
        policy = load_operator_policy(repo_root)
    pending = list_pending(repo_root)

    def key(q: ApprovalQueueItem) -> tuple[int, int, str]:
        manual = 0 if policy.requires_manual_review(q.action) else 1
        risk = _risk_index(q.action.risk_level)
        created = q.action.created_at or ""
        return (manual, risk, created)

    return sorted(pending, key=key)


def get_item(queue_id: str, repo_root: Path | str | None = None) -> ApprovalQueueItem | None:
    """Return the queue item with the given queue_id."""
    for q in load_queue(repo_root):
        if q.queue_id == queue_id:
            return q
    return None


def decide(
    queue_id: str,
    decision: str,
    note: str = "",
    repo_root: Path | str | None = None,
    defer_reason: str = "",
    revisit_after: str = "",
) -> ApprovalQueueItem | None:
    """
    Set decision for a pending item: approve | reject | defer.
    For defer: optional defer_reason and revisit_after (ISO date) for safer revisit.
    Persists queue and appends to history. Returns updated item or None if not found/not pending.
    """
    items = load_queue(repo_root)
    for i, q in enumerate(items):
        if q.queue_id == queue_id and q.status == "pending":
            items[i] = ApprovalQueueItem(
                queue_id=q.queue_id,
                action=q.action,
                status=decision,
                decided_at=utc_now_iso(),
                decision_note=note,
                cycle_id=q.cycle_id,
                defer_reason=defer_reason if decision == "deferred" else "",
                revisit_after=revisit_after if decision == "deferred" else "",
            )
            save_queue(items, repo_root)
            append_queue_history(q.queue_id, decision, utc_now_iso(), note or defer_reason, repo_root)
            return items[i]
    return None


def approve(queue_id: str, note: str = "", repo_root: Path | str | None = None) -> ApprovalQueueItem | None:
    return decide(queue_id, "approved", note, repo_root)


def reject(queue_id: str, note: str = "", repo_root: Path | str | None = None) -> ApprovalQueueItem | None:
    return decide(queue_id, "rejected", note, repo_root)


def defer(
    queue_id: str,
    note: str = "",
    repo_root: Path | str | None = None,
    defer_reason: str = "",
    revisit_after: str = "",
) -> ApprovalQueueItem | None:
    """Defer with optional reason and revisit_after (ISO date) for safer revisit."""
    return decide(queue_id, "deferred", note, repo_root, defer_reason=defer_reason, revisit_after=revisit_after)


def list_deferred(repo_root: Path | str | None = None) -> list[ApprovalQueueItem]:
    """Return queue items with status deferred (for list-deferred / revisit)."""
    return [q for q in load_queue(repo_root) if q.status == "deferred"]


def revisit_deferred(queue_id: str, repo_root: Path | str | None = None) -> ApprovalQueueItem | None:
    """
    Move a deferred item back to pending. Clears defer_reason and revisit_after.
    Returns updated item or None if not found or not deferred.
    """
    items = load_queue(repo_root)
    for i, q in enumerate(items):
        if q.queue_id == queue_id and q.status == "deferred":
            items[i] = ApprovalQueueItem(
                queue_id=q.queue_id,
                action=q.action,
                status="pending",
                decided_at="",
                decision_note="",
                cycle_id=q.cycle_id,
                defer_reason="",
                revisit_after="",
            )
            save_queue(items, repo_root)
            append_queue_history(q.queue_id, "revisit", utc_now_iso(), "moved back to pending", repo_root)
            return items[i]
    return None


def approve_batch(
    max_risk: str = "low",
    run_after: bool = True,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Approve all pending items that are allowed by policy for batch approval:
    - risk_level <= max_risk (in RISK_ORDER)
    - not in policy.requires_manual_review(action)
    Then optionally execute each (run_after=True). Returns counts and per-item results.
    """
    policy = load_operator_policy(repo_root)
    if max_risk not in RISK_ORDER:
        max_risk = "low"
    pending = list_pending_sorted(repo_root, policy)
    approved_ids: list[str] = []
    executed: list[dict[str, Any]] = []
    skipped_manual: list[str] = []
    skipped_risk: list[str] = []

    for q in pending:
        if policy.requires_manual_review(q.action):
            skipped_manual.append(q.queue_id)
            continue
        if not policy.risk_within_batch_limit(q.action.risk_level):
            skipped_risk.append(q.queue_id)
            continue
        # Also respect max_risk parameter
        if _risk_index(q.action.risk_level) > _risk_index(max_risk):
            skipped_risk.append(q.queue_id)
            continue
        item = approve(q.queue_id, "batch", repo_root)
        if item:
            approved_ids.append(q.queue_id)
            if run_after:
                from workflow_dataset.supervised_loop.handoff import execute_approved
                result = execute_approved(q.queue_id, repo_root)
                executed.append({"queue_id": q.queue_id, "handoff_id": result.get("handoff_id"), "status": result.get("status"), "error": result.get("error", "")})

    return {
        "approved_count": len(approved_ids),
        "approved_ids": approved_ids,
        "executed": executed,
        "skipped_manual_review": skipped_manual,
        "skipped_risk": skipped_risk,
    }
