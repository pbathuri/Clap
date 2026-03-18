"""
M41I–M41L: Ops job run history. data/local/ops_jobs/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DIR_NAME = "data/local/ops_jobs"
HISTORY_FILE = "history.json"
LAST_RUN_FILE = "last_run.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_ops_jobs_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / DIR_NAME


def _history_path(root: Path) -> Path:
    return root / DIR_NAME / HISTORY_FILE


def _last_run_path(root: Path) -> Path:
    return root / DIR_NAME / LAST_RUN_FILE


def append_run(job_id: str, run_result: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    """Append one run to history and update last_run for job_id."""
    root = _repo_root(repo_root)
    get_ops_jobs_dir(repo_root=root).mkdir(parents=True, exist_ok=True)
    history_path = root / DIR_NAME / HISTORY_FILE
    last_path = root / DIR_NAME / LAST_RUN_FILE

    history: list[dict[str, Any]] = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except Exception:
            history = []
    run_entry = {"job_id": job_id, **run_result}
    history.append(run_entry)
    # Keep last 500 entries
    if len(history) > 500:
        history = history[-500:]
    history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    last_map: dict[str, dict[str, Any]] = {}
    if last_path.exists():
        try:
            last_map = json.loads(last_path.read_text(encoding="utf-8"))
        except Exception:
            last_map = {}
    last_map[job_id] = run_result
    last_path.write_text(json.dumps(last_map, indent=2), encoding="utf-8")
    return history_path


def get_last_run(job_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return last run result for job_id; empty dict if never run."""
    root = _repo_root(repo_root)
    last_path = root / DIR_NAME / LAST_RUN_FILE
    if not last_path.exists():
        return {}
    try:
        last_map = json.loads(last_path.read_text(encoding="utf-8"))
        return last_map.get(job_id, {})
    except Exception:
        return {}


def list_run_history(job_id: str, limit: int = 20, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Return most recent runs for job_id (newest first)."""
    root = _repo_root(repo_root)
    history_path = root / DIR_NAME / HISTORY_FILE
    if not history_path.exists():
        return []
    try:
        history = json.loads(history_path.read_text(encoding="utf-8"))
        filtered = [e for e in history if e.get("job_id") == job_id]
        return list(reversed(filtered[-limit:]))
    except Exception:
        return []
