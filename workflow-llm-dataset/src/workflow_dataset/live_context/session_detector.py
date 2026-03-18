"""
Live session transition detection (M32C).

First-draft detection: session start, project switch, deep-work continuation,
interruption/context break, return-to-work. Bounded and explainable.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.live_context.models import (
    ActiveWorkContext,
    SessionTransitionEvent,
    SessionTransitionKind,
    WorkMode,
)
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def detect_transitions(
    current: ActiveWorkContext,
    previous: ActiveWorkContext | None,
    now_utc: str | None = None,
) -> list[SessionTransitionEvent]:
    """
    Compare current fused context to previous and emit transition events.
    Returns list of SessionTransitionEvent (may be empty).
    """
    now = now_utc or utc_now_iso()
    out: list[SessionTransitionEvent] = []

    if previous is None:
        if current.inferred_project or current.focus_target:
            out.append(
                SessionTransitionEvent(
                    transition_id=stable_id("tr", now, "start", prefix="tr"),
                    kind=SessionTransitionKind.SESSION_START,
                    timestamp_utc=now,
                    to_project=current.inferred_project.label if current.inferred_project else "",
                    evidence=current.evidence_summary[:3],
                    confidence=current.overall_confidence,
                )
            )
        return out

    prev_project = previous.inferred_project.label if previous.inferred_project else ""
    curr_project = current.inferred_project.label if current.inferred_project else ""

    # Project switch
    if prev_project and curr_project and prev_project != curr_project:
        out.append(
            SessionTransitionEvent(
                transition_id=stable_id("tr", now, "switch", prev_project, curr_project, prefix="tr"),
                kind=SessionTransitionKind.PROJECT_SWITCH,
                timestamp_utc=now,
                from_project=prev_project,
                to_project=curr_project,
                evidence=[f"from_file_events={prev_project}", f"to_file_events={curr_project}"],
                confidence=min(0.9, current.overall_confidence + 0.1),
            )
        )

    # Deep work continuation: same project, focused mode
    if curr_project and current.work_mode == WorkMode.FOCUSED and prev_project == curr_project:
        out.append(
            SessionTransitionEvent(
                transition_id=stable_id("tr", now, "deep", curr_project, prefix="tr"),
                kind=SessionTransitionKind.DEEP_WORK_CONTINUATION,
                timestamp_utc=now,
                from_project=curr_project,
                to_project=curr_project,
                evidence=["same_project", "work_mode=focused"],
                confidence=current.overall_confidence,
            )
        )

    # Interruption: was focused, now switching or idle
    if previous.work_mode == WorkMode.FOCUSED and current.work_mode in (WorkMode.SWITCHING, WorkMode.IDLE):
        out.append(
            SessionTransitionEvent(
                transition_id=stable_id("tr", now, "interrupt", prefix="tr"),
                kind=SessionTransitionKind.INTERRUPTION,
                timestamp_utc=now,
                from_project=prev_project,
                to_project=curr_project,
                evidence=[f"previous_mode={previous.work_mode.value}", f"current_mode={current.work_mode.value}"],
                confidence=0.6,
            )
        )

    # Return to work: was idle/unknown, now focused or switching with project
    if previous.work_mode in (WorkMode.IDLE, WorkMode.UNKNOWN) and curr_project and current.work_mode in (WorkMode.FOCUSED, WorkMode.SWITCHING):
        out.append(
            SessionTransitionEvent(
                transition_id=stable_id("tr", now, "return", curr_project, prefix="tr"),
                kind=SessionTransitionKind.RETURN_TO_WORK,
                timestamp_utc=now,
                to_project=curr_project,
                evidence=["prior_idle_or_unknown", f"current_project={curr_project}"],
                confidence=current.overall_confidence,
            )
        )

    return out
