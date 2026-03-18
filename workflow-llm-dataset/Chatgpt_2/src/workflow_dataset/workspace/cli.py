"""
M29: Workspace CLI — home, open, context, next. Phase E.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.workspace.state import (
    build_active_work_context,
    build_navigation_state,
    build_workspace_home_snapshot,
)
from workflow_dataset.workspace.home import build_unified_home, format_workspace_home
from workflow_dataset.workspace.navigation import resolve_view_target, deep_link_commands


def cmd_home(
    repo_root: Path | str | None = None,
    preset_id: str | None = None,
    profile_id: str | None = None,
) -> str:
    """Unified workspace home output. Optional preset_id for role layout; profile_id calm_default/first_user uses calm home (M37). When profile_id is omitted, active default profile is used."""
    effective = (profile_id or "").strip()
    if not effective:
        try:
            from workflow_dataset.default_experience.store import get_active_default_profile_id
            effective = get_active_default_profile_id(repo_root=repo_root) or "calm_default"
        except Exception:
            effective = "calm_default"
    # Any profile with default_home_format calm uses calm home (includes role calm: founder_calm, etc.)
    try:
        from workflow_dataset.default_experience.profiles import get_profile
        p = get_profile(effective)
        if p and p.default_home_format == "calm":
            from workflow_dataset.default_experience.calm_home import format_calm_default_home
            return format_calm_default_home(snapshot=None, repo_root=repo_root)
    except Exception:
        if effective in ("calm_default", "first_user"):
            from workflow_dataset.default_experience.calm_home import format_calm_default_home
            return format_calm_default_home(snapshot=None, repo_root=repo_root)
    return format_workspace_home(repo_root=repo_root, preset_id=preset_id)


def cmd_presets_list() -> list[dict[str, Any]]:
    """List workspace presets (id, label, description, recommended_first_view)."""
    from workflow_dataset.workspace.presets import WORKSPACE_PRESETS, list_preset_ids
    return [
        {
            "preset_id": pid,
            "label": WORKSPACE_PRESETS[pid].label,
            "description": WORKSPACE_PRESETS[pid].description,
            "recommended_first_view": WORKSPACE_PRESETS[pid].recommended_first_view,
        }
        for pid in list_preset_ids()
    ]


def cmd_open(
    view: str = "home",
    project: str = "",
    session: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Open a view; return navigation state and suggested commands."""
    return resolve_view_target(view, project_id=project, session_id=session, repo_root=repo_root)


def cmd_context(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Current workspace context: project, session, view, breadcrumbs, quick actions."""
    root = Path(repo_root).resolve() if repo_root else None
    ctx = build_active_work_context(root)
    nav = build_navigation_state("home", ctx.active_project_id, ctx.active_session_id, root)
    return {
        "active_project_id": ctx.active_project_id,
        "active_project_title": ctx.active_project_title,
        "active_session_id": ctx.active_session_id,
        "active_goal_text": (ctx.active_goal_text or "")[:100],
        "queued_approvals_count": ctx.queued_approvals_count,
        "blocked_items_count": ctx.blocked_items_count,
        "navigation": nav.to_dict(),
        "next_action": ctx.next_recommended_action,
        "next_detail": ctx.next_recommended_detail,
    }


def cmd_next(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Next recommended action (portfolio next + mission_control next)."""
    root = Path(repo_root).resolve() if repo_root else None
    ctx = build_active_work_context(root)
    return {
        "next_recommended_project_id": ctx.next_recommended_project_id,
        "portfolio_next_reason": ctx.portfolio_next_reason,
        "next_action": ctx.next_recommended_action,
        "next_detail": ctx.next_recommended_detail,
    }
