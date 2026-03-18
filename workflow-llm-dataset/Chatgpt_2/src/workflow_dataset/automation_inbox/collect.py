"""
M34I–M34L: Collect automation results from background runs into automation inbox items.
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

from workflow_dataset.automation_inbox.models import (
    AutomationInboxItem,
    ITEM_AUTOMATION_RESULT,
    ITEM_BLOCKED_AUTOMATION,
    ITEM_BACKGROUND_RESULT_SUMMARY,
    ITEM_FAILED_SUPPRESSED,
    ITEM_FOLLOW_UP_RECOMMENDATION,
    STATUS_PENDING,
)
from workflow_dataset.automation_inbox.store import get_latest_decision, load_operator_notes


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def collect_from_background_runs(
    repo_root: Path | str | None = None,
    status_filter: str | None = None,
    limit: int = 80,
    include_decided: bool = False,
) -> list[AutomationInboxItem]:
    """
    Build automation inbox items from background_run: completed, blocked, failed, suppressed.
    If include_decided is False, items that have a decision (accept/archive/dismiss/escalate) are excluded.
    """
    root = _repo_root(repo_root)
    items: list[AutomationInboxItem] = []

    try:
        from workflow_dataset.background_run.store import list_runs, load_run
    except Exception:
        return items

    runs = list_runs(limit=limit, status_filter=status_filter, repo_root=root)
    notes = load_operator_notes(root)

    for r in runs:
        run_id = r.get("run_id", "")
        status = r.get("status", "")
        automation_id = r.get("automation_id", "")
        plan_ref = r.get("plan_ref", "")
        ts = r.get("timestamp_start", "") or r.get("timestamp_end", "") or utc_now_iso()
        outcome = (r.get("outcome_summary") or "")[:200]

        if not include_decided:
            item_id = stable_id("auto_inbox", run_id, prefix="auto_")
            dec = get_latest_decision(item_id, root)
            if dec:
                continue

        item_id = stable_id("auto_inbox", run_id, prefix="auto_")

        if status == "blocked":
            br = load_run(run_id, root) if run_id else None
            failure_code = ""
            handoff = False
            if br:
                failure_code = (br.failure_retry.failure_code or "") if br.failure_retry else ""
                handoff = getattr(br.failure_retry, "handoff_to_review", False) if br.failure_retry else False
            items.append(AutomationInboxItem(
                item_id=item_id,
                kind=ITEM_BLOCKED_AUTOMATION,
                status=STATUS_PENDING,
                summary=f"Blocked: {run_id} — {(outcome or 'no summary')[:60]}",
                created_at=ts[:19] if ts else utc_now_iso()[:19],
                priority="high",
                run_id=run_id,
                automation_id=automation_id,
                plan_ref=plan_ref,
                outcome_summary=outcome,
                failure_code=failure_code,
                entity_refs={"run_id": run_id, "automation_id": automation_id},
                source_ref=run_id,
                operator_notes=notes.get(item_id, ""),
            ))
        elif status in ("failed", "suppressed"):
            br = load_run(run_id, root) if run_id else None
            reason = ""
            failure_code = ""
            policy_notes: list[str] = []
            if br:
                if br.failure_retry:
                    reason = br.failure_retry.failure_reason or ""
                    failure_code = br.failure_retry.failure_code or ""
                policy_notes = list(getattr(br, "policy_notes", []) or [])
            items.append(AutomationInboxItem(
                item_id=item_id,
                kind=ITEM_FAILED_SUPPRESSED,
                status=STATUS_PENDING,
                summary=f"{status.capitalize()}: {run_id} — {(reason or outcome or '')[:60]}",
                created_at=ts[:19] if ts else utc_now_iso()[:19],
                priority="high" if status == "failed" else "medium",
                run_id=run_id,
                automation_id=automation_id,
                plan_ref=plan_ref,
                outcome_summary=outcome,
                failure_code=failure_code,
                entity_refs={"run_id": run_id, "automation_id": automation_id},
                source_ref=run_id,
                operator_notes=notes.get(item_id, ""),
            ))
        elif status == "completed":
            items.append(AutomationInboxItem(
                item_id=item_id,
                kind=ITEM_AUTOMATION_RESULT,
                status=STATUS_PENDING,
                summary=f"Completed: {run_id} — {(outcome or 'ok')[:60]}",
                created_at=ts[:19] if ts else utc_now_iso()[:19],
                priority="low",
                run_id=run_id,
                automation_id=automation_id,
                plan_ref=plan_ref,
                outcome_summary=outcome,
                entity_refs={"run_id": run_id, "automation_id": automation_id},
                source_ref=run_id,
                operator_notes=notes.get(item_id, ""),
            ))

    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda i: (priority_order.get(i.priority, 2), i.created_at or ""), reverse=True)
    return items[:limit]


def build_automation_inbox(
    repo_root: Path | str | None = None,
    status: str = "pending",
    limit: int = 100,
) -> list[AutomationInboxItem]:
    """
    Build full automation inbox: items from background runs, excluding those already decided
    unless status is empty. status='pending' returns only items with no decision (or not yet decided).
    """
    root = _repo_root(repo_root)
    items = collect_from_background_runs(repo_root=root, limit=limit, include_decided=(status == ""))
    if status:
        # Filter to pending (no decision recorded)
        decided_ids = set()
        for i in items:
            dec = get_latest_decision(i.item_id, root)
            if dec:
                decided_ids.add(i.item_id)
        items = [i for i in items if i.item_id not in decided_ids]
    return items[:limit]
