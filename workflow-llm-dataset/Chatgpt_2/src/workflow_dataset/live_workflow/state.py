"""
Persist/load current live workflow run (M33H).

Stores under data/local/live_workflow/current_run.json. No server; local-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.live_workflow.models import SupervisedLiveWorkflow

LIVE_WORKFLOW_DIR = Path("data/local/live_workflow")
CURRENT_RUN_FILE = "current_run.json"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _run_path(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / LIVE_WORKFLOW_DIR / CURRENT_RUN_FILE


def get_live_workflow_run(repo_root: Path | str | None = None) -> SupervisedLiveWorkflow | None:
    """Load the current live workflow run from disk, or None if none saved."""
    path = _run_path(repo_root)
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        d = json.loads(raw)
        if not d or not isinstance(d, dict):
            return None
        return SupervisedLiveWorkflow.model_validate(_normalize_loaded(d))
    except Exception:
        return None


def _normalize_loaded(d: dict[str, Any]) -> dict[str, Any]:
    """Ensure nested steps and blocked_step use dicts for Pydantic."""
    if "steps" in d and isinstance(d["steps"], list):
        d["steps"] = [s if isinstance(s, dict) else {} for s in d["steps"]]
    if d.get("blocked_step") is not None and not isinstance(d["blocked_step"], dict):
        d["blocked_step"] = None
    return d


def save_live_workflow_run(run: SupervisedLiveWorkflow, repo_root: Path | str | None = None) -> None:
    """Persist the current live workflow run to disk."""
    path = _run_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = run.to_dict()
    # Ensure steps and nested enums are JSON-serializable
    steps_out = []
    for s in run.steps:
        step_d = s.model_dump()
        step_d["escalation_tier"] = s.escalation_tier.value
        steps_out.append(step_d)
    data["steps"] = steps_out
    data["blocked_step"] = run.blocked_step.model_dump() if run.blocked_step else None
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
