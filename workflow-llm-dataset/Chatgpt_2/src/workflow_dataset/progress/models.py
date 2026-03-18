"""
M27I–M27L: Replan and progress signal models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

REPLAN_SIGNAL_TYPES = (
    "new_blocker_detected",
    "capability_changed",
    "milestone_slipped",
    "repeated_failed_action",
    "new_skill_accepted",
    "artifact_updated",
    "context_drift_affecting_goal",
)


@dataclass
class ReplanSignal:
    """Single reason to consider replanning."""
    signal_type: str
    project_id: str = ""
    reason: str = ""
    ref: str = ""
    evidence: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "project_id": self.project_id,
            "reason": self.reason,
            "ref": self.ref,
            "evidence": list(self.evidence),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ReplanSignal:
        return cls(
            signal_type=str(d.get("signal_type", "")),
            project_id=str(d.get("project_id", "")),
            reason=str(d.get("reason", "")),
            ref=str(d.get("ref", "")),
            evidence=list(d.get("evidence") or []),
            created_at=str(d.get("created_at", "")),
        )


@dataclass
class ProgressSignal:
    """Single progress/impact signal (goal completed, actions executed, stalled, etc.)."""
    kind: str  # goal_completed, actions_executed, blocker_unresolved, artifact_produced, repeated_success, stalled, session_advance
    project_id: str = ""
    ref: str = ""
    detail: str = ""
    positive: bool = True
    created_at: str = ""
