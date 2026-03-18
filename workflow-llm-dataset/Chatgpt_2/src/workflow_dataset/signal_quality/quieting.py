"""
M37E–M37H: Queue and assist quieting.
Phase B: Apply signal-quality filters; produce suppressed list; never suppress urgent tier.
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

from workflow_dataset.signal_quality.models import (
    SignalQualityScore,
    SuppressedQueueItem,
    ProtectedFocusItem,
    ALWAYS_SHOW_PRIORITY,
)
from workflow_dataset.signal_quality.scoring import score_queue_item, score_assist_suggestion
from workflow_dataset.signal_quality.explain import explain_held_back


def _apply_queue_quieting(
    items: list[Any],
    focus: ProtectedFocusItem | None,
    max_visible: int = 30,
    suppress_low_value_below: float = 0.2,
) -> tuple[list[Any], list[SuppressedQueueItem]]:
    """
    Filter queue items: never drop urgent tier; when focus protected, drop non-urgent low usefulness;
    cap visible at max_visible (lowest signal first); record suppressed.
    """
    from workflow_dataset.signal_quality.scoring import rank_by_high_signal
    suppressed: list[SuppressedQueueItem] = []
    now = utc_now_iso()
    context = {"focus_mode_active": focus.active if focus else False}
    work_mode = getattr(focus, "work_mode", "") if focus else ""
    ranked = rank_by_high_signal(items, score_queue_item, context)
    visible: list[Any] = []
    for item in ranked:
        score = score_queue_item(item, context)
        item_id = getattr(item, "item_id", "") or ""
        priority = (getattr(item, "priority", "") or "medium").lower()
        if score.is_urgent_tier or priority in ALWAYS_SHOW_PRIORITY:
            visible.append(item)
            continue
        if focus and focus.active and focus.allow_urgent_only:
            suppressed.append(SuppressedQueueItem(
                item_id=item_id,
                source="queue",
                suppressed_at_utc=now,
                reason="focus_safe",
                urgency_tier=priority,
                resurfacing_eligible=True,
                explanation=explain_held_back("focus_safe", item_id=item_id, source="queue", work_mode=work_mode, urgency_tier=priority),
            ))
            continue
        if score.usefulness < suppress_low_value_below:
            suppressed.append(SuppressedQueueItem(
                item_id=item_id,
                source="queue",
                suppressed_at_utc=now,
                reason="low_value",
                urgency_tier=priority,
                resurfacing_eligible=True,
                explanation=explain_held_back("low_value", item_id=item_id, source="queue", work_mode=work_mode, urgency_tier=priority),
            ))
            continue
        if len(visible) >= max_visible:
            suppressed.append(SuppressedQueueItem(
                item_id=item_id,
                source="queue",
                suppressed_at_utc=now,
                reason="rate_cap",
                urgency_tier=priority,
                resurfacing_eligible=True,
                explanation=explain_held_back("rate_cap", item_id=item_id, source="queue", work_mode=work_mode, urgency_tier=priority),
            ))
            continue
        visible.append(item)
    return visible, suppressed


def apply_queue_quieting(
    items: list[Any],
    repo_root: Path | str | None = None,
    focus: ProtectedFocusItem | None = None,
    max_visible: int = 30,
) -> tuple[list[Any], list[SuppressedQueueItem]]:
    """Public: apply quieting to unified queue items; return (visible, suppressed)."""
    return _apply_queue_quieting(items, focus, max_visible=max_visible)


def apply_assist_quieting(
    suggestions: list[Any],
    focus: ProtectedFocusItem | None = None,
    max_visible: int = 20,
    suppress_low_usefulness_below: float = 0.2,
) -> tuple[list[Any], list[SuppressedQueueItem]]:
    """
    Filter assist suggestions: never drop urgent tier (e.g. blocked_review high confidence);
    when focus protected, drop high-interrupt; cap visible; record suppressed.
    """
    from workflow_dataset.signal_quality.scoring import rank_by_high_signal
    suppressed: list[SuppressedQueueItem] = []
    now = utc_now_iso()
    context = {"focus_mode_active": focus.active if focus else False}
    work_mode = getattr(focus, "work_mode", "") if focus else ""
    ranked = rank_by_high_signal(suggestions, score_assist_suggestion, context)
    visible: list[Any] = []
    for s in ranked:
        score = score_assist_suggestion(s, context)
        sid = getattr(s, "suggestion_id", "") or ""
        if score.is_urgent_tier:
            visible.append(s)
            continue
        if focus and focus.active and score.interruption_cost > 0.4:
            suppressed.append(SuppressedQueueItem(
                item_id=sid,
                source="assist",
                suppressed_at_utc=now,
                reason="focus_safe",
                urgency_tier="medium",
                resurfacing_eligible=True,
                explanation=explain_held_back("focus_safe", item_id=sid, source="assist", work_mode=work_mode),
            ))
            continue
        if score.usefulness < suppress_low_usefulness_below:
            suppressed.append(SuppressedQueueItem(
                item_id=sid,
                source="assist",
                suppressed_at_utc=now,
                reason="low_value",
                urgency_tier="medium",
                resurfacing_eligible=True,
                explanation=explain_held_back("low_value", item_id=sid, source="assist", work_mode=work_mode),
            ))
            continue
        if len(visible) >= max_visible:
            suppressed.append(SuppressedQueueItem(
                item_id=sid,
                source="assist",
                suppressed_at_utc=now,
                reason="rate_cap",
                urgency_tier="medium",
                resurfacing_eligible=True,
                explanation=explain_held_back("rate_cap", item_id=sid, source="assist", work_mode=work_mode),
            ))
            continue
        visible.append(s)
    return visible, suppressed
