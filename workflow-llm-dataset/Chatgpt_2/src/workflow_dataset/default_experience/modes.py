"""
M37B: Mode simplification — user-facing modes vs internal workday states.
"""

from __future__ import annotations

from workflow_dataset.default_experience.models import (
    DEFAULT_USER_MODES,
    DefaultWorkdayModeSet,
    USER_MODE_FOCUS,
    USER_MODE_OPERATOR,
    USER_MODE_REVIEW,
    USER_MODE_RESUME,
    USER_MODE_START,
    USER_MODE_WRAP_UP,
)
from workflow_dataset.workday.models import WorkdayState

# Internal state values (from WorkdayState enum)
_NOT_STARTED = WorkdayState.NOT_STARTED.value
_STARTUP = WorkdayState.STARTUP.value
_FOCUS = WorkdayState.FOCUS_WORK.value
_REVIEW = WorkdayState.REVIEW_AND_APPROVALS.value
_OPERATOR = WorkdayState.OPERATOR_MODE.value
_WRAP_UP = WorkdayState.WRAP_UP.value
_SHUTDOWN = WorkdayState.SHUTDOWN.value
_RESUME_PENDING = WorkdayState.RESUME_PENDING.value

# User-facing mode set (six modes)
SIMPLIFIED_MODE_SET: list[DefaultWorkdayModeSet] = [
    DefaultWorkdayModeSet(
        USER_MODE_START,
        "Start",
        [_NOT_STARTED, _STARTUP],
        "Day not started or in startup.",
    ),
    DefaultWorkdayModeSet(
        USER_MODE_FOCUS,
        "Focus",
        [_FOCUS],
        "Focused work.",
    ),
    DefaultWorkdayModeSet(
        USER_MODE_REVIEW,
        "Review",
        [_REVIEW],
        "Review and approvals.",
    ),
    DefaultWorkdayModeSet(
        USER_MODE_OPERATOR,
        "Operator",
        [_OPERATOR],
        "Operator mode.",
    ),
    DefaultWorkdayModeSet(
        USER_MODE_WRAP_UP,
        "Wrap up",
        [_WRAP_UP],
        "Wrapping up.",
    ),
    DefaultWorkdayModeSet(
        USER_MODE_RESUME,
        "Resume",
        [_SHUTDOWN, _RESUME_PENDING],
        "Shut down or resume pending.",
    ),
]


def internal_state_to_user_mode(internal_state: str) -> str:
    """Map internal workday state to user-facing mode id."""
    for mode in SIMPLIFIED_MODE_SET:
        if internal_state in mode.internal_states:
            return mode.mode_id
    return USER_MODE_START


def get_simplified_mode_mapping() -> list[dict]:
    """For mission control / CLI: list of { mode_id, label, internal_states }."""
    return [m.to_dict() for m in SIMPLIFIED_MODE_SET]
