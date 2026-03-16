"""
M21Z: Experiment definitions and queue. Local-only; no auto-apply.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.devlab.config import get_experiments_dir, get_experiment_queue_path, get_devlab_root
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def load_experiment(experiment_id: str, root: Path | str | None = None) -> dict[str, Any] | None:
    """Load experiment definition by id. Expects experiments/<id>.json."""
    exp_dir = get_experiments_dir(root)
    path = exp_dir / f"{experiment_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_experiment(definition: dict[str, Any], root: Path | str | None = None) -> Path:
    """Save experiment definition. Uses definition['id'] for filename."""
    exp_id = definition.get("id", "unnamed")
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in exp_id).strip("_") or "exp"
    exp_dir = get_experiments_dir(root)
    path = exp_dir / f"{safe_id}.json"
    path.write_text(json.dumps(definition, indent=2), encoding="utf-8")
    return path


def list_experiments(root: Path | str | None = None) -> list[dict[str, Any]]:
    """List all experiment definitions."""
    exp_dir = get_experiments_dir(root)
    out: list[dict[str, Any]] = []
    for p in sorted(exp_dir.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def load_queue(root: Path | str | None = None) -> list[dict[str, Any]]:
    """Load experiment queue: list of {experiment_id, status, run_id?, proposal_id?, queued_at?, completed_at?}."""
    path = get_experiment_queue_path(root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_queue(items: list[dict[str, Any]], root: Path | str | None = None) -> Path:
    """Save experiment queue."""
    path = get_experiment_queue_path(root)
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")
    return path


def queue_experiment(experiment_id: str, root: Path | str | None = None) -> dict[str, Any]:
    """Add experiment to queue as queued. Returns queue entry."""
    q = load_queue(root)
    for e in q:
        if e.get("experiment_id") == experiment_id and e.get("status") in ("queued", "running"):
            return e
    entry = {
        "experiment_id": experiment_id,
        "status": "queued",
        "queued_at": utc_now_iso(),
        "run_id": None,
        "proposal_id": None,
        "completed_at": None,
    }
    q.append(entry)
    save_queue(q, root)
    return entry


def update_queue_entry(experiment_id: str, status: str, run_id: str | None = None, proposal_id: str | None = None, root: Path | str | None = None) -> None:
    """Update the most recent queue entry for experiment_id."""
    q = load_queue(root)
    for i in range(len(q) - 1, -1, -1):
        if q[i].get("experiment_id") == experiment_id:
            q[i]["status"] = status
            if run_id is not None:
                q[i]["run_id"] = run_id
            if proposal_id is not None:
                q[i]["proposal_id"] = proposal_id
            if status in ("done", "failed"):
                q[i]["completed_at"] = utc_now_iso()
            save_queue(q, root)
            return
    # No existing entry; add one
    entry = {"experiment_id": experiment_id, "status": status, "queued_at": utc_now_iso(), "run_id": run_id, "proposal_id": proposal_id, "completed_at": utc_now_iso() if status in ("done", "failed") else None}
    q.append(entry)
    save_queue(q, root)


def seed_default_experiment(root: Path | str | None = None) -> dict[str, Any]:
    """Write a default experiment definition if none exist. Returns the definition."""
    exp_dir = get_experiments_dir(root)
    default_id = "ops_reporting_benchmark"
    path = exp_dir / f"{default_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    definition = {
        "id": default_id,
        "goal": "Run ops_reporting_core benchmark and produce a patch proposal for review.",
        "workflow_target": "weekly_status",
        "benchmark_suite": "ops_reporting_core",
        "provider_model_variants": [],
        "expected_success_metric": "Benchmark scores computed; proposal generated for operator review.",
    }
    save_experiment(definition, root)
    return definition


def get_queue_status(root: Path | str | None = None) -> dict[str, Any]:
    """Summary: queued count, running count, last run."""
    q = load_queue(root)
    queued = sum(1 for e in q if e.get("status") == "queued")
    running = sum(1 for e in q if e.get("status") == "running")
    done = sum(1 for e in q if e.get("status") == "done")
    failed = sum(1 for e in q if e.get("status") == "failed")
    cancelled = sum(1 for e in q if e.get("status") == "cancelled")
    last = q[-1] if q else None
    return {"queued": queued, "running": running, "done": done, "failed": failed, "cancelled": cancelled, "total": len(q), "last": last}


def _sort_entries_newest_first(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort queue entries by most recent first (completed_at or queued_at)."""
    def key(e: dict[str, Any]) -> str:
        t = e.get("completed_at") or e.get("queued_at") or ""
        return t
    return sorted(entries, key=key, reverse=True)


def list_recent_runs(limit: int = 20, root: Path | str | None = None) -> list[dict[str, Any]]:
    """List recent run history (queue entries) newest first. Each entry has experiment_id, status, queued_at, run_id, proposal_id, completed_at."""
    q = load_queue(root)
    ordered = _sort_entries_newest_first(q)
    out = ordered[:limit]
    for i, e in enumerate(out):
        e["_index"] = i  # 0 = most recent
    return out


def get_run_entry(
    *,
    run_id: str | None = None,
    experiment_id: str | None = None,
    index: int | None = None,
    root: Path | str | None = None,
) -> dict[str, Any] | None:
    """Get one queue entry by run_id, or latest for experiment_id, or by history index (0=most recent)."""
    q = load_queue(root)
    if run_id is not None:
        for e in q:
            if e.get("run_id") == run_id:
                return e
        return None
    if index is not None:
        ordered = _sort_entries_newest_first(q)
        if 0 <= index < len(ordered):
            out = dict(ordered[index])
            out["_index"] = index
            return out
        return None
    if experiment_id is not None:
        matches = [e for e in q if e.get("experiment_id") == experiment_id]
        if not matches:
            return None
        ordered = sorted(matches, key=lambda e: e.get("completed_at") or e.get("queued_at") or "", reverse=True)
        out = dict(ordered[0])
        out["_index"] = None
        return out
    return None


def cancel_queued(experiment_id: str, root: Path | str | None = None) -> bool:
    """Cancel the oldest queued entry for experiment_id. Returns True if one was cancelled."""
    q = load_queue(root)
    for e in q:
        if e.get("experiment_id") == experiment_id and e.get("status") == "queued":
            e["status"] = "cancelled"
            e["completed_at"] = utc_now_iso()
            save_queue(q, root)
            return True
    return False


def cancel_queued_by_index(index: int, root: Path | str | None = None) -> bool:
    """Cancel the queue entry at history index (0=most recent). Only cancels if status is queued."""
    q = load_queue(root)
    ordered = _sort_entries_newest_first(q)
    if index < 0 or index >= len(ordered):
        return False
    entry = ordered[index]
    if entry.get("status") != "queued":
        return False
    # Update in-place in q (same ref)
    for e in q:
        if e.get("queued_at") == entry.get("queued_at") and e.get("experiment_id") == entry.get("experiment_id"):
            e["status"] = "cancelled"
            e["completed_at"] = utc_now_iso()
            save_queue(q, root)
            return True
    return False


def run_next_queued(root: Path | str | None = None) -> dict[str, Any]:
    """Run one next queued experiment (first in queue order with status queued). No perpetual loop; returns after one run."""
    q = load_queue(root)
    for e in q:
        if e.get("status") == "queued":
            experiment_id = e.get("experiment_id", "")
            from workflow_dataset.devlab.experiment_runner import run_experiment
            result = run_experiment(experiment_id, root)
            return {"ran": True, "experiment_id": experiment_id, "result": result}
    return {"ran": False, "reason": "no_queued"}
