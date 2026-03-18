"""
M44D.1: Vertical memory views — project, session, learning, coding, continuity, operator.
"""

from __future__ import annotations

from workflow_dataset.memory_os.models import VerticalMemoryView
from workflow_dataset.memory_os.profiles import (
    PROFILE_CONSERVATIVE,
    PROFILE_CONTINUITY_HEAVY,
    PROFILE_OPERATOR_HEAVY,
    PROFILE_CODING_HEAVY,
)
from workflow_dataset.memory_os.surfaces import (
    SURFACE_PROJECT,
    SURFACE_SESSION,
    SURFACE_EPISODE,
    SURFACE_CONTINUITY,
    SURFACE_OPERATOR,
    SURFACE_LEARNING,
    SURFACE_CURSOR,
)

VERTICAL_PROJECT = "project"
VERTICAL_SESSION = "session"
VERTICAL_LEARNING = "learning"
VERTICAL_CODING = "coding"
VERTICAL_CONTINUITY = "continuity"
VERTICAL_OPERATOR = "operator"

_VIEWS: list[VerticalMemoryView] = [
    VerticalMemoryView(
        view_id="view_project",
        vertical_id=VERTICAL_PROJECT,
        label="Project memory view",
        description="Memory for project-scoped workflows: project and episode surfaces.",
        surface_ids=[SURFACE_PROJECT, SURFACE_EPISODE, SURFACE_SESSION],
        preferred_profile_id=PROFILE_CONSERVATIVE,
        why_this_profile="Project vertical uses conservative profile by default to keep context high-signal and trusted.",
    ),
    VerticalMemoryView(
        view_id="view_session",
        vertical_id=VERTICAL_SESSION,
        label="Session memory view",
        description="Memory for current session and short-term context.",
        surface_ids=[SURFACE_SESSION, SURFACE_PROJECT],
        preferred_profile_id=PROFILE_CONTINUITY_HEAVY,
        why_this_profile="Session vertical benefits from continuity-heavy profile to surface resume context and blockers.",
    ),
    VerticalMemoryView(
        view_id="view_learning",
        vertical_id=VERTICAL_LEARNING,
        label="Learning / eval memory view",
        description="Memory for learning lab and evaluation workflows.",
        surface_ids=[SURFACE_LEARNING, SURFACE_OPERATOR],
        preferred_profile_id=PROFILE_OPERATOR_HEAVY,
        why_this_profile="Learning vertical uses operator-heavy profile to recall decision rationale and review history.",
    ),
    VerticalMemoryView(
        view_id="view_coding",
        vertical_id=VERTICAL_CODING,
        label="Coding / Cursor memory view",
        description="Memory for Cursor and coding workflows.",
        surface_ids=[SURFACE_CURSOR, SURFACE_LEARNING, SURFACE_SESSION],
        preferred_profile_id=PROFILE_CODING_HEAVY,
        why_this_profile="Coding vertical uses coding-heavy profile to prioritize patterns and Cursor context.",
    ),
    VerticalMemoryView(
        view_id="view_continuity",
        vertical_id=VERTICAL_CONTINUITY,
        label="Continuity / resume view",
        description="Memory for resume and cross-session continuity.",
        surface_ids=[SURFACE_CONTINUITY, SURFACE_SESSION, SURFACE_PROJECT],
        preferred_profile_id=PROFILE_CONTINUITY_HEAVY,
        why_this_profile="Continuity vertical explicitly uses continuity-heavy profile for blockers and context.",
    ),
    VerticalMemoryView(
        view_id="view_operator",
        vertical_id=VERTICAL_OPERATOR,
        label="Operator / history view",
        description="Memory for operator decisions and approval history.",
        surface_ids=[SURFACE_OPERATOR, SURFACE_PROJECT, SURFACE_SESSION],
        preferred_profile_id=PROFILE_OPERATOR_HEAVY,
        why_this_profile="Operator vertical uses operator-heavy profile to surface decisions and review history.",
    ),
]


def list_views() -> list[VerticalMemoryView]:
    """Return all vertical memory views."""
    return list(_VIEWS)


def get_view(view_id: str) -> VerticalMemoryView | None:
    """Return view by view_id."""
    for v in _VIEWS:
        if v.view_id == view_id:
            return v
    return None


def get_view_for_vertical(vertical_id: str) -> VerticalMemoryView | None:
    """Return the memory view for a product vertical (e.g. project, session, coding)."""
    for v in _VIEWS:
        if v.vertical_id == vertical_id:
            return v
    return None
