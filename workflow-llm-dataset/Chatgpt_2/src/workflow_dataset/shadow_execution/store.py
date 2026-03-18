"""
M45E–M45H: Persist shadow runs under data/local/shadow_execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.shadow_execution.models import ShadowRun

DIR_NAME = "data/local/shadow_execution"
RUNS_DIR = "runs"
RUN_FILE = "run.json"
MAX_LIST = 100


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_runs_dir(repo_root: Path | str | None = None) -> Path:
    root = _repo_root(repo_root)
    path = root / DIR_NAME / RUNS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_shadow_run(run: ShadowRun, repo_root: Path | str | None = None) -> Path:
    root = get_runs_dir(repo_root)
    run_dir = root / run.shadow_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / RUN_FILE
    path.write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")
    return path


def load_shadow_run(shadow_run_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    root = get_runs_dir(repo_root)
    path = root / shadow_run_id / RUN_FILE
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_shadow_runs(
    limit: int = 50,
    status: str | None = None,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    root = get_runs_dir(repo_root)
    out: list[dict[str, Any]] = []
    for d in sorted(root.iterdir(), key=lambda x: x.stat().st_mtime if x.is_dir() else 0, reverse=True):
        if not d.is_dir():
            continue
        f = d / RUN_FILE
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if status and data.get("status") != status:
                continue
            out.append({
                "shadow_run_id": data.get("shadow_run_id", d.name),
                "status": data.get("status", ""),
                "plan_ref": data.get("plan_ref", ""),
                "plan_source": data.get("plan_source", ""),
                "timestamp_start": data.get("timestamp_start", ""),
                "forced_takeover": data.get("forced_takeover", {}).get("forced", False),
            })
            if len(out) >= limit:
                break
        except Exception:
            pass
    return out
