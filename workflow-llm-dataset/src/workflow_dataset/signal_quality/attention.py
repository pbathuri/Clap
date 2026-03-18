"""
M37E–M37H: Attention protection.
Phase C: Focus mode quieting, operator grouped review, review-mode surfacing,
digest bundling, stronger interruption thresholds.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.signal_quality.models import ProtectedFocusItem


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_protected_focus(repo_root: Path | str | None = None) -> ProtectedFocusItem:
    """
    Resolve current focus protection: portfolio active_focus_mode_id + live_context work_mode.
    When focus mode is active or work_mode is focused, set active=True and allow_urgent_only=True.
    """
    root = _root(repo_root)
    project_id = ""
    work_mode = ""
    focus_mode_id = ""
    active = False
    try:
        from workflow_dataset.portfolio.store import load_attention_config
        config = load_attention_config(root)
        focus_mode_id = str(config.get("active_focus_mode_id", ""))
        if focus_mode_id:
            active = True
    except Exception:
        pass
    try:
        from workflow_dataset.live_context.state import get_live_context_state
        state = get_live_context_state(root / "data/local")
        if state:
            w = getattr(state, "work_mode", None)
            work_mode = (w.value if hasattr(w, "value") else str(w or "")).lower()
            if work_mode == "focused":
                active = True
            proj = getattr(state, "inferred_project", None)
            if proj is not None:
                project_id = getattr(proj, "project_id", "") or getattr(proj, "label", "") or ""
    except Exception:
        pass
    try:
        from workflow_dataset.project_case.store import get_current_project_id
        if not project_id:
            project_id = get_current_project_id(root) or ""
    except Exception:
        pass
    return ProtectedFocusItem(
        active=active,
        project_id=project_id,
        work_mode=work_mode,
        focus_mode_id=focus_mode_id,
        allow_urgent_only=True,
    )


def interruption_threshold_for_mode(work_mode: str) -> float:
    """
    Max interruptiveness score allowed for showing suggestions in this mode.
    Focused -> 0.3; switching/interrupted -> 0.5; idle/unknown -> 0.8.
    """
    w = (work_mode or "").lower()
    if w == "focused":
        return 0.3
    if w in ("switching", "interrupted", "returning"):
        return 0.5
    return 0.8


def digest_bundling_recommended(
    queue_count: int,
    overload_threshold: int = 20,
) -> dict[str, Any]:
    """
    When queue is overloaded, recommend digest view instead of drip.
    Returns dict: recommended=True/False, message, suggested_command.
    """
    recommended = queue_count > overload_threshold
    message = ""
    suggested_command = "queue view --mode focus  # or queue summary"
    if recommended:
        message = (
            f"Queue has {queue_count} items (over {overload_threshold}). "
            "Prefer digest/mode view to reduce noise."
        )
    return {
        "recommended": recommended,
        "message": message,
        "suggested_command": suggested_command,
        "queue_count": queue_count,
        "overload_threshold": overload_threshold,
    }


def operator_grouped_review_cap() -> int:
    """Suggested cap for operator-mode grouped review (show N items per group)."""
    return 15


def review_mode_surfacing_rule() -> str:
    """In review mode, surface: blocked first, then approval, then rest (no suppression of urgent)."""
    return "blocked_first_then_approval_then_rest"
