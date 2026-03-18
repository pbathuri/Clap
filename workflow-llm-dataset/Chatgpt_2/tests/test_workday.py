"""
M36A–M36D: Tests for workday state machine, daily operating surface, transitions, resume/shutdown.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.workday.models import (
    WorkdayState,
    WorkdayStateRecord,
    StateTransition,
    DaySummarySnapshot,
)
from workflow_dataset.workday.store import (
    load_workday_state,
    save_workday_state,
    current_day_id,
    day_id_from_iso,
    load_day_summary,
    save_day_summary,
)
from workflow_dataset.workday.state_machine import (
    VALID_TRANSITIONS,
    can_transition,
    apply_transition,
    gather_context,
)
from workflow_dataset.workday.surface import (
    build_daily_operating_surface,
    DailyOperatingSurface,
)
from workflow_dataset.workday.cli import (
    cmd_day_start,
    cmd_day_mode,
    cmd_day_shutdown,
    cmd_day_resume,
)


def test_workday_state_enum() -> None:
    """WorkdayState has expected values."""
    assert WorkdayState.NOT_STARTED.value == "not_started"
    assert WorkdayState.STARTUP.value == "startup"
    assert WorkdayState.FOCUS_WORK.value == "focus_work"
    assert WorkdayState.SHUTDOWN.value == "shutdown"
    assert WorkdayState.RESUME_PENDING.value == "resume_pending"


def test_valid_transitions_not_started_to_startup() -> None:
    """not_started can only go to startup."""
    ok, blocked = can_transition(WorkdayState.NOT_STARTED.value, WorkdayState.STARTUP.value)
    assert ok is True
    assert len(blocked) == 0


def test_valid_transitions_startup_to_focus() -> None:
    """startup can go to focus_work."""
    ok, _ = can_transition(WorkdayState.STARTUP.value, WorkdayState.FOCUS_WORK.value)
    assert ok is True


def test_invalid_transition_not_started_to_focus() -> None:
    """not_started cannot go directly to focus_work."""
    ok, blocked = can_transition(WorkdayState.NOT_STARTED.value, WorkdayState.FOCUS_WORK.value)
    assert ok is False
    assert len(blocked) >= 1


def test_apply_transition_startup() -> None:
    """apply_transition not_started -> startup returns new record."""
    record = WorkdayStateRecord(state=WorkdayState.NOT_STARTED.value, entered_at_iso="2025-01-01T00:00:00Z")
    new_record = apply_transition(record, WorkdayState.STARTUP.value, "cli_start", "2025-01-01T08:00:00Z")
    assert new_record is not None
    assert new_record.state == WorkdayState.STARTUP.value
    assert new_record.previous_state == WorkdayState.NOT_STARTED.value
    assert len(new_record.transition_history) == 1
    assert new_record.transition_history[0].to_state == WorkdayState.STARTUP.value


def test_store_roundtrip(tmp_path: Path) -> None:
    """Save and load workday state."""
    record = WorkdayStateRecord(
        state=WorkdayState.FOCUS_WORK.value,
        entered_at_iso="2025-01-01T09:00:00Z",
        day_id="2025-01-01",
    )
    save_workday_state(record, tmp_path)
    loaded = load_workday_state(tmp_path)
    assert loaded.state == record.state
    assert loaded.day_id == record.day_id


def test_build_daily_operating_surface_empty(tmp_path: Path) -> None:
    """Surface with no state has not_started and recommended start."""
    surf = build_daily_operating_surface(tmp_path)
    assert isinstance(surf, DailyOperatingSurface)
    assert surf.current_workday_state in (WorkdayState.NOT_STARTED.value, "", "resume_pending")
    # When not_started, recommended is startup
    if surf.current_workday_state == WorkdayState.NOT_STARTED.value:
        assert surf.next_recommended_transition == WorkdayState.STARTUP.value


def test_cmd_day_start(tmp_path: Path) -> None:
    """day start transitions to startup and persists."""
    ok, msg = cmd_day_start(tmp_path)
    assert ok is True
    record = load_workday_state(tmp_path)
    assert record.state == WorkdayState.STARTUP.value
    assert record.day_started_at_iso
    assert record.day_id == current_day_id()


def test_cmd_day_start_idempotent_after_start(tmp_path: Path) -> None:
    """day start when already in startup returns False (already started)."""
    cmd_day_start(tmp_path)
    ok, msg = cmd_day_start(tmp_path)
    assert ok is False
    assert "Already" in msg or "startup" in msg.lower()


def test_cmd_day_mode_focus(tmp_path: Path) -> None:
    """After start, mode --set focus_work succeeds."""
    cmd_day_start(tmp_path)
    ok, msg = cmd_day_mode(WorkdayState.FOCUS_WORK.value, tmp_path)
    assert ok is True
    assert load_workday_state(tmp_path).state == WorkdayState.FOCUS_WORK.value


def test_cmd_day_shutdown_saves_summary(tmp_path: Path) -> None:
    """day shutdown transitions to shutdown and saves day summary."""
    cmd_day_start(tmp_path)
    cmd_day_mode(WorkdayState.WRAP_UP.value, tmp_path)
    ok, msg = cmd_day_shutdown(tmp_path)
    assert ok is True
    record = load_workday_state(tmp_path)
    assert record.state == WorkdayState.SHUTDOWN.value
    day_id = current_day_id()
    summary = load_day_summary(day_id, tmp_path)
    assert summary is not None
    assert summary.final_state == WorkdayState.SHUTDOWN.value


def test_cmd_day_resume_after_shutdown(tmp_path: Path) -> None:
    """day resume after shutdown sets resume_pending."""
    cmd_day_start(tmp_path)
    cmd_day_mode(WorkdayState.SHUTDOWN.value, tmp_path)
    ok, msg = cmd_day_resume(tmp_path)
    assert ok is True
    record = load_workday_state(tmp_path)
    assert record.state == WorkdayState.RESUME_PENDING.value


def test_day_id_from_iso() -> None:
    """day_id_from_iso extracts YYYY-MM-DD."""
    assert day_id_from_iso("2025-03-16T12:00:00Z") == "2025-03-16"
    assert day_id_from_iso("") == ""


def test_empty_state_load(tmp_path: Path) -> None:
    """Load when no file returns default not_started record."""
    record = load_workday_state(tmp_path)
    assert record.state == WorkdayState.NOT_STARTED.value or record.state == ""
    assert record.entered_at_iso == ""
