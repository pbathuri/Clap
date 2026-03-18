"""
M41I–M41L: Ops maintenance report — due, overdue, blocked, recent outcome, recommended action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.ops_jobs.cadence import list_due, list_overdue, next_due_utc
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


def build_ops_maintenance_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build ops maintenance report: next_due_job_id, due_jobs, overdue_jobs,
    blocked_job_id (if any), recent_outcome (last run across jobs), recommended_action.
    """
    root = _repo_root(repo_root)
    due = list_due(repo_root=root)
    overdue = list_overdue(repo_root=root)
    # Next due: first due job or first by next_due_utc among all
    next_due_job_id = ""
    if due:
        next_due_job_id = due[0].get("job_id", "")
    if not next_due_job_id:
        best: tuple[str, str] = ("", "9999-99-99")
        for jid in list_ops_job_ids():
            nd = next_due_utc(jid, repo_root=root)
            if nd and nd < best[1]:
                best = (jid, nd)
        next_due_job_id = best[0]

    # Blocked: job that has prerequisite failed (e.g. reliability_refresh when install check fails)
    blocked_job_id = ""
    for jid in list_ops_job_ids():
        job = get_ops_job(jid)
        if not job or not job.prerequisites:
            continue
        last = get_last_run(jid, repo_root=root)
        if last.get("outcome") == "blocked":
            blocked_job_id = jid
            break

    # Recent outcome: last run from history (any job)
    recent_outcome: dict[str, Any] = {}
    for jid in list_ops_job_ids():
        last = get_last_run(jid, repo_root=root)
        if last and last.get("finished_utc"):
            if not recent_outcome or (last.get("finished_utc", "") > recent_outcome.get("finished_utc", "")):
                recent_outcome = {"job_id": jid, **last}
    if not recent_outcome and due:
        recent_outcome = {"job_id": due[0].get("job_id"), "outcome": "due", "summary": "No run yet; job is due."}

    # Highest-value overdue: for now first overdue
    highest_value_overdue_id = overdue[0].get("job_id", "") if overdue else ""

    # Recommended action
    recommended_action = "workflow-dataset ops-jobs due"
    if blocked_job_id:
        job = get_ops_job(blocked_job_id)
        if job and job.escalation_targets:
            recommended_action = job.escalation_targets[0].command_hint or recommended_action
    elif next_due_job_id:
        recommended_action = f"workflow-dataset ops-jobs run --id {next_due_job_id}"

    return {
        "next_due_job_id": next_due_job_id,
        "due_jobs": due,
        "overdue_jobs": overdue,
        "blocked_job_id": blocked_job_id,
        "highest_value_overdue_id": highest_value_overdue_id,
        "recent_outcome": recent_outcome,
        "recommended_action": recommended_action,
    }


