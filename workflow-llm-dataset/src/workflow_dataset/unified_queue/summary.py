"""
M36H.1: Stronger queue summaries for overloaded states.
"""

from __future__ import annotations

from pathlib import Path

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.unified_queue.models import UnifiedQueueItem, QueueSummary


def build_queue_summary(
    items: list[UnifiedQueueItem],
    overload_threshold: int = 20,
    recommended_cap: int = 10,
) -> QueueSummary:
    """
    Build queue summary; when total_count > overload_threshold, set is_overloaded
    and populate overflow_message, by_section, by_mode, top_blocked, suggested_action.
    """
    now = utc_now_iso()
    total = len(items)
    is_overloaded = total > overload_threshold
    by_section: dict[str, int] = {}
    for i in items:
        sid = i.section_id or "other"
        by_section[sid] = by_section.get(sid, 0) + 1
    by_mode: dict[str, int] = {}
    for i in items:
        for tag in i.mode_tags or []:
            by_mode[tag] = by_mode.get(tag, 0) + 1
    top_blocked_id = ""
    top_blocked_summary = ""
    for i in items:
        if i.section_id == "blocked" or i.actionability_class.value == "blocked":
            top_blocked_id = i.item_id
            top_blocked_summary = (i.summary or i.label or "")[:120]
            break
    overflow_message = ""
    suggested_action = ""
    if is_overloaded:
        overflow_message = (
            f"Queue has {total} items (over threshold {overload_threshold}). "
            "Consider using a mode view to narrow: queue view --mode focus | review | operator | wrap-up."
        )
        suggested_action = "queue view --mode focus  # or review | operator | wrap-up"
    return QueueSummary(
        total_count=total,
        is_overloaded=is_overloaded,
        overload_threshold=overload_threshold,
        by_section=by_section,
        by_mode=by_mode,
        top_blocked_item_id=top_blocked_id,
        top_blocked_summary=top_blocked_summary,
        recommended_cap=min(recommended_cap, total) if total else 0,
        overflow_message=overflow_message,
        suggested_action=suggested_action,
        generated_at_utc=now,
    )
