"""
M46D.1: Stability window registry — daily, weekly, rolling_7, rolling_30, rolling long-run.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any

from workflow_dataset.long_run_health.models import StabilityWindow


@dataclass
class StabilityWindowDef:
    """Definition of a stability window for health/drift."""
    kind: str
    label: str
    description: str
    days: int  # 0 = daily (1), 7 = weekly, etc.
    for_rolling: bool = False  # True for rolling_7, rolling_30, rolling_long_run


WINDOWS: list[StabilityWindowDef] = [
    StabilityWindowDef("daily", "Today", "Single-day view; most recent 24 hours.", 1, False),
    StabilityWindowDef("weekly", "This week", "Last 7 days; week view.", 7, False),
    StabilityWindowDef("rolling_7", "Last 7 days (rolling)", "Rolling 7-day window for short-run stability.", 7, True),
    StabilityWindowDef("rolling_30", "Last 30 days (rolling)", "Rolling 30-day window.", 30, True),
    StabilityWindowDef("rolling_long_run", "Long-run (rolling 30 days)", "Rolling 30-day window for sustained deployment health.", 30, True),
]


def list_stability_windows() -> list[dict[str, Any]]:
    """Return all window definitions as dicts (kind, label, description, days, for_rolling)."""
    return [
        {
            "kind": w.kind,
            "label": w.label,
            "description": w.description,
            "days": w.days,
            "for_rolling": w.for_rolling,
        }
        for w in WINDOWS
    ]


def get_stability_window(kind: str) -> StabilityWindowDef | None:
    """Return the window definition for kind, or None. Accepts rolling_long_run as alias."""
    kind = (kind or "").strip() or "rolling_7"
    for w in WINDOWS:
        if w.kind == kind:
            return w
    return None


def build_window(kind: str) -> StabilityWindow:
    """Build a StabilityWindow for the given kind with start_iso and end_iso."""
    kind = (kind or "").strip() or "rolling_7"
    # Map rolling_long_run to same as rolling_30 for date range
    days = 7
    label = "Last 7 days (rolling)"
    for w in WINDOWS:
        if w.kind == kind:
            days = w.days
            label = w.label
            break
    now = datetime.now(timezone.utc)
    end_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    start = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return StabilityWindow(kind=kind, start_iso=start, end_iso=end_iso, label=label)
