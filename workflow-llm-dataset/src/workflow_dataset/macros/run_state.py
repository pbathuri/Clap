"""
M23P: Macro run state for pause/resume and checkpoint approval.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.copilot.config import get_runs_dir

STATUS_RUNNING = "running"
STATUS_PAUSED = "paused"
STATUS_AWAITING_APPROVAL = "awaiting_approval"
STATUS_BLOCKED = "blocked"
STATUS_COMPLETED = "completed"
STATUS_STOPPED = "stopped"

MACRO_RUN_STATE_FILE = "macro_run_state.json"


def _run_state_path(run_id: str, repo_root: Path | str | None) -> Path:
    root = Path(repo_root).resolve() if repo_root else None
    runs_dir = get_runs_dir(root)
    return runs_dir / run_id / MACRO_RUN_STATE_FILE


def save_run_state(
    run_id: str,
    macro_id: str,
    status: str,
    plan_id: str,
    job_pack_ids: list[str],
    mode: str,
    current_step_index: int,
    executed: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
    run_path: str,
    repo_root: Path | str | None = None,
    approval_required_before_step: int | None = None,
    timestamp: str = "",
) -> None:
    """Persist macro run state for resume."""
    root = Path(repo_root).resolve() if repo_root else None
    runs_dir = get_runs_dir(root)
    path = runs_dir / run_id
    path.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "macro_id": macro_id,
        "status": status,
        "plan_id": plan_id,
        "job_pack_ids": job_pack_ids,
        "mode": mode,
        "current_step_index": current_step_index,
        "executed": executed,
        "blocked": blocked,
        "run_path": run_path or str(path),
        "approval_required_before_step": approval_required_before_step,
        "timestamp": timestamp,
    }
    (path / MACRO_RUN_STATE_FILE).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_run_state(run_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load macro run state by run_id."""
    path = _run_state_path(run_id, repo_root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_paused_runs(repo_root: Path | str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """List runs with status paused."""
    return _list_runs_with_status(repo_root, [STATUS_PAUSED], limit)


def list_awaiting_approval_runs(repo_root: Path | str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """List runs with status awaiting_approval."""
    return _list_runs_with_status(repo_root, [STATUS_AWAITING_APPROVAL], limit)


def _list_runs_with_status(
    repo_root: Path | str | None,
    statuses: list[str],
    limit: int,
) -> list[dict[str, Any]]:
    runs_dir = get_runs_dir(repo_root)
    if not runs_dir.exists():
        return []
    out = []
    for d in sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not d.is_dir():
            continue
        f = d / MACRO_RUN_STATE_FILE
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("status") in statuses:
                data["run_path"] = str(d)
                out.append(data)
        except Exception:
            pass
        if len(out) >= limit:
            break
    return out


def list_all_macro_runs(repo_root: Path | str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """List recent runs that have macro_run_state.json (any status)."""
    runs_dir = get_runs_dir(repo_root)
    if not runs_dir.exists():
        return []
    out = []
    for d in sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not d.is_dir():
            continue
        f = d / MACRO_RUN_STATE_FILE
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["run_path"] = str(d)
            out.append(data)
        except Exception:
            pass
        if len(out) >= limit:
            break
    return out
