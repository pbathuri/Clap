"""
M47E–M47H: Fast route from queue/review item to single command or view (route-to-action).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_speed.models import SpeedUpCandidate


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


# Map routing_target (from UnifiedQueueItem) to suggested CLI command
ROUTING_TO_COMMAND: dict[str, str] = {
    "review": "workflow-dataset queue view --mode review",
    "planner": "workflow-dataset queue view",
    "executor": "workflow-dataset queue view",
    "workspace": "workflow-dataset workspace home",
    "automation_follow_up": "workflow-dataset automation-inbox list",
    "draft_composer": "workflow-dataset queue view",
    "": "workflow-dataset queue view",
}


def route_item_to_action(
    item_id: str | None = None,
    repo_root: Path | str | None = None,
    use_first_if_no_id: bool = True,
) -> dict[str, Any]:
    """
    Return a single recommended command (and optional view) for a queue/review item.
    If item_id is None and use_first_if_no_id, use first item in unified queue.
    """
    root = _root(repo_root)
    command = "workflow-dataset queue view"
    view_id = ""
    item_label = ""
    source = ""

    try:
        from workflow_dataset.unified_queue import build_unified_queue
        items = build_unified_queue(repo_root=root, limit=30)
        if not items:
            return {
                "command": "workflow-dataset queue view",
                "view_id": "",
                "item_id": "",
                "item_label": "Queue empty",
                "source": "",
                "reason": "No queue items; open queue view to see state.",
            }
        target = None
        if item_id:
            for i in items:
                if getattr(i, "item_id", "") == item_id:
                    target = i
                    break
        if target is None and use_first_if_no_id:
            target = items[0]
        if target:
            item_label = (getattr(target, "label", "") or getattr(target, "summary", ""))[:80]
            source = getattr(target, "source_subsystem", "")
            if hasattr(source, "value"):
                source = source.value
            routing = getattr(target, "routing_target", "") or ""
            command = ROUTING_TO_COMMAND.get(routing, "workflow-dataset queue view")
            if routing == "review":
                view_id = "review_studio"
            elif source == "action_cards":
                ref = getattr(target, "source_ref", "")
                command = f"workflow-dataset action-cards show --id {ref}" if ref else command
            elif source == "review_studio":
                command = "workflow-dataset review-studio open"
                view_id = "review_studio"
    except Exception as e:
        return {
            "command": "workflow-dataset queue view",
            "view_id": "",
            "item_id": item_id or "",
            "item_label": "",
            "source": "",
            "reason": f"Could not resolve route: {e}",
        }

    return {
        "command": command,
        "view_id": view_id,
        "item_id": getattr(target, "item_id", "") if target else "",
        "item_label": item_label,
        "source": source,
        "reason": f"Route for {source or 'queue'} item to single action.",
    }


def get_grouped_review_recommendation(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Recommend grouped review when multiple review items exist."""
    root = _root(repo_root)
    try:
        from workflow_dataset.unified_queue import build_unified_queue
        items = build_unified_queue(repo_root=root, limit=50)
        review_items = [i for i in items if getattr(i, "routing_target", "") == "review" or getattr(i, "section_id", "") == "review_ready"]
        count = len(review_items)
        if count == 0:
            return {"recommended": False, "command": "workflow-dataset queue view", "reason": "No review items.", "count": 0}
        if count >= 2:
            return {
                "recommended": True,
                "command": "workflow-dataset queue view --mode review",
                "reason": f"{count} items need review; use queue view --mode review for grouped review.",
                "count": count,
            }
        return {
            "recommended": True,
            "command": "workflow-dataset queue view --mode review",
            "reason": "One review item; open queue view --mode review.",
            "count": count,
        }
    except Exception:
        return {"recommended": False, "command": "workflow-dataset queue view", "reason": "Could not build queue.", "count": 0}
