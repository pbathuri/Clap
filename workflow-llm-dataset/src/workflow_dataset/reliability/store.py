"""
M30E–M30H: Persist reliability runs to data/local/reliability/runs/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


RELIABILITY_DIR = "data/local/reliability"
RUNS_SUBDIR = "runs"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_reliability_dir(repo_root: Path | str | None = None) -> Path:
    """Return path to reliability data directory."""
    return _repo_root(repo_root) / RELIABILITY_DIR


def get_runs_dir(repo_root: Path | str | None = None) -> Path:
    """Return path to reliability runs directory."""
    return get_reliability_dir(repo_root) / RUNS_SUBDIR


def save_run(run_result: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    """Save reliability run to data/local/reliability/runs/<run_id>.json."""
    root = _repo_root(repo_root)
    runs_dir = get_runs_dir(root)
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = run_result.get("run_id", "rel_unknown")
    run_result["saved_at"] = utc_now_iso()
    path = runs_dir / f"{run_id}.json"
    out = {
        "run_id": run_result.get("run_id"),
        "path_id": run_result.get("path_id"),
        "path_name": run_result.get("path_name"),
        "outcome": run_result.get("outcome"),
        "failure_step_index": run_result.get("failure_step_index"),
        "failure_step_id": run_result.get("failure_step_id"),
        "subsystem": run_result.get("subsystem"),
        "reasons": run_result.get("reasons", []),
        "timestamp": run_result.get("timestamp"),
        "saved_at": run_result.get("saved_at"),
        "steps_results": [
            {"step_id": s.get("step_id"), "actual": s.get("actual")}
            for s in run_result.get("steps_results", [])
        ],
    }
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return path


def load_latest_run(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load most recent reliability run. Returns None if no runs."""
    runs_dir = get_runs_dir(repo_root)
    if not runs_dir.exists():
        return None
    files = sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except Exception:
        return None


def list_runs(repo_root: Path | str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """List reliability run summaries (run_id, path_id, outcome, timestamp)."""
    runs_dir = get_runs_dir(repo_root)
    if not runs_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            out.append({
                "run_id": data.get("run_id", path.stem),
                "path_id": data.get("path_id"),
                "outcome": data.get("outcome"),
                "subsystem": data.get("subsystem"),
                "timestamp": data.get("timestamp"),
                "saved_at": data.get("saved_at"),
            })
        except Exception:
            pass
    return out
