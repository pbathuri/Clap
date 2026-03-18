"""
M24J–M24M: Session task board — active tasks, queued routines/macros, blocked, ready, completed, artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.session.models import Session
from workflow_dataset.session.artifacts import list_artifacts


@dataclass
class SessionBoard:
    """Live task board for a session: active, queued, blocked, ready, completed, artifacts."""
    active_tasks: list[dict[str, Any]] = field(default_factory=list)
    queued: list[dict[str, Any]] = field(default_factory=list)
    blocked: list[dict[str, Any]] = field(default_factory=list)
    ready: list[dict[str, Any]] = field(default_factory=list)
    completed: list[dict[str, Any]] = field(default_factory=list)
    artifacts_produced: list[dict[str, Any]] = field(default_factory=list)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_session_board(session: Session, repo_root: Path | str | None = None) -> SessionBoard:
    """
    Build the live task board for a session by aggregating from copilot, macros, job_packs, and session artifacts.
    """
    root = _repo_root(repo_root)
    board = SessionBoard()

    # Active: session's job/routine/macro ids as task labels
    for jid in session.active_job_ids or []:
        board.active_tasks.append({"kind": "job", "id": jid, "label": jid})
    for rid in session.active_routine_ids or []:
        board.active_tasks.append({"kind": "routine", "id": rid, "label": rid})
    for mid in session.active_macro_ids or []:
        board.active_tasks.append({"kind": "macro", "id": mid, "label": mid})
    for t in session.active_tasks or []:
        board.active_tasks.append({"kind": "task", "id": t, "label": t})

    # Queued: paused and awaiting_approval macro runs
    try:
        from workflow_dataset.macros.run_state import list_paused_runs, list_awaiting_approval_runs
        paused = list_paused_runs(root, limit=20)
        awaiting = list_awaiting_approval_runs(root, limit=20)
        session_macro_ids = set(session.active_macro_ids or [])
        for r in paused + awaiting:
            macro_id = r.get("macro_id", "")
            if macro_id in session_macro_ids or not session_macro_ids:
                board.queued.append({
                    "kind": "macro_run",
                    "run_id": r.get("run_id"),
                    "macro_id": macro_id,
                    "status": r.get("status", ""),
                })
    except Exception:
        pass

    # Blocked: macro blocked steps + copilot recommend jobs with blocking_issues that are in session
    try:
        from workflow_dataset.macros.runner import get_blocked_steps
        for mid in session.active_macro_ids or []:
            steps = get_blocked_steps(mid, run_id=None, repo_root=root)
            for s in steps[:10]:
                board.blocked.append({
                    "kind": "macro_step",
                    "macro_id": mid,
                    "step": s.get("step_index"),
                    "reason": s.get("reason", ""),
                })
    except Exception:
        pass
    try:
        from workflow_dataset.copilot.recommendations import recommend_jobs
        recs = recommend_jobs(root, limit=50)
        session_job_ids = set(session.active_job_ids or [])
        for r in recs:
            if r.get("blocking_issues") and (r.get("job_pack_id") in session_job_ids or not session_job_ids):
                board.blocked.append({
                    "kind": "job",
                    "id": r.get("job_pack_id"),
                    "reason": ", ".join(r.get("blocking_issues", [])),
                })
    except Exception:
        pass

    # Ready: pack jobs/routines/macros that exist and are not in blocked (by id)
    blocked_ids = {b.get("id") for b in board.blocked if b.get("id")}
    try:
        from workflow_dataset.job_packs import list_job_packs, get_job_pack
        from workflow_dataset.copilot.routines import list_routines, get_routine
        job_ids = list_job_packs(root)
        for jid in session.active_job_ids or []:
            if jid in blocked_ids:
                continue
            if get_job_pack(jid, root) is not None or jid in job_ids:
                board.ready.append({"kind": "job", "id": jid})
        routine_ids = list_routines(root)
        for rid in session.active_routine_ids or []:
            if rid in blocked_ids:
                continue
            if get_routine(rid, root) is not None or rid in routine_ids:
                board.ready.append({"kind": "routine", "id": rid})
        for mid in session.active_macro_ids or []:
            if mid in blocked_ids:
                continue
            if mid in routine_ids:
                board.ready.append({"kind": "macro", "id": mid})
    except Exception:
        pass

    # Completed: recent plan runs and macro runs (last 10)
    try:
        from workflow_dataset.copilot.run import list_plan_runs
        runs = list_plan_runs(limit=10, repo_root=root)
        for r in runs:
            board.completed.append({
                "kind": "plan_run",
                "run_id": r.get("run_id"),
                "job_pack_id": r.get("job_pack_id"),
                "outcome": r.get("outcome"),
            })
    except Exception:
        pass
    try:
        from workflow_dataset.macros.run_state import list_all_macro_runs
        macro_runs = list_all_macro_runs(root, limit=10)
        for r in macro_runs:
            if r.get("status") == "completed":
                board.completed.append({
                    "kind": "macro_run",
                    "run_id": r.get("run_id"),
                    "macro_id": r.get("macro_id"),
                })
    except Exception:
        pass

    # Artifacts produced this session
    artifacts = list_artifacts(session.session_id, root, limit=50)
    for a in artifacts:
        board.artifacts_produced.append({
            "path_or_label": a.get("path_or_label", ""),
            "kind": a.get("kind", "file"),
        })

    return board
