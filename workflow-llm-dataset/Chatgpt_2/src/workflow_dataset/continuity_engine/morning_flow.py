"""
M36I–M36L: Morning entry flow — change since last, top queue, automations, approvals, stalled projects, first mode/action.
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

from workflow_dataset.continuity_engine.models import MorningEntryBrief, ChangeSinceLastSession
from workflow_dataset.continuity_engine.changes import build_changes_since_last_session
from workflow_dataset.continuity_engine.store import load_next_session_recommendation


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_morning_entry_flow(
    repo_root: Path | str | None = None,
    queue_limit: int = 20,
    automation_limit: int = 15,
) -> MorningEntryBrief:
    """Build morning entry flow: change since last, top queue, automations, approvals, stalled, first mode/action."""
    root = _root(repo_root)
    now = utc_now_iso()
    brief_id = stable_id("morning", now[:10], prefix="brief_")

    change = build_changes_since_last_session(repo_root=root, queue_limit=queue_limit, automation_limit=automation_limit)
    top_queue: list[dict[str, Any]] = []
    automation_lines: list[str] = []
    urgent_approvals: list[str] = []
    stalled_projects: list[str] = []
    first_mode = "startup"
    first_action = "Review inbox"
    first_command = "workflow-dataset inbox list"
    handoff_label = "Open inbox"
    handoff_command = "workflow-dataset inbox list"

    try:
        from workflow_dataset.unified_queue import build_unified_queue
        items = build_unified_queue(repo_root=root, limit=queue_limit)
        for i in items[:10]:
            top_queue.append({
                "item_id": getattr(i, "item_id", ""),
                "label": (getattr(i, "label", "") or getattr(i, "summary", "") or "")[:60],
                "source": i.source_subsystem.value if hasattr(i.source_subsystem, "value") else str(i.source_subsystem),
                "priority": getattr(i, "priority", "medium"),
            })
        if items:
            first_action = f"Process queue ({len(items)} items)"
            first_command = "workflow-dataset queue view"
    except Exception:
        pass

    try:
        from workflow_dataset.automation_inbox import build_automation_inbox
        inbox = build_automation_inbox(repo_root=root, status="pending", limit=automation_limit)
        for i in inbox[:10]:
            automation_lines.append(f"  {i.kind}: {(i.summary or i.item_id)[:55]}")
        if inbox:
            first_action = "Review automation inbox"
            first_command = "workflow-dataset automation-inbox list"
    except Exception:
        pass

    try:
        from workflow_dataset.review_studio.inbox import build_inbox
        inbox = build_inbox(repo_root=root, status="pending", limit=20)
        for i in inbox:
            if i.kind == "approval_queue":
                urgent_approvals.append(i.source_ref or i.item_id)
            if i.kind == "blocked_run":
                stalled_projects.append((i.entity_refs or {}).get("project_id", "unknown"))
        if urgent_approvals:
            first_action = "Review approval queue"
            first_command = "workflow-dataset inbox list"
    except Exception:
        pass

    try:
        from workflow_dataset.automation_inbox import get_recommended_handoff
        handoff = get_recommended_handoff(repo_root=root)
        if handoff:
            handoff_label = handoff.label
            handoff_command = handoff.command or handoff_command
    except Exception:
        pass

    # M36L.1: Prefer stored next-day recommendation when it has urgent carry-forward
    rec = load_next_session_recommendation(repo_root=root)
    if rec and getattr(rec, "urgent_carry_forward_count", 0) > 0 and rec.first_action_label:
        first_action = rec.first_action_label
        first_command = rec.first_action_command or first_command

    return MorningEntryBrief(
        brief_id=brief_id,
        generated_at_utc=now,
        change_since_last=change,
        top_queue_items=top_queue,
        automation_outcomes_summary=automation_lines,
        urgent_approvals=urgent_approvals,
        stalled_projects=list(dict.fromkeys(stalled_projects)),
        recommended_first_mode=first_mode,
        recommended_first_action=first_action,
        recommended_first_command=first_command,
        handoff_label=handoff_label,
        handoff_command=handoff_command,
    )
