"""
M36A–M36D: Workday state machine — valid transitions, entry/exit conditions, blocked reasons.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.workday.models import (
    WorkdayState,
    WorkdayStateRecord,
    StateTransition,
    BlockedStateInfo,
)

# Valid transitions: from_state -> list of to_state
VALID_TRANSITIONS: dict[str, list[str]] = {
    WorkdayState.NOT_STARTED.value: [WorkdayState.STARTUP.value],
    WorkdayState.STARTUP.value: [
        WorkdayState.FOCUS_WORK.value,
        WorkdayState.REVIEW_AND_APPROVALS.value,
        WorkdayState.OPERATOR_MODE.value,
        WorkdayState.WRAP_UP.value,
        WorkdayState.SHUTDOWN.value,
    ],
    WorkdayState.FOCUS_WORK.value: [
        WorkdayState.REVIEW_AND_APPROVALS.value,
        WorkdayState.OPERATOR_MODE.value,
        WorkdayState.WRAP_UP.value,
        WorkdayState.SHUTDOWN.value,
    ],
    WorkdayState.REVIEW_AND_APPROVALS.value: [
        WorkdayState.FOCUS_WORK.value,
        WorkdayState.OPERATOR_MODE.value,
        WorkdayState.WRAP_UP.value,
        WorkdayState.SHUTDOWN.value,
    ],
    WorkdayState.OPERATOR_MODE.value: [
        WorkdayState.FOCUS_WORK.value,
        WorkdayState.REVIEW_AND_APPROVALS.value,
        WorkdayState.WRAP_UP.value,
        WorkdayState.SHUTDOWN.value,
    ],
    WorkdayState.WRAP_UP.value: [
        WorkdayState.SHUTDOWN.value,
        WorkdayState.FOCUS_WORK.value,
        WorkdayState.REVIEW_AND_APPROVALS.value,
    ],
    WorkdayState.SHUTDOWN.value: [],  # terminal for the day
    WorkdayState.RESUME_PENDING.value: [WorkdayState.STARTUP.value],
}


def can_transition(
    from_state: str,
    to_state: str,
    context: dict[str, Any] | None = None,
) -> tuple[bool, list[BlockedStateInfo]]:
    """
    Check if transition from_state -> to_state is allowed.
    Returns (allowed, list of block reasons). Block reasons may include entry conditions (e.g. operator_mode blocked if paused).
    """
    context = context or {}
    blocked: list[BlockedStateInfo] = []
    allowed = VALID_TRANSITIONS.get(from_state, [])
    if to_state not in allowed:
        blocked.append(
            BlockedStateInfo(
                from_state=from_state,
                to_state=to_state,
                reason=f"Transition from {from_state} to {to_state} is not allowed. Allowed: {allowed}",
            )
        )
        return False, blocked
    # Entry conditions for operator_mode: e.g. not paused (optional check)
    if to_state == WorkdayState.OPERATOR_MODE.value:
        if context.get("operator_mode_paused"):
            blocked.append(
                BlockedStateInfo(
                    from_state=from_state,
                    to_state=to_state,
                    reason="Operator mode is paused; clear pause before entering operator_mode.",
                )
            )
            return False, blocked
    return True, blocked


def entry_conditions(to_state: str) -> list[str]:
    """Human-readable entry conditions for to_state."""
    if to_state == WorkdayState.OPERATOR_MODE.value:
        return ["Operator mode must not be paused."]
    if to_state == WorkdayState.STARTUP.value:
        return ["None."]
    return []


def exit_conditions(from_state: str) -> list[str]:
    """Human-readable exit conditions for from_state."""
    return []


def gather_context(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Gather context for transition checks (e.g. operator_mode_paused)."""
    ctx: dict[str, Any] = {}
    try:
        root = Path(repo_root).resolve() if repo_root else Path.cwd()
        from workflow_dataset.operator_mode import load_pause_state
        pause = load_pause_state(root)
        ctx["operator_mode_paused"] = bool(pause and getattr(pause, "paused", False))
    except Exception:
        ctx["operator_mode_paused"] = False
    return ctx


def blocked_reasons(
    from_state: str,
    to_state: str,
    context: dict[str, Any] | None = None,
) -> list[str]:
    """List of reason strings why transition is blocked."""
    ok, infos = can_transition(from_state, to_state, context)
    return [i.reason for i in infos]


def apply_transition(
    record: WorkdayStateRecord,
    to_state: str,
    trigger: str,
    at_iso: str,
    context: dict[str, Any] | None = None,
) -> WorkdayStateRecord | None:
    """
    Apply transition; returns new record or None if transition invalid.
    Does not persist; caller saves.
    """
    ok, blocked = can_transition(record.state, to_state, context)
    if not ok:
        return None
    new_record = WorkdayStateRecord(
        state=to_state,
        entered_at_iso=at_iso,
        previous_state=record.state,
        day_started_at_iso=record.day_started_at_iso if record.day_started_at_iso else at_iso,
        transition_history=record.transition_history
        + [StateTransition(from_state=record.state, to_state=to_state, at_iso=at_iso, trigger=trigger)],
        day_id=record.day_id,
    )
    return new_record
