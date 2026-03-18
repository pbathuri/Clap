"""
M26E: Persist current goal and latest plan for preview/explain/graph without re-compiling.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PLANNER_DIR = Path("data/local/planner")
CURRENT_GOAL_FILE = "current_goal.txt"
LATEST_PLAN_FILE = "latest_plan.json"


def _planner_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve() / PLANNER_DIR
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve() / PLANNER_DIR
    except Exception:
        return Path.cwd().resolve() / PLANNER_DIR


def save_current_goal(goal: str, repo_root: Path | str | None = None) -> Path:
    """Save current goal text to data/local/planner/current_goal.txt."""
    root = _planner_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / CURRENT_GOAL_FILE
    path.write_text(goal or "", encoding="utf-8")
    return path


def load_current_goal(repo_root: Path | str | None = None) -> str:
    """Load current goal text; return empty string if missing."""
    path = _planner_root(repo_root) / CURRENT_GOAL_FILE
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def save_latest_plan(plan: Any, repo_root: Path | str | None = None) -> Path:
    """Save plan to data/local/planner/latest_plan.json. plan must have to_dict()."""
    root = _planner_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / LATEST_PLAN_FILE
    data = plan.to_dict() if hasattr(plan, "to_dict") else plan
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_latest_plan(repo_root: Path | str | None = None):
    """Load latest plan from JSON; return None if missing. Returns Plan instance."""
    path = _planner_root(repo_root) / LATEST_PLAN_FILE
    if not path.exists():
        return None
    try:
        from workflow_dataset.planner.schema import Plan
        data = json.loads(path.read_text(encoding="utf-8"))
        return Plan.from_dict(data)
    except Exception:
        return None
