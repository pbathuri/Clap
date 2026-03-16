"""
M23A: Chain run manifest and state persistence. One run = one directory with run_manifest.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.chain_lab.config import get_chain_lab_root, get_runs_dir
from workflow_dataset.utils.dates import utc_now_iso

RUN_MANIFEST_FILENAME = "run_manifest.json"
STEP_RESULTS_DIR = "steps"


def get_run_dir(run_id: str, repo_root: Path | str | None = None, create: bool = False) -> Path:
    """Path for a single run: runs/<run_id>/. If create=True, mkdir."""
    runs_dir = get_runs_dir(repo_root)
    d = runs_dir / run_id
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def run_dir_for(run_id: str, repo_root: Path | str | None = None) -> Path:
    """Directory for a single run: runs/<run_id>/ (creates if needed)."""
    return get_run_dir(run_id, repo_root, create=True)


def step_result_dir(run_id: str, step_index: int, repo_root: Path | str | None = None) -> Path:
    """Directory for one step's persisted output: runs/<run_id>/steps/<index>/."""
    base = run_dir_for(run_id, repo_root) / STEP_RESULTS_DIR / str(step_index)
    base.mkdir(parents=True, exist_ok=True)
    return base


def load_run_manifest(run_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load run manifest by run_id. Returns None if not found or invalid."""
    d = get_run_dir(run_id, repo_root, create=False)
    path = d / RUN_MANIFEST_FILENAME
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_run_manifest(
    run_id: str,
    chain_id: str,
    variant_label: str,
    status: str,
    step_results: list[dict[str, Any]],
    started_at: str,
    ended_at: str | None = None,
    failure_summary: str | None = None,
    repo_root: Path | str | None = None,
) -> Path:
    """Write run_manifest.json for this run. step_results: list of {step_index, step_id, status, started_at, ended_at, output_paths, error}."""
    d = run_dir_for(run_id, repo_root)
    path = d / RUN_MANIFEST_FILENAME
    payload: dict[str, Any] = {
        "run_id": run_id,
        "chain_id": chain_id,
        "variant_label": variant_label or "",
        "status": status,
        "step_results": list(step_results),
        "started_at": started_at,
        "ended_at": ended_at or utc_now_iso(),
        "failure_summary": failure_summary,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def list_run_ids(repo_root: Path | str | None = None, limit: int = 50) -> list[str]:
    """List run_id directories (newest first by mtime)."""
    runs_dir = get_runs_dir(repo_root)
    if not runs_dir.exists():
        return []
    ids_with_mtime: list[tuple[str, float]] = []
    for p in runs_dir.iterdir():
        if p.is_dir() and (p / RUN_MANIFEST_FILENAME).exists():
            ids_with_mtime.append((p.name, (p / RUN_MANIFEST_FILENAME).stat().st_mtime))
    ids_with_mtime.sort(key=lambda x: x[1], reverse=True)
    return [rid for rid, _ in ids_with_mtime[:limit]]


def get_latest_run_id(repo_root: Path | str | None = None, limit: int = 1) -> str | None:
    """Return the most recent run_id, or None if no runs exist. For --run latest."""
    ids = list_run_ids(repo_root=repo_root, limit=max(1, limit))
    return ids[0] if ids else None
