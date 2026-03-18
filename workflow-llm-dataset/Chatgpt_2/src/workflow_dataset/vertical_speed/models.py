"""
M47E–M47H: High-frequency workflow speed and friction-reduction models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowKind(str, Enum):
    """Kind of frequent workflow."""
    morning_entry_first_action = "morning_entry_first_action"
    queue_item_to_action = "queue_item_to_action"
    review_item_to_decision = "review_item_to_decision"
    continuity_resume_to_context = "continuity_resume_to_context"
    operator_routine_to_execution = "operator_routine_to_execution"
    vertical_draft_to_completion = "vertical_draft_to_completion"


class FrictionKind(str, Enum):
    """Kind of friction cluster."""
    handoff_overhead = "handoff_overhead"
    repeated_navigation = "repeated_navigation"
    review_detour = "review_detour"
    slow_transition = "slow_transition"
    unnecessary_branch = "unnecessary_branch"
    blocked_recovery = "blocked_recovery"


@dataclass
class FrequentWorkflow:
    """A high-frequency workflow in the chosen vertical."""
    workflow_id: str
    kind: WorkflowKind
    label: str
    description: str = ""
    vertical_pack_id: str = ""
    estimated_frequency: str = ""  # e.g. "daily", "multiple_per_day"
    entry_point: str = ""  # e.g. "queue view", "continuity morning"
    typical_steps: list[str] = field(default_factory=list)
    current_step_count: int = 0  # observed or default
    suggested_step_count: int = 0  # after speed-up

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "kind": self.kind.value,
            "label": self.label,
            "description": self.description,
            "vertical_pack_id": self.vertical_pack_id,
            "estimated_frequency": self.estimated_frequency,
            "entry_point": self.entry_point,
            "typical_steps": self.typical_steps,
            "current_step_count": self.current_step_count,
            "suggested_step_count": self.suggested_step_count,
        }


@dataclass
class RepeatedHandoff:
    """A repeated handoff point (queue → card → target)."""
    handoff_id: str
    from_surface: str
    to_surface: str
    description: str = ""
    occurrence_count_estimate: int = 0
    suggested_single_step: str = ""  # e.g. single command that skips handoff

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "from_surface": self.from_surface,
            "to_surface": self.to_surface,
            "description": self.description,
            "occurrence_count_estimate": self.occurrence_count_estimate,
            "suggested_single_step": self.suggested_single_step,
        }


@dataclass
class SlowTransition:
    """A slow or high-effort transition (e.g. startup → review_and_approvals)."""
    transition_id: str
    from_mode: str
    to_mode: str
    description: str = ""
    typical_actions: list[str] = field(default_factory=list)
    shortcut_available: bool = False
    shortcut_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "from_mode": self.from_mode,
            "to_mode": self.to_mode,
            "description": self.description,
            "typical_actions": self.typical_actions,
            "shortcut_available": self.shortcut_available,
            "shortcut_command": self.shortcut_command,
        }


@dataclass
class UnnecessaryBranch:
    """An unnecessary branch or detour (e.g. open queue then open inbox for same content)."""
    branch_id: str
    trigger: str
    branch_description: str = ""
    suggested_merge: str = ""  # single path that avoids branch

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "trigger": self.trigger,
            "branch_description": self.branch_description,
            "suggested_merge": self.suggested_merge,
        }


@dataclass
class FrictionCluster:
    """A cluster of related friction (e.g. queue→action path)."""
    cluster_id: str
    kind: FrictionKind
    label: str
    description: str = ""
    repeated_handoffs: list[RepeatedHandoff] = field(default_factory=list)
    slow_transitions: list[SlowTransition] = field(default_factory=list)
    unnecessary_branches: list[UnnecessaryBranch] = field(default_factory=list)
    impact_summary: str = ""
    suggested_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "kind": self.kind.value,
            "label": self.label,
            "description": self.description,
            "repeated_handoffs": [h.to_dict() for h in self.repeated_handoffs],
            "slow_transitions": [t.to_dict() for t in self.slow_transitions],
            "unnecessary_branches": [b.to_dict() for b in self.unnecessary_branches],
            "impact_summary": self.impact_summary,
            "suggested_action": self.suggested_action,
        }


@dataclass
class RepeatValueBottleneck:
    """A bottleneck that reduces repeat value (e.g. no prefilled default, blocked with no hint)."""
    bottleneck_id: str
    workflow_id: str
    label: str
    description: str = ""
    recovery_hint: str = ""
    prefilled_default_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "bottleneck_id": self.bottleneck_id,
            "workflow_id": self.workflow_id,
            "label": self.label,
            "description": self.description,
            "recovery_hint": self.recovery_hint,
            "prefilled_default_available": self.prefilled_default_available,
        }


@dataclass
class SpeedUpCandidate:
    """A concrete speed-up recommendation."""
    candidate_id: str
    label: str
    description: str = ""
    workflow_id: str = ""
    friction_cluster_id: str = ""
    route_to_action: str = ""  # single command or view
    expected_step_reduction: int = 0
    priority: str = "medium"  # high | medium | low

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "label": self.label,
            "description": self.description,
            "workflow_id": self.workflow_id,
            "friction_cluster_id": self.friction_cluster_id,
            "route_to_action": self.route_to_action,
            "expected_step_reduction": self.expected_step_reduction,
            "priority": self.priority,
        }


# ----- M47H.1 Fast paths + common-loop bundles -----


@dataclass
class FastPath:
    """A compressed path for a high-frequency workflow (one or few steps instead of many)."""
    path_id: str
    workflow_id: str
    label: str
    description: str = ""
    compressed_steps: list[str] = field(default_factory=list)  # one or short sequence of commands
    single_command: str = ""  # convenience: first/only command when compressed_steps has one
    step_count_before: int = 0
    step_count_after: int = 0
    precondition: str = ""  # optional: e.g. "queue has items", "continuity morning available"

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "workflow_id": self.workflow_id,
            "label": self.label,
            "description": self.description,
            "compressed_steps": self.compressed_steps,
            "single_command": self.single_command,
            "step_count_before": self.step_count_before,
            "step_count_after": self.step_count_after,
            "precondition": self.precondition,
        }


@dataclass
class CommonLoopBundle:
    """A bundle of repeated flows that form a common loop (e.g. morning loop, queue-review loop)."""
    bundle_id: str
    label: str
    description: str = ""
    workflow_ids: list[str] = field(default_factory=list)
    step_ids: list[str] = field(default_factory=list)  # optional step identifiers
    single_entry_command: str = ""  # optional: one command to enter the loop
    fast_path_ids: list[str] = field(default_factory=list)  # optional link to fast paths

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "label": self.label,
            "description": self.description,
            "workflow_ids": self.workflow_ids,
            "step_ids": self.step_ids,
            "single_entry_command": self.single_entry_command,
            "fast_path_ids": self.fast_path_ids,
        }
