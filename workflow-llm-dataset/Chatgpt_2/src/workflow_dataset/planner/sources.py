"""
M26B: Gather planning inputs from session, jobs, routines, macros, task demos, context, packs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def gather_planning_sources(
    repo_root: Path | str | None = None,
    project_id: str = "",
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Load session, work state, job recommendations, routines, macros, task demos, pack behavior summary.
    If project_id (or session_id) is provided, enriches with memory_context and memory_prior_cases (M44).
    Returns a single dict for the compiler to use. No network; read-only.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "session": None,
        "session_board": None,
        "work_state": None,
        "job_recommendations": [],
        "job_pack_ids": [],
        "routines": [],
        "routine_ids": [],
        "macros": [],
        "macro_ids": [],
        "task_demos": [],
        "task_ids": [],
        "pack_summary": {},
        "errors": [],
    }

    # Current session and board
    try:
        from workflow_dataset.session import get_current_session, build_session_board
        session = get_current_session(root)
        if session:
            out["session"] = session.to_dict() if hasattr(session, "to_dict") else {"session_id": session.session_id, "value_pack_id": getattr(session, "value_pack_id", ""), "active_job_ids": getattr(session, "active_job_ids", []) or [], "active_routine_ids": getattr(session, "active_routine_ids", []) or [], "active_macro_ids": getattr(session, "active_macro_ids", []) or [], "active_tasks": getattr(session, "active_tasks", []) or []}
            out["session_board"] = _board_to_dict(build_session_board(session, root))
    except Exception as e:
        out["errors"].append(f"session: {e}")

    # Work state
    try:
        from workflow_dataset.context.work_state import build_work_state
        state = build_work_state(root)
        out["work_state"] = {
            "recent_successful_jobs": getattr(state, "recent_successful_jobs", [])[:15],
            "trusted_for_real_jobs": getattr(state, "trusted_for_real_jobs", []),
            "routine_ids": getattr(state, "routine_ids", []),
            "task_demos_count": getattr(state, "task_demos_count", 0),
        }
    except Exception as e:
        out["errors"].append(f"work_state: {e}")

    # Job recommendations and job pack ids
    try:
        from workflow_dataset.copilot.recommendations import recommend_jobs
        from workflow_dataset.job_packs import list_job_packs
        out["job_recommendations"] = recommend_jobs(root, limit=30)
        out["job_pack_ids"] = list_job_packs(root)
    except Exception as e:
        out["errors"].append(f"jobs: {e}")

    # Routines
    try:
        from workflow_dataset.copilot.routines import list_routines, get_routine, get_ordered_job_ids
        routine_ids = list_routines(root)
        out["routine_ids"] = routine_ids
        for rid in routine_ids[:20]:
            r = get_routine(rid, root)
            if r:
                out["routines"].append({
                    "routine_id": r.routine_id,
                    "title": getattr(r, "title", ""),
                    "description": getattr(r, "description", ""),
                    "job_pack_ids": get_ordered_job_ids(r) if hasattr(r, "job_pack_ids") else getattr(r, "job_pack_ids", []),
                })
    except Exception as e:
        out["errors"].append(f"routines: {e}")

    # Macros (one per routine)
    try:
        from workflow_dataset.macros.runner import list_macros
        from workflow_dataset.copilot.routines import get_ordered_job_ids, get_routine
        for macro in list_macros(root)[:20]:
            out["macro_ids"].append(macro.macro_id)
            job_ids = get_ordered_job_ids(get_routine(macro.macro_id, root)) if get_routine(macro.macro_id, root) else (macro.job_pack_ids or [])
            out["macros"].append({
                "macro_id": macro.macro_id,
                "title": macro.title,
                "job_pack_ids": job_ids or macro.job_pack_ids or [],
                "routine_id": macro.routine_id or macro.macro_id,
            })
    except Exception as e:
        out["errors"].append(f"macros: {e}")

    # Task demos
    try:
        from workflow_dataset.task_demos.store import list_tasks, get_task
        out["task_ids"] = list_tasks(root)
        for tid in out["task_ids"][:20]:
            t = get_task(tid, root)
            if t:
                out["task_demos"].append({
                    "task_id": t.task_id,
                    "notes": getattr(t, "notes", ""),
                    "steps_count": len(getattr(t, "steps", [])),
                })
    except Exception as e:
        out["errors"].append(f"task_demos: {e}")

    # Pack behavior summary (winning pack, active)
    try:
        from workflow_dataset.packs.behavior_resolver import get_active_behavior_summary
        packs_dir = root / "data/local/packs"
        if packs_dir.exists():
            summary = get_active_behavior_summary(packs_dir=packs_dir)
            out["pack_summary"] = {
                "winning_pack_id": summary.get("winning_pack_id", ""),
                "active_pack_ids": summary.get("active_pack_ids", []),
                "primary_pack_id": summary.get("primary_pack_id", ""),
            }
    except Exception as e:
        out["errors"].append(f"packs: {e}")

    # M44: optional memory enrichment for planner context
    if project_id or session_id:
        try:
            from workflow_dataset.memory_intelligence.planner_enrichment import enrich_planning_sources
            out = enrich_planning_sources(out, project_id=project_id, session_id=session_id, repo_root=root)
        except Exception as e:
            out["errors"].append(f"memory_enrichment: {e}")

    return out


def _board_to_dict(board: Any) -> dict[str, Any]:
    return {
        "active_tasks": getattr(board, "active_tasks", []) or [],
        "queued": getattr(board, "queued", []) or [],
        "blocked": getattr(board, "blocked", []) or [],
        "ready": getattr(board, "ready", []) or [],
        "completed": getattr(board, "completed", []) or [],
    }
