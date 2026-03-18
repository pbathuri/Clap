"""
M45C: Adaptive step progression — advance, branch on outcome, stop, escalate, switch fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.adaptive_execution.models import (
    BoundedExecutionLoop,
    StepOutcome,
    ExecutionStep,
)

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

from workflow_dataset.adaptive_execution.store import load_loop, save_loop


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _current_branch_steps(loop: BoundedExecutionLoop) -> list[int]:
    """Step indices for current branch in order."""
    if not loop.plan or not loop.current_branch_id:
        return list(range(len(loop.plan.steps))) if loop.plan else []
    for b in loop.plan.branches:
        if b.branch_id == loop.current_branch_id:
            return list(b.step_indices)
    return list(range(len(loop.plan.steps))) if loop.plan else []


def _next_takeover_index(loop: BoundedExecutionLoop) -> int | None:
    """Next required review step index after current."""
    for i in loop.required_review_step_indices:
        if i > loop.current_step_index:
            return i
    return None


def advance_step(
    loop_id: str,
    outcome: StepOutcome | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Advance the loop by one step; record outcome. Checks stop/escalation/adaptation.
    Returns { loop, status, message, stopped, escalated, branch_switched }.
    """
    root = _repo_root(repo_root)
    loop = load_loop(loop_id, root)
    if not loop:
        return {"error": f"Loop not found: {loop_id}", "loop": None}
    if loop.status not in ("running", "paused", "awaiting_takeover"):
        return {"loop": loop, "status": loop.status, "message": f"Loop is {loop.status}; cannot advance.", "stopped": False, "escalated": False, "branch_switched": False}

    if outcome:
        loop.outcomes.append(outcome)
        loop.steps_executed += 1

    # Check adaptation triggers before advancing (blocked -> fallback, low confidence -> fallback)
    if outcome and outcome.status == "blocked" and loop.plan and not loop.fallback_activated:
        for t in loop.plan.adaptation_triggers:
            if t.kind == "outcome_status" and t.outcome_status == "blocked" and t.branch_to_id:
                loop.current_branch_id = t.branch_to_id
                loop.fallback_activated = True
                loop.updated_at = utc_now_iso()
                save_loop(loop, root)
                return {"loop": loop, "status": loop.status, "message": f"Switched to fallback branch {t.branch_to_id}.", "stopped": False, "escalated": False, "branch_switched": True}

    if outcome and outcome.confidence < 0.5 and loop.plan and not loop.fallback_activated:
        for t in loop.plan.adaptation_triggers:
            if t.kind == "confidence_below" and outcome.confidence < t.confidence_threshold and t.branch_to_id:
                loop.current_branch_id = t.branch_to_id
                loop.fallback_activated = True
                loop.updated_at = utc_now_iso()
                save_loop(loop, root)
                return {"loop": loop, "status": loop.status, "message": f"Confidence low; switched to {t.branch_to_id}.", "stopped": False, "escalated": False, "branch_switched": True}

    branch_steps = _current_branch_steps(loop)
    if not branch_steps:
        loop.status = "stopped"
        loop.stop_reason = "no_steps_in_branch"
        loop.updated_at = utc_now_iso()
        save_loop(loop, root)
        return {"loop": loop, "status": "stopped", "message": "No steps in branch.", "stopped": True, "escalated": False, "branch_switched": False}

    current_idx = loop.current_step_index
    next_idx_pos = branch_steps.index(current_idx) + 1 if current_idx in branch_steps else 0
    if next_idx_pos >= len(branch_steps):
        loop.status = "completed"
        loop.updated_at = utc_now_iso()
        save_loop(loop, root)
        return {"loop": loop, "status": "completed", "message": "All steps in branch completed.", "stopped": False, "escalated": False, "branch_switched": False}

    next_step_index = branch_steps[next_idx_pos]

    if loop.steps_executed >= loop.max_steps:
        loop.status = "stopped"
        loop.stop_reason = "max_steps_reached"
        loop.updated_at = utc_now_iso()
        save_loop(loop, root)
        return {"loop": loop, "status": "stopped", "message": "Max steps reached.", "stopped": True, "escalated": False, "branch_switched": False}

    loop.current_step_index = next_step_index
    loop.next_takeover_step_index = _next_takeover_index(loop)
    loop.updated_at = utc_now_iso()

    if loop.next_takeover_step_index == next_step_index:
        loop.status = "awaiting_takeover"
        loop.escalation_reason = "review_required"
        save_loop(loop, root)
        return {"loop": loop, "status": "awaiting_takeover", "message": "At takeover point; human review required.", "stopped": False, "escalated": True, "branch_switched": False}

    save_loop(loop, root)
    return {"loop": loop, "status": loop.status, "message": f"Advanced to step {next_step_index}.", "stopped": False, "escalated": False, "branch_switched": False}


def stop_loop(
    loop_id: str,
    reason: str = "manual_stop",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Stop the loop; set status=stopped and stop_reason."""
    root = _repo_root(repo_root)
    loop = load_loop(loop_id, root)
    if not loop:
        return {"error": f"Loop not found: {loop_id}", "loop": None}
    loop.status = "stopped"
    loop.stop_reason = reason or "manual_stop"
    loop.updated_at = utc_now_iso()
    save_loop(loop, root)
    return {"loop": loop, "status": "stopped", "message": loop.stop_reason}


def escalate_loop(
    loop_id: str,
    reason: str = "blocked",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Escalate the loop; set status=escalated and escalation_reason."""
    root = _repo_root(repo_root)
    loop = load_loop(loop_id, root)
    if not loop:
        return {"error": f"Loop not found: {loop_id}", "loop": None}
    loop.status = "escalated"
    loop.escalation_reason = reason or "blocked"
    loop.updated_at = utc_now_iso()
    save_loop(loop, root)
    return {"loop": loop, "status": "escalated", "message": loop.escalation_reason}


def record_takeover_decision(
    loop_id: str,
    decision: str = "proceed",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """After human review at a takeover point: proceed | cancel | defer. If proceed, advance remains possible."""
    root = _repo_root(repo_root)
    loop = load_loop(loop_id, root)
    if not loop:
        return {"error": f"Loop not found: {loop_id}", "loop": None}
    if decision == "cancel":
        loop.status = "stopped"
        loop.stop_reason = "operator_cancelled"
    elif decision == "defer":
        loop.status = "paused"
        loop.escalation_reason = "deferred"
    else:
        loop.status = "running"
        loop.escalation_reason = ""
    loop.updated_at = utc_now_iso()
    save_loop(loop, root)
    return {"loop": loop, "status": loop.status, "message": f"Takeover decision: {decision}"}
