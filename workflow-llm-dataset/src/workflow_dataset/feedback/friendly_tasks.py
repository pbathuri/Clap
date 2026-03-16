"""
M19: Load friendly trial task set from JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_friendly_trial_tasks(
    tasks_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Load friendly_trial_tasks.json; return list of task dicts. Empty list if missing."""
    path = Path(tasks_path) if tasks_path else Path("data/local/trials/friendly_trial_tasks.json")
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def get_task_by_id(task_id: str, tasks_path: Path | str | None = None) -> dict[str, Any] | None:
    """Return first task with given task_id or None."""
    for t in load_friendly_trial_tasks(tasks_path):
        if t.get("task_id") == task_id:
            return t
    return None
