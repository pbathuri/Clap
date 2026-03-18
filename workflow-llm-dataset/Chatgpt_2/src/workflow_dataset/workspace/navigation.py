"""
M29: View switching / deep links. Phase D.
Resolve view target and return suggested commands for portfolio -> project -> session -> etc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.workspace.models import NavigationState, WORKSPACE_VIEWS
from workflow_dataset.workspace.state import build_navigation_state


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def resolve_view_target(
    view: str,
    project_id: str = "",
    session_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Resolve a view target and return navigation state + suggested commands (deep link).
    view: one of home, portfolio, project, session, approvals, policy, lanes, packs, artifacts, outcomes, rollout, settings.
    """
    root = _root(repo_root)
    view = (view or "home").lower().strip()
    if view not in WORKSPACE_VIEWS:
        view = "home"
    nav = build_navigation_state(view, project_id or None, session_id or None, root)
    suggested_commands: list[str] = []
    if view == "home":
        suggested_commands = ["workflow-dataset workspace home", "workflow-dataset mission-control"]
    elif view == "portfolio":
        suggested_commands = ["workflow-dataset portfolio status", "workflow-dataset portfolio next"]
    elif view == "project":
        pid = project_id or nav.current_project_id
        if pid:
            suggested_commands = [
                f"workflow-dataset projects show --id {pid}",
                f"workflow-dataset projects report --id {pid}",
                f"workflow-dataset agent-loop next --project {pid}",
            ]
        else:
            suggested_commands = ["workflow-dataset projects list", "workflow-dataset portfolio next"]
    elif view == "session":
        sid = session_id or nav.current_session_id
        if sid:
            suggested_commands = [
                "workflow-dataset session board",
                "workflow-dataset session artifacts",
            ]
        else:
            suggested_commands = ["workflow-dataset session list", "workflow-dataset session start"]
    elif view == "approvals":
        suggested_commands = ["workflow-dataset agent-loop queue", "workflow-dataset agent-loop status"]
    elif view == "policy":
        suggested_commands = ["workflow-dataset policy board", "workflow-dataset policy show"]
    elif view == "lanes":
        suggested_commands = ["workflow-dataset lanes list"]
        if nav.current_project_id:
            suggested_commands.append(f"workflow-dataset lanes list --project {nav.current_project_id}")
    elif view == "packs":
        suggested_commands = ["workflow-dataset packs list", "workflow-dataset runtime summary"]
    elif view == "artifacts":
        suggested_commands = ["workflow-dataset session artifacts", "workflow-dataset outcomes report"]
    elif view == "outcomes":
        suggested_commands = ["workflow-dataset outcomes report"]
    elif view == "rollout":
        suggested_commands = ["workflow-dataset rollout status"]
    elif view == "settings":
        suggested_commands = ["workflow-dataset mission-control", "workflow-dataset trust cockpit"]
    elif view == "ask":
        suggested_commands = [
            "workflow-dataset ask \"What should I do next?\"",
            "workflow-dataset ask \"Why is this blocked?\"",
            "workflow-dataset ask \"What changed since yesterday?\"",
        ]
    elif view == "timeline":
        suggested_commands = ["workflow-dataset timeline latest", "workflow-dataset timeline project --id <project_id>"]
    elif view == "inbox":
        suggested_commands = ["workflow-dataset inbox-studio list", "workflow-dataset inbox-studio review --id <item_id>", "workflow-dataset inbox list"]
    return {
        "view": view,
        "navigation": nav.to_dict(),
        "suggested_commands": suggested_commands,
    }


def deep_link_commands(
    from_view: str,
    to_view: str,
    project_id: str = "",
    session_id: str = "",
    repo_root: Path | str | None = None,
) -> list[str]:
    """Return list of commands to move from one view to another (e.g. portfolio -> project X)."""
    root = _root(repo_root)
    out: list[str] = []
    if to_view == "project" and project_id:
        out.append(f"workflow-dataset projects set-current --id {project_id}")
        out.append(f"workflow-dataset projects report --id {project_id}")
    elif to_view == "session" and session_id:
        out.append(f"workflow-dataset session board")  # assumes current session is set
    elif to_view == "portfolio":
        out.append("workflow-dataset portfolio status")
    elif to_view == "home":
        out.append("workflow-dataset workspace home")
    if not out:
        res = resolve_view_target(to_view, project_id, session_id, root)
        out = res.get("suggested_commands", [])[:3]
    return out
