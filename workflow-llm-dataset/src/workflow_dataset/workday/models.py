"""
M36A–M36D: Workday state machine models — workday state, transitions, active daily context, day summary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkdayState(str, Enum):
    """Explicit workday states."""
    NOT_STARTED = "not_started"
    STARTUP = "startup"
    FOCUS_WORK = "focus_work"
    REVIEW_AND_APPROVALS = "review_and_approvals"
    OPERATOR_MODE = "operator_mode"
    WRAP_UP = "wrap_up"
    SHUTDOWN = "shutdown"
    RESUME_PENDING = "resume_pending"


@dataclass
class StateTransition:
    """One state transition: from, to, timestamp, trigger."""
    from_state: str = ""
    to_state: str = ""
    at_iso: str = ""
    trigger: str = ""  # e.g. cli_start, cli_mode_set, cli_wrap_up, cli_shutdown, cli_resume

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "at_iso": self.at_iso,
            "trigger": self.trigger,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StateTransition":
        return cls(
            from_state=str(d.get("from_state", "")),
            to_state=str(d.get("to_state", "")),
            at_iso=str(d.get("at_iso", "")),
            trigger=str(d.get("trigger", "")),
        )


@dataclass
class WorkdayStateRecord:
    """Current workday state record: state, when entered, previous, day start, history."""
    state: str = WorkdayState.NOT_STARTED.value
    entered_at_iso: str = ""
    previous_state: str = ""
    day_started_at_iso: str = ""  # when start_day was last run (this "day" session)
    transition_history: list[StateTransition] = field(default_factory=list)
    day_id: str = ""  # e.g. YYYY-MM-DD for current day

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "entered_at_iso": self.entered_at_iso,
            "previous_state": self.previous_state,
            "day_started_at_iso": self.day_started_at_iso,
            "transition_history": [t.to_dict() for t in self.transition_history],
            "day_id": self.day_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorkdayStateRecord":
        hist = d.get("transition_history") or []
        return cls(
            state=str(d.get("state", WorkdayState.NOT_STARTED.value)),
            entered_at_iso=str(d.get("entered_at_iso", "")),
            previous_state=str(d.get("previous_state", "")),
            day_started_at_iso=str(d.get("day_started_at_iso", "")),
            transition_history=[StateTransition.from_dict(x) for x in hist],
            day_id=str(d.get("day_id", "")),
        )


@dataclass
class ActiveDailyContext:
    """Active daily context: project, focus, queue, approvals — can mirror workspace + workday-specific."""
    active_project_id: str = ""
    active_project_title: str = ""
    active_focus: str = ""       # e.g. goal text or workflow id
    top_queue_item_ref: str = "" # e.g. approval id or job id
    pending_approvals_count: int = 0
    automation_background_summary: str = ""
    trust_posture: str = ""      # e.g. active preset or tier
    updated_at_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_project_id": self.active_project_id,
            "active_project_title": self.active_project_title,
            "active_focus": self.active_focus,
            "top_queue_item_ref": self.top_queue_item_ref,
            "pending_approvals_count": self.pending_approvals_count,
            "automation_background_summary": self.automation_background_summary,
            "trust_posture": self.trust_posture,
            "updated_at_iso": self.updated_at_iso,
        }


@dataclass
class DaySummarySnapshot:
    """Day summary: what was done this day (states visited, counts, top actions)."""
    day_id: str = ""
    started_at_iso: str = ""
    ended_at_iso: str = ""
    states_visited: list[str] = field(default_factory=list)
    approvals_processed_count: int = 0
    top_actions: list[str] = field(default_factory=list)
    final_state: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "day_id": self.day_id,
            "started_at_iso": self.started_at_iso,
            "ended_at_iso": self.ended_at_iso,
            "states_visited": list(self.states_visited),
            "approvals_processed_count": self.approvals_processed_count,
            "top_actions": list(self.top_actions),
            "final_state": self.final_state,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DaySummarySnapshot":
        return cls(
            day_id=str(d.get("day_id", "")),
            started_at_iso=str(d.get("started_at_iso", "")),
            ended_at_iso=str(d.get("ended_at_iso", "")),
            states_visited=list(d.get("states_visited") or []),
            approvals_processed_count=int(d.get("approvals_processed_count", 0)),
            top_actions=list(d.get("top_actions") or []),
            final_state=str(d.get("final_state", "")),
        )


@dataclass
class BlockedStateInfo:
    """Why a transition is blocked."""
    from_state: str = ""
    to_state: str = ""
    reason: str = ""
