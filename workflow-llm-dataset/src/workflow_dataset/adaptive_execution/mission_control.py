"""
M45D: Mission control slice — active loop, next step, remaining steps, takeover point, branch/fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.adaptive_execution.store import list_active_loops, load_loop


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def adaptive_execution_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Mission-control slice for adaptive execution: active loop id, next step, remaining safe steps,
    next takeover/review point, current branch, fallback state.
    """
    root = _repo_root(repo_root)
    running = list_active_loops(status_filter="running", repo_root=root, limit=5)
    awaiting = list_active_loops(status_filter="awaiting_takeover", repo_root=root, limit=5)
    active_loop_id = (running[0].get("loop_id") if running else None) or (awaiting[0].get("loop_id") if awaiting else None)

    out: dict[str, Any] = {
        "active_loop_id": active_loop_id,
        "running_loop_count": len(running),
        "awaiting_takeover_count": len(awaiting),
        "next_step_index": None,
        "remaining_safe_steps": None,
        "next_takeover_step_index": None,
        "current_branch_id": None,
        "fallback_activated": False,
        "stop_reason": None,
        "escalation_reason": None,
    }

    if active_loop_id:
        loop = load_loop(active_loop_id, root)
        if loop:
            out["next_step_index"] = loop.current_step_index
            out["current_branch_id"] = loop.current_branch_id
            out["fallback_activated"] = loop.fallback_activated
            out["next_takeover_step_index"] = loop.next_takeover_step_index
            out["stop_reason"] = loop.stop_reason or None
            out["escalation_reason"] = loop.escalation_reason or None
            if loop.max_steps > 0 and loop.steps_executed is not None:
                out["remaining_safe_steps"] = max(0, loop.max_steps - loop.steps_executed)

    return out
