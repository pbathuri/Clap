"""
M27E–M27H: Execution handoff — run approved action via executor/planner, record result, update cycle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]

from workflow_dataset.supervised_loop.models import (
    AgentCycle,
    ApprovalQueueItem,
    ExecutionHandoff,
    LOOP_STATUS_EXECUTING,
    LOOP_STATUS_AWAITING_APPROVAL,
    LOOP_STATUS_COMPLETED,
    LOOP_STATUS_BLOCKED,
    LOOP_STATUS_IDLE,
)
from workflow_dataset.supervised_loop.store import (
    load_cycle,
    save_cycle,
    load_queue,
    append_handoff,
)
from workflow_dataset.supervised_loop.queue import get_item


def execute_approved(
    queue_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Execute the approved action for queue_id: call executor or planner, record handoff, update cycle.
    Returns dict with handoff_id, run_id, status, outcome_summary, error (if any).
    """
    root = Path(repo_root).resolve() if repo_root else None
    item = get_item(queue_id, root)
    if not item:
        return {"error": f"Queue item not found: {queue_id}"}
    if item.status != "approved":
        return {"error": f"Queue item not approved (status={item.status})", "queue_id": queue_id}

    act = item.action
    handoff_id = stable_id("h", queue_id, utc_now_iso(), prefix="h_")
    handoff = ExecutionHandoff(
        handoff_id=handoff_id,
        queue_id=queue_id,
        cycle_id=item.cycle_id,
        action_type=act.action_type,
        plan_ref=act.plan_ref,
        plan_source=act.plan_source,
        mode=act.mode,
        started_at=utc_now_iso(),
    )

    cycle = load_cycle(root)
    if cycle:
        cycle.status = LOOP_STATUS_EXECUTING
        cycle.updated_at = utc_now_iso()
        save_cycle(cycle, root)

    if act.action_type == "executor_run":
        from workflow_dataset.executor.runner import run_with_checkpoints
        result = run_with_checkpoints(
            plan_source=act.plan_source,
            plan_ref=act.plan_ref,
            mode=act.mode,
            repo_root=root,
            stop_at_checkpoints=True,
        )
        handoff.run_id = result.get("run_id", "")
        handoff.status = result.get("status", "completed")
        handoff.outcome_summary = f"executed={result.get('executed_count', 0)} blocked={result.get('blocked_count', 0)}"
        handoff.error = result.get("error", "")
        handoff.ended_at = utc_now_iso()
        if result.get("message"):
            handoff.outcome_summary += " " + result["message"]
        if handoff.run_id:
            from workflow_dataset.executor.hub import load_run as load_exec_run
            er = load_exec_run(handoff.run_id, root)
            if er:
                handoff.artifact_paths = list(er.artifacts)
        if cycle:
            cycle.last_run_id = handoff.run_id
            cycle.last_handoff_id = handoff_id
            cycle.status = LOOP_STATUS_AWAITING_APPROVAL if handoff.status == "awaiting_approval" else (LOOP_STATUS_BLOCKED if handoff.status == "blocked" else LOOP_STATUS_COMPLETED)
            cycle.updated_at = utc_now_iso()
            save_cycle(cycle, root)

    elif act.action_type == "executor_resume":
        from workflow_dataset.executor.hub import list_runs, load_run
        from workflow_dataset.executor.runner import resume_run
        runs = list_runs(limit=10, repo_root=root)
        run_id = ""
        for r in runs:
            if r.get("status") == "awaiting_approval":
                run_id = r.get("run_id", "")
                break
        if not run_id:
            handoff.status = "error"
            handoff.error = "No run awaiting approval"
            handoff.ended_at = utc_now_iso()
            append_handoff(handoff, root)
            if cycle:
                cycle.status = LOOP_STATUS_IDLE
                cycle.updated_at = utc_now_iso()
                save_cycle(cycle, root)
            return {"handoff_id": handoff_id, "error": handoff.error, "status": "error"}
        result = resume_run(run_id, "proceed", root)
        handoff.run_id = run_id
        handoff.status = result.get("status", "completed")
        handoff.outcome_summary = result.get("message", "") or f"resumed run {run_id}"
        handoff.error = result.get("error", "")
        handoff.ended_at = utc_now_iso()
        if cycle:
            cycle.last_run_id = run_id
            cycle.last_handoff_id = handoff_id
            cycle.status = LOOP_STATUS_AWAITING_APPROVAL if handoff.status == "awaiting_approval" else LOOP_STATUS_COMPLETED
            cycle.updated_at = utc_now_iso()
            save_cycle(cycle, root)

    elif act.action_type == "planner_compile":
        from workflow_dataset.planner.compile import compile_goal_to_plan
        from workflow_dataset.planner.store import load_current_goal, save_latest_plan
        goal = load_current_goal(root)
        plan = compile_goal_to_plan(goal or "", root, mode=act.mode or "simulate")
        save_latest_plan(plan, root)
        handoff.status = "completed"
        handoff.outcome_summary = f"plan_id={plan.plan_id} steps={len(plan.steps)}"
        handoff.ended_at = utc_now_iso()
        if cycle:
            cycle.plan_id = plan.plan_id
            cycle.last_handoff_id = handoff_id
            cycle.status = LOOP_STATUS_COMPLETED
            cycle.updated_at = utc_now_iso()
            save_cycle(cycle, root)

    else:
        handoff.status = "error"
        handoff.error = f"Unknown action_type: {act.action_type}"
        handoff.ended_at = utc_now_iso()
        if cycle:
            cycle.status = LOOP_STATUS_IDLE
            cycle.updated_at = utc_now_iso()
            save_cycle(cycle, root)

    append_handoff(handoff, root)
    return {
        "handoff_id": handoff_id,
        "run_id": handoff.run_id,
        "status": handoff.status,
        "outcome_summary": handoff.outcome_summary,
        "error": handoff.error or "",
        "artifact_paths": handoff.artifact_paths,
    }
