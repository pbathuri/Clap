"""
M36A–M36D: CLI helpers for day status, start, mode, wrap-up, shutdown, resume.
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

from workflow_dataset.workday.models import WorkdayState, WorkdayStateRecord
from workflow_dataset.workday.store import (
    load_workday_state,
    save_workday_state,
    current_day_id,
    day_id_from_iso,
    save_day_summary,
)
from workflow_dataset.workday.state_machine import apply_transition, can_transition, gather_context
from workflow_dataset.workday.surface import build_daily_operating_surface, format_daily_operating_surface


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def cmd_day_status(repo_root: Path | str | None = None) -> str:
    """Return formatted daily operating surface."""
    surf = build_daily_operating_surface(repo_root)
    return format_daily_operating_surface(surf)


def cmd_day_start(repo_root: Path | str | None = None) -> tuple[bool, str]:
    """Transition to startup (start the day). Returns (success, message)."""
    root = _root(repo_root)
    record = load_workday_state(root)
    if record.state not in (WorkdayState.NOT_STARTED.value, WorkdayState.RESUME_PENDING.value):
        return False, f"Already in state {record.state}. Use day mode --set to change, or day wrap-up / day shutdown."
    new_record = apply_transition(
        record,
        WorkdayState.STARTUP.value,
        trigger="cli_start",
        at_iso=utc_now_iso(),
        context=gather_context(root),
    )
    if not new_record:
        return False, "Transition to startup blocked."
    new_record.day_started_at_iso = utc_now_iso()
    new_record.day_id = current_day_id()
    save_workday_state(new_record, root)
    return True, f"Day started. State: {new_record.state}. Run: workflow-dataset day mode --set focus_work"


def cmd_day_mode(set_value: str, repo_root: Path | str | None = None) -> tuple[bool, str]:
    """Transition to given mode (focus_work, review_and_approvals, operator_mode, wrap_up, shutdown). Returns (success, message)."""
    root = _root(repo_root)
    record = load_workday_state(root)
    to_state = set_value.strip().lower()
    ok, blocked = can_transition(record.state, to_state, gather_context(root))
    if not ok:
        reasons = "; ".join(b.reason for b in blocked)
        return False, f"Cannot transition to {to_state}: {reasons}"
    new_record = apply_transition(
        record,
        to_state,
        trigger="cli_mode_set",
        at_iso=utc_now_iso(),
        context=gather_context(root),
    )
    if not new_record:
        return False, "Transition failed."
    save_workday_state(new_record, root)
    return True, f"State set to {to_state}."


def cmd_day_wrap_up(repo_root: Path | str | None = None) -> tuple[bool, str]:
    """Transition to wrap_up."""
    return cmd_day_mode(WorkdayState.WRAP_UP.value, repo_root)


def cmd_day_shutdown(repo_root: Path | str | None = None) -> tuple[bool, str]:
    """Transition to shutdown (end day). Optionally save day summary."""
    root = _root(repo_root)
    record = load_workday_state(root)
    if record.state == WorkdayState.SHUTDOWN.value:
        return True, "Already shut down."
    ok, blocked = can_transition(record.state, WorkdayState.SHUTDOWN.value, gather_context(root))
    if not ok:
        reasons = "; ".join(b.reason for b in blocked)
        return False, f"Cannot shutdown: {reasons}"
    new_record = apply_transition(
        record,
        WorkdayState.SHUTDOWN.value,
        trigger="cli_shutdown",
        at_iso=utc_now_iso(),
        context=gather_context(root),
    )
    if not new_record:
        return False, "Transition failed."
    save_workday_state(new_record, root)
    # Optional: write day summary snapshot
    from workflow_dataset.workday.models import DaySummarySnapshot
    states_visited = list({t.to_state for t in new_record.transition_history})
    snapshot = DaySummarySnapshot(
        day_id=new_record.day_id or current_day_id(),
        started_at_iso=new_record.day_started_at_iso,
        ended_at_iso=utc_now_iso(),
        states_visited=states_visited,
        final_state=new_record.state,
    )
    save_day_summary(snapshot, root)
    return True, "Day shut down. Summary saved. Next session: workflow-dataset day resume then day start"


def cmd_day_resume(repo_root: Path | str | None = None) -> tuple[bool, str]:
    """Set state to resume_pending so user can run day start to continue. Or: transition not_started -> startup if last was shutdown."""
    root = _root(repo_root)
    record = load_workday_state(root)
    if record.state == WorkdayState.SHUTDOWN.value:
        # Move to resume_pending so next "day start" starts fresh
        new_record = WorkdayStateRecord(
            state=WorkdayState.RESUME_PENDING.value,
            entered_at_iso=utc_now_iso(),
            previous_state=record.state,
            day_started_at_iso="",
            transition_history=record.transition_history,
            day_id=current_day_id(),
        )
        save_workday_state(new_record, root)
        return True, "Resume pending. Run: workflow-dataset day start to start the day."
    if record.state == WorkdayState.RESUME_PENDING.value:
        return True, "Already in resume_pending. Run: workflow-dataset day start"
    return False, f"Current state is {record.state}. Use day start to start the day, or day status to see surface."
