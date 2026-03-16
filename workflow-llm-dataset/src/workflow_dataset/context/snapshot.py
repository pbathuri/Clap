"""
M23L: Context snapshot persistence. Save/load work-state snapshots; no background refresh.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from workflow_dataset.context.config import (
    get_context_root,
    get_snapshots_dir,
    get_latest_snapshot_path,
    get_previous_snapshot_path,
)
from workflow_dataset.context.work_state import (
    WorkState,
    work_state_to_dict,
    work_state_summary_md,
)


def _work_state_from_dict(d: dict[str, Any]) -> WorkState:
    from workflow_dataset.context.work_state import WorkState
    return WorkState(
        snapshot_id=str(d.get("snapshot_id", "")),
        created_at=str(d.get("created_at", "")),
        recent_successful_jobs=list(d.get("recent_successful_jobs", [])),
        trusted_for_real_jobs=list(d.get("trusted_for_real_jobs", [])),
        approval_blocked_jobs=list(d.get("approval_blocked_jobs", [])),
        simulate_only_jobs=list(d.get("simulate_only_jobs", [])),
        jobs_with_failure_notes=list(d.get("jobs_with_failure_notes", [])),
        intake_labels=list(d.get("intake_labels", [])),
        intake_summary=list(d.get("intake_summary", [])),
        recent_workspaces_count=int(d.get("recent_workspaces_count", 0)),
        unreviewed_count=int(d.get("unreviewed_count", 0)),
        package_pending_count=int(d.get("package_pending_count", 0)),
        recent_workspaces_sample=list(d.get("recent_workspaces_sample", [])),
        approvals_file_exists=bool(d.get("approvals_file_exists", False)),
        approved_paths_count=int(d.get("approved_paths_count", 0)),
        approved_action_scopes_count=int(d.get("approved_action_scopes_count", 0)),
        adapter_ids=list(d.get("adapter_ids", [])),
        reminders_count=int(d.get("reminders_count", 0)),
        reminders_due_sample=list(d.get("reminders_due_sample", [])),
        routines_count=int(d.get("routines_count", 0)),
        routine_ids=list(d.get("routine_ids", [])),
        recent_plan_runs_count=int(d.get("recent_plan_runs_count", 0)),
        recent_plan_runs_sample=list(d.get("recent_plan_runs_sample", [])),
        task_demos_count=int(d.get("task_demos_count", 0)),
        errors=dict(d.get("errors", {})),
    )


def save_snapshot(
    work_state: WorkState,
    repo_root: Path | str | None = None,
    snapshot_id: str | None = None,
) -> Path:
    """
    Persist work-state snapshot. Writes timestamped file in snapshots/, latest.json, and work_state_summary.md.
    If snapshot_id not provided, use created_at (sanitized) as id.
    """
    root = get_context_root(repo_root)
    snap_dir = get_snapshots_dir(repo_root)
    sid = snapshot_id or work_state.created_at.replace(":", "").replace("-", "")[:14]
    work_state.snapshot_id = sid

    data = work_state_to_dict(work_state)
    # Timestamped file
    ts_path = snap_dir / f"snapshot_{sid}.json"
    ts_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # latest.json
    latest_path = get_latest_snapshot_path(repo_root)
    prev_path = get_previous_snapshot_path(repo_root)
    if latest_path.exists():
        shutil.copy2(latest_path, prev_path)
    latest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Summary markdown
    summary_path = root / "work_state_summary.md"
    summary_path.write_text(work_state_summary_md(work_state), encoding="utf-8")
    return ts_path


def load_snapshot(
    snapshot_id: str = "latest",
    repo_root: Path | str | None = None,
) -> WorkState | None:
    """Load snapshot by id ('latest' or timestamp id) or from snapshots/snapshot_<id>.json."""
    root = get_context_root(repo_root)
    snap_dir = get_snapshots_dir(repo_root)
    if snapshot_id == "latest":
        path = get_latest_snapshot_path(repo_root)
    elif snapshot_id == "previous":
        path = get_previous_snapshot_path(repo_root)
    else:
        path = snap_dir / f"snapshot_{snapshot_id}.json"
        if not path.exists():
            path = root / f"{snapshot_id}.json"
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _work_state_from_dict(data)
    except Exception:
        return None


def list_snapshots(
    limit: int = 20,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List snapshot ids and created_at from snapshots dir (newest first)."""
    snap_dir = get_snapshots_dir(repo_root)
    out = []
    for f in sorted(snap_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.suffix != ".json" or not f.name.startswith("snapshot_"):
            continue
        sid = f.stem.replace("snapshot_", "")
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out.append({"snapshot_id": sid, "created_at": data.get("created_at", "")})
        except Exception:
            out.append({"snapshot_id": sid, "created_at": ""})
        if len(out) >= limit:
            break
    return out
