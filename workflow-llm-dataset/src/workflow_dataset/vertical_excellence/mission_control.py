"""
M47D: Mission control slice — current first-value stage, friction, recommend-next, blocked cases.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_excellence.compression import (
    assess_first_value_stage,
    list_blocked_first_value_cases,
    list_friction_points,
)
from workflow_dataset.vertical_excellence.path_resolver import get_chosen_vertical_id
from workflow_dataset.vertical_excellence.recommend_next import recommend_next_for_vertical


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def vertical_excellence_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Additive mission-control slice for vertical excellence.
    Keys: current_first_value_stage, strongest_friction_point_id, top_default_path_improvement,
    next_recommended_excellence_action, blocked_first_value_cases_count.
    """
    root = _root(repo_root)
    stage = assess_first_value_stage(root)
    frictions = list_friction_points(root)
    blocked = list_blocked_first_value_cases(root)
    rec = recommend_next_for_vertical(root)
    strongest_friction = frictions[0] if frictions else None
    return {
        "vertical_id": get_chosen_vertical_id(root),
        "current_first_value_stage": stage.to_dict(),
        "strongest_friction_point_id": strongest_friction.friction_id if strongest_friction else None,
        "strongest_friction_label": strongest_friction.label if strongest_friction else None,
        "top_default_path_improvement": (
            "Reduce steps to first value: run next step " + stage.next_command_hint
            if stage.status == "in_progress" and stage.next_command_hint
            else ("Start first-value path" if stage.status == "not_started" else None)
        ),
        "next_recommended_excellence_action": {
            "command": rec.command,
            "label": rec.label,
            "rationale": rec.rationale,
        } if rec else None,
        "blocked_first_value_cases_count": len(blocked),
        "blocked_first_value_cases": blocked,
    }
