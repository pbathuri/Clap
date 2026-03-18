"""
M37H.1: Stronger explanations for why an item was held back, grouped, or resurfaced.
"""

from __future__ import annotations

from typing import Any

# Reason code -> human-readable template (may use item_id, work_mode, etc.)
HELD_BACK_TEMPLATES: dict[str, str] = {
    "focus_safe": "Held back because focus protection is on: only urgent items are shown. This item is not in the urgent tier (blocked/approval/urgent). Turn off focus mode or use queue view --mode review to see it.",
    "repeat": "Held back as repetitive: a suggestion with the same type and reason was recently dismissed. It will resurface after the cooldown or when context changes.",
    "rate_cap": "Held back by rate cap: the queue is showing the maximum number of items for this view. Use queue view --mode focus or queue summary to narrow.",
    "low_value": "Held back as low value in current context: usefulness score is below the threshold for this profile. It may appear in wrap-up or when you switch mode.",
    "quiet_hours": "Held back during quiet hours: assist policy restricts suggestions in this time window. It will be available after the quiet window ends.",
    "noise_ceiling": "Held back by noise ceiling: this item exceeds the allowed noise level for your current role/mode. Use queue suppressions to see it or switch to a less strict profile.",
}

GROUPED_TEMPLATES: dict[str, str] = {
    "by_section": "Grouped by section (project or episode) to reduce clutter. Expand the section to see all items.",
    "by_mode": "Grouped by mode view (focus, review, operator, wrap-up). Use queue view --mode <mode> to see this group.",
    "digest": "Grouped into a digest to avoid drip. Use queue summary or queue view to see the full set.",
}

RESURFACED_TEMPLATES: dict[str, str] = {
    "stale_blocked_3d": "Resurfaced because this blocked or approval item is older than 3 days and may need attention. Stale-but-important rule applied.",
    "cooldown_elapsed": "Resurfaced after cooldown: it was previously held back and is now eligible to show again.",
    "default": "Resurfaced as a candidate for attention (e.g. stale-but-important or resurfacing rule).",
}


def explain_held_back(
    reason: str,
    item_id: str = "",
    source: str = "queue",
    work_mode: str = "",
    urgency_tier: str = "",
) -> str:
    """Human-readable explanation for why an item was held back."""
    template = HELD_BACK_TEMPLATES.get(reason) or (
        f"Held back: reason={reason}. Use queue suppressions to see suppressed items."
    )
    if work_mode:
        template += f" (Current mode: {work_mode}.)"
    return template


def explain_grouped(
    group_reason: str,
    item_count: int = 0,
) -> str:
    """Human-readable explanation for why items were grouped."""
    template = GROUPED_TEMPLATES.get(group_reason) or f"Grouped: {group_reason}."
    if item_count:
        template += f" {item_count} item(s) in this group."
    return template


def explain_resurfaced(
    item_id: str = "",
    rule_name: str = "",
    section_id: str = "",
    created_at: str = "",
) -> str:
    """Human-readable explanation for why an item was resurfaced."""
    template = RESURFACED_TEMPLATES.get(rule_name or "default") or RESURFACED_TEMPLATES["default"]
    if section_id:
        template += f" Section: {section_id}."
    if created_at:
        template += f" Created: {created_at[:19]}."
    return template
