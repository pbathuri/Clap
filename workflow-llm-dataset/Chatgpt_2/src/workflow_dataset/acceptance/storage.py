"""
M24C: Persist acceptance runs to data/local/acceptance/runs/. Read/write run results.
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


ACCEPTANCE_DIR = "data/local/acceptance"
RUNS_SUBDIR = "runs"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_runs_dir(repo_root: Path | str | None = None) -> Path:
    """Return path to acceptance runs directory."""
    return _repo_root(repo_root) / ACCEPTANCE_DIR / RUNS_SUBDIR


def _run_id() -> str:
    t = utc_now_iso().replace(":", "-").replace(".", "-").replace("+", "-")[:23]
    return f"run_{t}"


def save_run(
    run_result: dict[str, Any],
    repo_root: Path | str | None = None,
) -> Path:
    """Save run result to data/local/acceptance/runs/<run_id>.json. Returns path to file."""
    root = _repo_root(repo_root)
    runs_dir = get_runs_dir(root)
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = run_result.get("run_id") or _run_id()
    run_result["run_id"] = run_id
    run_result["saved_at"] = utc_now_iso()
    path = runs_dir / f"{run_id}.json"
    # Serialize steps_results (may contain non-JSON-safe types in actual)
    out = {
        "run_id": run_result.get("run_id"),
        "scenario_id": run_result.get("scenario_id"),
        "scenario_name": run_result.get("scenario_name"),
        "outcome": run_result.get("outcome"),
        "reasons": run_result.get("reasons", []),
        "ready_for_trial": run_result.get("ready_for_trial"),
        "saved_at": run_result.get("saved_at"),
        "steps_results": [
            {"step_id": s.get("step_id"), "actual": s.get("actual")}
            for s in run_result.get("steps_results", [])
        ],
    }
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return path


def load_latest_run(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load most recent run from runs dir. Returns None if no runs."""
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


def list_runs(repo_root: Path | str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """List run summaries (run_id, scenario_id, outcome, saved_at)."""
    runs_dir = get_runs_dir(repo_root)
    if not runs_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            out.append({
                "run_id": data.get("run_id", path.stem),
                "scenario_id": data.get("scenario_id"),
                "outcome": data.get("outcome"),
                "saved_at": data.get("saved_at"),
            })
        except Exception:
            pass
    return out
