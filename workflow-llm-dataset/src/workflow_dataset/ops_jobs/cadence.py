"""
M41I–M41L: Ops job cadence — next due, list due, list overdue.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from workflow_dataset.ops_jobs.registry import get_ops_job, list_ops_job_ids
from workflow_dataset.ops_jobs.store import get_last_run


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _parse_utc(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def next_due_utc(job_id: str, repo_root: Path | str | None = None) -> str:
    """Return next due time (ISO) for job_id; empty if no cadence or never due."""
    job = get_ops_job(job_id)
    if not job or (job.cadence.interval_hours <= 0 and job.cadence.interval_days <= 0):
        return ""
    root = _repo_root(repo_root)
    last = get_last_run(job_id, repo_root=root)
    last_utc = _parse_utc(last.get("started_utc", "") or last.get("finished_utc", ""))
    now = datetime.now(timezone.utc)
    if not last_utc:
        return now.isoformat()[:19] + "Z"
    base = last_utc
    if job.cadence.interval_days > 0:
        next_due = base + timedelta(days=job.cadence.interval_days)
    else:
        next_due = base + timedelta(hours=job.cadence.interval_hours)
    if next_due <= now:
        return now.isoformat()[:19] + "Z"
    return next_due.isoformat()[:19] + "Z"


def list_due(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Return jobs that are due (next_due <= now) with next_due_utc and job_id."""
    root = _repo_root(repo_root)
    now = datetime.now(timezone.utc)
    out: list[dict[str, Any]] = []
    for jid in list_ops_job_ids():
        next_due = next_due_utc(jid, repo_root=root)
        if not next_due:
            continue
        nd = _parse_utc(next_due)
        if nd and nd <= now:
            job = get_ops_job(jid)
            out.append({
                "job_id": jid,
                "name": job.name if job else jid,
                "next_due_utc": next_due,
            })
    return out


def list_overdue(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Same as list_due for now (overdue = due and not run). Could later add threshold."""
    return list_due(repo_root=repo_root)
