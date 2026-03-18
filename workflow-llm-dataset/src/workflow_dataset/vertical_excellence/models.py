"""
M47A: Primary vertical path model — first-value path, repeat-value path, friction, ambiguity, excellence target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FirstValuePathStage:
    """Current stage on the first-value path (step index and status)."""
    vertical_id: str = ""
    step_index: int = 0  # 0 = not started, 1..N = current step
    total_steps: int = 0
    status: str = ""  # not_started | in_progress | first_value_reached | completed
    milestone_id: str = ""
    next_command_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertical_id": self.vertical_id,
            "step_index": self.step_index,
            "total_steps": self.total_steps,
            "status": self.status,
            "milestone_id": self.milestone_id,
            "next_command_hint": self.next_command_hint,
        }


@dataclass
class RepeatValuePathStage:
    """Repeat-value path stage (high-frequency workflow and current compression)."""
    workflow_id: str = ""
    label: str = ""
    current_step_count: int = 0
    suggested_step_count: int = 0
    entry_point: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "label": self.label,
            "current_step_count": self.current_step_count,
            "suggested_step_count": self.suggested_step_count,
            "entry_point": self.entry_point,
        }


@dataclass
class CriticalUserJourney:
    """Critical user journey: entry → key steps → first-value outcome."""
    journey_id: str = ""
    label: str = ""
    entry_point: str = ""
    steps: list[str] = field(default_factory=list)
    first_value_outcome: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "journey_id": self.journey_id,
            "label": self.label,
            "entry_point": self.entry_point,
            "steps": list(self.steps),
            "first_value_outcome": self.first_value_outcome,
        }


@dataclass
class FrictionPoint:
    """Friction point on the path (from vertical_speed or common_failure_points)."""
    friction_id: str = ""
    kind: str = ""  # handoff_overhead | repeated_navigation | blocked_recovery | etc.
    step_index: int = 0
    label: str = ""
    remediation_hint: str = ""
    escalation_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "friction_id": self.friction_id,
            "kind": self.kind,
            "step_index": self.step_index,
            "label": self.label,
            "remediation_hint": self.remediation_hint,
            "escalation_command": self.escalation_command,
        }


@dataclass
class AmbiguityPoint:
    """Ambiguity point: user may not know what to do next."""
    ambiguity_id: str = ""
    step_index: int = 0
    label: str = ""
    suggested_next: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ambiguity_id": self.ambiguity_id,
            "step_index": self.step_index,
            "label": self.label,
            "suggested_next": self.suggested_next,
        }


@dataclass
class MissingNextStepSignal:
    """Signal that the next step is missing or unclear."""
    signal_id: str = ""
    step_index: int = 0
    reason: str = ""  # no_active_vertical | no_path | blocked | completed
    recommended_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "step_index": self.step_index,
            "reason": self.reason,
            "recommended_command": self.recommended_command,
        }


@dataclass
class ExcellenceTarget:
    """Excellence target: what to improve next (first-value or repeat-value)."""
    target_id: str = ""
    kind: str = ""  # first_value_compression | repeat_value_compression | friction_reduction
    label: str = ""
    action_hint: str = ""
    priority: str = ""  # high | medium | low

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "kind": self.kind,
            "label": self.label,
            "action_hint": self.action_hint,
            "priority": self.priority,
        }


# ----- M47D.1 Role-tuned entry paths + faster on-ramps -----


@dataclass
class RoleTunedEntryPath:
    """Role-tuned first-value entry path inside the chosen vertical."""
    vertical_id: str = ""
    role_id: str = ""  # operator | reviewer | analyst
    label: str = ""
    entry_point: str = ""
    step_titles: list[str] = field(default_factory=list)
    step_commands: list[str] = field(default_factory=list)
    first_value_outcome: str = ""
    best_next_after_entry: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertical_id": self.vertical_id,
            "role_id": self.role_id,
            "label": self.label,
            "entry_point": self.entry_point,
            "step_titles": list(self.step_titles),
            "step_commands": list(self.step_commands),
            "first_value_outcome": self.first_value_outcome,
            "best_next_after_entry": self.best_next_after_entry,
        }


@dataclass
class OnRampPreset:
    """Faster on-ramp preset: compressed step set for quick first value."""
    preset_id: str = ""  # minimal | standard | full
    label: str = ""
    description: str = ""
    step_count: int = 0
    step_indices: list[int] = field(default_factory=list)  # 1-based indices from base path
    entry_point: str = ""
    suggested_for: str = ""  # new_user | returning_user | both

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "description": self.description,
            "step_count": self.step_count,
            "step_indices": list(self.step_indices),
            "entry_point": self.entry_point,
            "suggested_for": self.suggested_for,
        }
