"""
M36I–M36L: Change since last session — what changed since last active session / shutdown.
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

from workflow_dataset.continuity_engine.models import ChangeSinceLastSession
from workflow_dataset.continuity_engine.store import get_last_session_end_utc


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_changes_since_last_session(
    repo_root: Path | str | None = None,
    queue_limit: int = 50,
    automation_limit: int = 20,
) -> ChangeSinceLastSession:
    """Build what changed since last session (from stored last_session_end or last shutdown)."""
    root = _root(repo_root)
    now = utc_now_iso()
    last_end = get_last_session_end_utc(root)
    out = ChangeSinceLastSession(
        last_session_end_utc=last_end,
        generated_at_utc=now,
        summary_lines=[],
        has_changes=False,
    )
    if not last_end:
        out.summary_lines.append("No previous session end recorded. Run 'continuity shutdown' at end of day to record.")
        return out

    # Queue: collect current queue; we don't have "queue at last_end" so we report current pending counts as "since last" context
    try:
        from workflow_dataset.unified_queue import build_unified_queue
        items = build_unified_queue(repo_root=root, limit=queue_limit)
        out.queue_items_added = len(items)
        out.summary_lines.append(f"Queue: {len(items)} pending item(s) now.")
    except Exception:
        out.summary_lines.append("Queue: (unavailable)")

    # Automation outcomes since last session (recent automation inbox items)
    try:
        from workflow_dataset.automation_inbox import build_automation_inbox
        inbox = build_automation_inbox(repo_root=root, status="", limit=automation_limit)
        for i in inbox[:15]:
            if i.created_at and i.created_at >= last_end[:19]:
                out.automation_outcomes.append(f"{i.kind}: {(i.summary or i.item_id)[:50]}")
        if out.automation_outcomes:
            out.has_changes = True
    except Exception:
        pass

    # Urgent approvals (from review studio inbox)
    try:
        from workflow_dataset.review_studio.inbox import build_inbox
        inbox = build_inbox(repo_root=root, status="pending", limit=20)
        for i in inbox:
            if i.kind == "approval_queue" and (i.priority or "").lower() in ("high", "urgent"):
                out.approvals_urgent.append(i.source_ref or i.item_id)
        if out.approvals_urgent:
            out.has_changes = True
            out.summary_lines.append(f"Urgent approvals: {len(out.approvals_urgent)}")
    except Exception:
        pass

    if not out.summary_lines and not out.has_changes:
        out.summary_lines.append("No significant changes since last session.")
    elif out.has_changes:
        out.summary_lines.insert(0, "Changes since last session:")
    return out
