"""
M36E–M36H: Collect actionable items from across subsystems into unified queue items.
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
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]

from workflow_dataset.unified_queue.models import (
    UnifiedQueueItem,
    SourceSubsystem,
    ActionabilityClass,
    RoutingTarget,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _collect_from_review_studio(repo_root: Path | str | None, limit: int) -> list[UnifiedQueueItem]:
    """Normalize intervention inbox items to UnifiedQueueItem."""
    items: list[UnifiedQueueItem] = []
    try:
        from workflow_dataset.review_studio.inbox import build_inbox
        root = _root(repo_root)
        inbox = build_inbox(repo_root=root, status="pending", limit=limit)
        for i in inbox:
            uq_id = stable_id("uq", "review_studio", i.item_id, prefix="uq_")
            actionability = ActionabilityClass.NEEDS_APPROVAL if i.kind == "approval_queue" else ActionabilityClass.NEEDS_REVIEW
            routing = RoutingTarget.REVIEW.value
            if i.kind == "blocked_run":
                routing = RoutingTarget.EXECUTOR.value
            project_id = (i.entity_refs or {}).get("project_id", "")
            items.append(UnifiedQueueItem(
                item_id=uq_id,
                source_subsystem=SourceSubsystem.REVIEW_STUDIO,
                source_ref=i.source_ref or i.item_id,
                actionability_class=actionability,
                priority=i.priority or "medium",
                urgency_score=0.8 if (i.priority or "").lower() in ("urgent", "high") else 0.5,
                routing_target=routing,
                state="pending",
                label=(i.summary or i.item_id)[:80],
                summary=i.summary or "",
                entity_refs=dict(i.entity_refs or {}),
                created_at=i.created_at or utc_now_iso(),
                project_id=project_id,
            ))
    except Exception:
        pass
    return items


def _collect_from_automation_inbox(repo_root: Path | str | None, limit: int) -> list[UnifiedQueueItem]:
    """Normalize automation inbox items to UnifiedQueueItem."""
    items: list[UnifiedQueueItem] = []
    try:
        from workflow_dataset.automation_inbox import build_automation_inbox
        root = _root(repo_root)
        inbox = build_automation_inbox(repo_root=root, status="pending", limit=limit)
        for i in inbox:
            uq_id = stable_id("uq", "automation_inbox", i.item_id, prefix="uq_")
            actionability = ActionabilityClass.BLOCKED if i.kind in ("blocked_automation", "failed_suppressed_automation") else ActionabilityClass.NEEDS_REVIEW
            items.append(UnifiedQueueItem(
                item_id=uq_id,
                source_subsystem=SourceSubsystem.AUTOMATION_INBOX,
                source_ref=i.source_ref or i.item_id,
                actionability_class=actionability,
                priority=i.priority or "medium",
                urgency_score=0.8 if i.kind in ("blocked_automation", "failed_suppressed_automation") else 0.5,
                routing_target=RoutingTarget.AUTOMATION_FOLLOW_UP.value,
                blocked_reason=i.failure_code or "",
                state="pending",
                label=(i.summary or i.item_id)[:80],
                summary=i.outcome_summary or i.summary or "",
                entity_refs={"run_id": i.run_id, "automation_id": i.automation_id, **i.entity_refs},
                created_at=i.created_at or utc_now_iso(),
                project_id=getattr(i, "project_id", "") or (i.entity_refs or {}).get("project_id", ""),
            ))
    except Exception:
        pass
    return items


def build_unified_queue(
    repo_root: Path | str | None = None,
    limit: int = 100,
    include_sections: bool = True,
) -> list[UnifiedQueueItem]:
    """
    Collect from review_studio and automation_inbox, normalize to UnifiedQueueItem.
    Dedupe by source_ref; section_id and mode_tags assigned in prioritize.
    """
    root = _root(repo_root)
    seen: set[str] = set()
    out: list[UnifiedQueueItem] = []
    for item in _collect_from_review_studio(root, limit) + _collect_from_automation_inbox(root, limit):
        key = f"{item.source_subsystem.value}:{item.source_ref}"
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out[:limit]
