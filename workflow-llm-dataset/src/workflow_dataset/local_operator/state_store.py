"""
Local operator core state store.
Keeps rich state in a local JSON file under data/local/operator/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STATE_DIR = "data/local/operator"
STATE_FILENAME = "state.json"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_operator_state_path(repo_root: Path | str | None = None) -> Path:
    root = _repo_root(repo_root)
    return root / STATE_DIR / STATE_FILENAME


def default_operator_state() -> dict[str, Any]:
    return {
        "approved_folders": [],
        "workflow_tree": [],
        "tool_registry": [],
        "action_proposals": [],
        "session_trust": {},
        "capability_trust": [],
        "machine_readiness": {},
        "operator_readiness": {},
        "last_execution": None,
        "last_task_plan_id": "",
        "last_task_run_id": "",
        "last_task_run": None,
        "updated_at": "",
    }


def load_operator_state(repo_root: Path | str | None = None) -> dict[str, Any]:
    path = get_operator_state_path(repo_root)
    if not path.exists():
        return default_operator_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        out = default_operator_state()
        out.update(data if isinstance(data, dict) else {})
        return out
    except Exception:
        return default_operator_state()


def save_operator_state(state: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    path = get_operator_state_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = default_operator_state()
    payload.update(state if isinstance(state, dict) else {})
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
