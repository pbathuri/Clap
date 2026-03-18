"""
M47E–M47H: Repeat-value flows — prefilled defaults, grouped review, blocked recovery.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_speed.models import SpeedUpCandidate, RepeatValueBottleneck
from workflow_dataset.vertical_speed.friction import get_repeat_value_bottlenecks
from workflow_dataset.vertical_speed.action_route import route_item_to_action, get_grouped_review_recommendation


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_morning_first_action_prefill(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return prefilled first action from morning/continuity brief (single command to run next)."""
    root = _root(repo_root)
    try:
        from workflow_dataset.continuity_engine.morning_flow import build_morning_entry_flow
        brief = build_morning_entry_flow(repo_root=root, queue_limit=20, automation_limit=15)
        first_command = getattr(brief, "first_action_command", "") or getattr(brief, "handoff_command", "") or "workflow-dataset queue view"
        first_action = getattr(brief, "first_action", "") or "Review queue"
        return {
            "prefilled_command": first_command,
            "prefilled_label": first_action,
            "brief_id": getattr(brief, "brief_id", ""),
            "reason": "Use this command as first action after morning or resume.",
        }
    except Exception as e:
        return {
            "prefilled_command": "workflow-dataset continuity morning",
            "prefilled_label": "Run continuity morning",
            "brief_id": "",
            "reason": f"Could not build morning brief: {e}",
        }


def get_blocked_recovery_suggestion(
    repo_root: Path | str | None = None,
    subsystem: str | None = None,
) -> dict[str, Any]:
    """Suggest minimal recovery for blocked workflow (e.g. recovery suggest, or action-route for top blocked item)."""
    root = _root(repo_root)
    try:
        from workflow_dataset.unified_queue import build_unified_queue
        items = build_unified_queue(repo_root=root, limit=50)
        blocked = [i for i in items if getattr(i, "section_id", "") == "blocked" or str(getattr(i, "actionability_class", "")).endswith("BLOCKED")]
        if not blocked:
            return {
                "suggestion": "workflow-dataset recovery suggest",
                "reason": "No blocked items in queue; use recovery suggest with --subsystem if a specific area is stuck.",
                "item_id": "",
            }
        top = blocked[0]
        item_id = getattr(top, "item_id", "")
        route = route_item_to_action(item_id=item_id, repo_root=root, use_first_if_no_id=False)
        return {
            "suggestion": route.get("command", "workflow-dataset queue view"),
            "reason": "Top blocked item; try route-to-action or recovery suggest --subsystem.",
            "item_id": item_id,
            "recovery_command": "workflow-dataset recovery suggest",
        }
    except Exception:
        return {
            "suggestion": "workflow-dataset recovery suggest",
            "reason": "Use recovery suggest to get playbook for blocked state.",
            "item_id": "",
        }


def repeat_value_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Aggregate repeat-value signals: morning prefill, grouped review, blocked recovery, bottlenecks."""
    root = _root(repo_root)
    morning = get_morning_first_action_prefill(repo_root=root)
    grouped = get_grouped_review_recommendation(repo_root=root)
    blocked = get_blocked_recovery_suggestion(repo_root=root)
    bottlenecks = get_repeat_value_bottlenecks(repo_root=root)
    return {
        "morning_prefill": morning,
        "grouped_review": grouped,
        "blocked_recovery": blocked,
        "bottlenecks": [b.to_dict() for b in bottlenecks],
        "next_recommended": morning.get("prefilled_command", "workflow-dataset queue view"),
    }
