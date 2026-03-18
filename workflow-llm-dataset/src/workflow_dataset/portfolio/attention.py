"""
M28D.1: Attention budgets, work windows, focus modes — recommend work window and when to switch.
Explicit, operator-readable; no hidden automation.
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

from workflow_dataset.portfolio.models import (
    WorkWindow,
    FocusMode,
    WorkWindowRecommendation,
    SwitchRecommendation,
    SWITCH_RULE_TRIGGERS,
)
from workflow_dataset.portfolio.store import load_attention_config
from workflow_dataset.portfolio.scheduler import get_next_recommended_project


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _parse_iso_to_minutes_ago(iso: str) -> int | None:
    """Minutes since iso timestamp. Returns None if parse fails."""
    if not iso:
        return None
    try:
        from datetime import datetime, timezone
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - t
        return int(delta.total_seconds() / 60)
    except Exception:
        return None


def get_work_window_recommendation(
    current_project_id: str | None = None,
    repo_root: Path | str | None = None,
) -> WorkWindowRecommendation:
    """
    Current work window suggestion: default window duration, remaining minutes if tracking,
    and suggested next project (from portfolio next). Operator-readable.
    """
    root = _root(repo_root)
    config = load_attention_config(root)
    windows = [WorkWindow.from_dict(w) for w in config.get("work_windows", [])]
    default_duration = 25
    window_id = ""
    window_name = "default"
    if windows:
        w = windows[0]
        default_duration = w.duration_minutes
        window_id = w.window_id or "default"
        window_name = w.name or "Default slice"
    started_iso = config.get("current_window_started_at_iso", "")
    remaining: int | None = None
    if started_iso and default_duration > 0:
        minutes_ago = _parse_iso_to_minutes_ago(started_iso)
        if minutes_ago is not None:
            remaining = max(0, default_duration - minutes_ago)
    next_rec = get_next_recommended_project(root)
    suggested_next = next_rec.project_id if next_rec else ""
    reason = ""
    if suggested_next and suggested_next != (current_project_id or ""):
        reason = f"Portfolio next: {suggested_next}"
    return WorkWindowRecommendation(
        project_id=current_project_id or "",
        window_id=window_id,
        window_name=window_name,
        duration_minutes=default_duration,
        remaining_minutes=remaining,
        suggested_next_project_id=suggested_next,
        reason=reason,
    )


def should_recommend_switch(
    current_project_id: str | None = None,
    repo_root: Path | str | None = None,
) -> SwitchRecommendation:
    """
    Rules for when to recommend switching projects:
    - work_window_ended: current window duration elapsed (if tracking).
    - higher_priority_ready: portfolio next recommends a different project.
    - attention_budget_cap: placeholder (no spent tracking yet); not triggered in first-draft.
    Returns SwitchRecommendation with reason and suggested_project_id. Explicit, operator-readable.
    """
    root = _root(repo_root)
    config = load_attention_config(root)
    focus_modes = [FocusMode.from_dict(f) for f in config.get("focus_modes", [])]
    active_mode_id = config.get("active_focus_mode_id", "")
    active_mode: FocusMode | None = next((m for m in focus_modes if m.mode_id == active_mode_id), None)
    if not active_mode:
        active_mode = FocusMode(mode_id="", switch_rules=["when_higher_priority_ready"])  # default rules
    rules = set(active_mode.switch_rules or ["when_higher_priority_ready"])
    current = current_project_id or ""

    # Work window ended: check current_window_started_at + first work window duration
    windows = [WorkWindow.from_dict(w) for w in config.get("work_windows", [])]
    duration = 25
    if windows:
        duration = windows[0].duration_minutes
    started_iso = config.get("current_window_started_at_iso", "")
    remaining_min: int | None = None
    if started_iso:
        minutes_ago = _parse_iso_to_minutes_ago(started_iso)
        if minutes_ago is not None:
            remaining_min = max(0, duration - minutes_ago)
            if "on_window_end" in rules and remaining_min == 0 and duration > 0:
                next_rec = get_next_recommended_project(root)
                suggested = next_rec.project_id if next_rec else ""
                if suggested != current:
                    return SwitchRecommendation(
                        recommend_switch=True,
                        reason="Work window ended; consider switching to next recommended project.",
                        suggested_project_id=suggested,
                        rule_triggered="work_window_ended",
                        current_project_id=current,
                        work_window_remaining_minutes=0,
                        focus_mode_id=active_mode_id,
                    )

    # Higher priority ready: portfolio next recommends different project
    if "when_higher_priority_ready" in rules:
        next_rec = get_next_recommended_project(root)
        if next_rec and next_rec.project_id != current:
            return SwitchRecommendation(
                recommend_switch=True,
                reason=next_rec.reason or "Higher-priority project recommended by portfolio.",
                suggested_project_id=next_rec.project_id,
                rule_triggered="higher_priority_ready",
                current_project_id=current,
                work_window_remaining_minutes=remaining_min,
                focus_mode_id=active_mode_id,
            )

    # No switch recommended
    return SwitchRecommendation(
        recommend_switch=False,
        reason="No switch rule triggered; continue current project or choose manually.",
        suggested_project_id="",
        rule_triggered="manual_only",
        current_project_id=current,
        work_window_remaining_minutes=remaining_min,
        focus_mode_id=active_mode_id,
    )


def start_work_window(repo_root: Path | str | None = None) -> str:
    """
    Set current_window_started_at_iso to now. Call when operator starts a work slice.
    Returns updated iso timestamp.
    """
    now = utc_now_iso()
    root = _root(repo_root)
    from workflow_dataset.portfolio.store import load_attention_config, save_attention_config
    from workflow_dataset.portfolio.models import AttentionBudget, WorkWindow, FocusMode
    config = load_attention_config(root)
    budgets = [AttentionBudget.from_dict(b) for b in config.get("attention_budgets", [])]
    windows = [WorkWindow.from_dict(w) for w in config.get("work_windows", [])]
    modes = [FocusMode.from_dict(f) for f in config.get("focus_modes", [])]
    save_attention_config(
        attention_budgets=budgets,
        work_windows=windows,
        focus_modes=modes,
        active_focus_mode_id=config.get("active_focus_mode_id", ""),
        current_window_started_at_iso=now,
        repo_root=root,
    )
    return now
