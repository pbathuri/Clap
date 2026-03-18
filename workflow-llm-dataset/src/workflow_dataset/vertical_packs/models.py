"""
M39E–M39H: Curated vertical pack model — opinionated workflow packs and guided value paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequiredSurfaces:
    """Required vs optional surfaces for this vertical."""
    required_surface_ids: list[str] = field(default_factory=list)
    optional_surface_ids: list[str] = field(default_factory=list)
    hidden_for_vertical: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_surface_ids": list(self.required_surface_ids),
            "optional_surface_ids": list(self.optional_surface_ids),
            "hidden_for_vertical": list(self.hidden_for_vertical),
        }


@dataclass
class SuccessMilestone:
    """A measurable success milestone on a value path."""
    milestone_id: str = ""
    label: str = ""
    description: str = ""
    step_index: int = 0  # 1-based; 0 = path-level
    command_hint: str = ""
    reached_when: str = ""  # Short condition, e.g. "first_run_completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "label": self.label,
            "description": self.description,
            "step_index": self.step_index,
            "command_hint": self.command_hint,
            "reached_when": self.reached_when,
        }


@dataclass
class TrustReviewPosture:
    """Trust and review posture recommended for this vertical."""
    trust_preset_id: str = ""
    review_gates_default: list[str] = field(default_factory=list)
    audit_posture: str = ""  # e.g. "before_real", "before_send"
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trust_preset_id": self.trust_preset_id,
            "review_gates_default": list(self.review_gates_default),
            "audit_posture": self.audit_posture,
            "description": self.description,
        }


@dataclass
class RecommendedWorkdayProfile:
    """Recommended workday preset and day-flow for this vertical."""
    workday_preset_id: str = ""
    default_day_states: list[str] = field(default_factory=list)
    default_transition_after_startup: str = ""
    queue_review_emphasis: str = ""
    operator_mode_usage: str = ""
    role_operating_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "workday_preset_id": self.workday_preset_id,
            "default_day_states": list(self.default_day_states),
            "default_transition_after_startup": self.default_transition_after_startup,
            "queue_review_emphasis": self.queue_review_emphasis,
            "operator_mode_usage": self.operator_mode_usage,
            "role_operating_hint": self.role_operating_hint,
        }


@dataclass
class RecommendedQueueProfile:
    """Recommended queue and calmness settings for this vertical."""
    queue_section_order: list[str] = field(default_factory=list)
    calmness_default: str = ""  # e.g. "calm", "focused"
    max_visible_sections: int = 0  # 0 = no limit
    emphasis: str = ""  # high | medium | low

    def to_dict(self) -> dict[str, Any]:
        return {
            "queue_section_order": list(self.queue_section_order),
            "calmness_default": self.calmness_default,
            "max_visible_sections": self.max_visible_sections,
            "emphasis": self.emphasis,
        }


@dataclass
class CoreWorkflowPath:
    """Core workflow path: main workflows and ordering for this vertical."""
    path_id: str = ""
    label: str = ""
    workflow_ids: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "label": self.label,
            "workflow_ids": list(self.workflow_ids),
            "description": self.description,
        }


@dataclass
class FirstValuePathStep:
    """One step on the first-value path."""
    step_number: int
    title: str
    command: str
    what_user_sees: str = ""
    what_to_do_next: str = ""
    run_read_only: bool = False
    milestone_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "title": self.title,
            "command": self.command,
            "what_user_sees": self.what_user_sees,
            "what_to_do_next": self.what_to_do_next,
            "run_read_only": self.run_read_only,
            "milestone_id": self.milestone_id,
        }


@dataclass
class CommonFailurePoint:
    """Common failure point on a path with short remediation hint."""
    step_index: int
    symptom: str = ""
    remediation_hint: str = ""
    escalation_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "symptom": self.symptom,
            "remediation_hint": self.remediation_hint,
            "escalation_command": self.escalation_command,
        }


@dataclass
class FirstValuePath:
    """Guided first-value path: entry, steps, milestones, failure points."""
    path_id: str = ""
    pack_id: str = ""
    label: str = ""
    entry_point: str = ""  # command or surface, e.g. "workflow-dataset package first-run"
    required_surface_ids: list[str] = field(default_factory=list)
    steps: list[FirstValuePathStep] = field(default_factory=list)
    milestones: list[SuccessMilestone] = field(default_factory=list)
    suggested_next_actions: list[str] = field(default_factory=list)
    first_value_milestone_id: str = ""
    common_failure_points: list[CommonFailurePoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "pack_id": self.pack_id,
            "label": self.label,
            "entry_point": self.entry_point,
            "required_surface_ids": list(self.required_surface_ids),
            "steps": [s.to_dict() for s in self.steps],
            "milestones": [m.to_dict() for m in self.milestones],
            "suggested_next_actions": list(self.suggested_next_actions),
            "first_value_milestone_id": self.first_value_milestone_id,
            "common_failure_points": [f.to_dict() for f in self.common_failure_points],
        }


# ----- M39H.1 Vertical playbooks + recovery paths -----


@dataclass
class RecoveryPathStep:
    """One step in a recovery path to get back to first-value."""
    step_order: int
    command: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"step_order": self.step_order, "command": self.command, "label": self.label}


@dataclass
class RecoveryPath:
    """Recovery path: ordered steps to resume first-value after a failure."""
    recovery_path_id: str = ""
    label: str = ""
    steps: list[RecoveryPathStep] = field(default_factory=list)
    target_milestone_id: str = ""  # milestone to reach to be "back on path"

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_path_id": self.recovery_path_id,
            "label": self.label,
            "steps": [s.to_dict() for s in self.steps],
            "target_milestone_id": self.target_milestone_id,
        }


@dataclass
class VerticalPlaybookFailureEntry:
    """Failure point entry in a vertical playbook (step + symptom + remediation + optional recovery_path_id)."""
    step_index: int
    symptom: str = ""
    remediation_hint: str = ""
    escalation_command: str = ""
    recovery_path_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "symptom": self.symptom,
            "remediation_hint": self.remediation_hint,
            "escalation_command": self.escalation_command,
            "recovery_path_id": self.recovery_path_id,
        }


@dataclass
class VerticalPlaybook:
    """Vertical playbook: common failure points by vertical + recovery paths + operator guidance when path stalls."""
    playbook_id: str = ""
    curated_pack_id: str = ""
    label: str = ""
    description: str = ""
    failure_entries: list[VerticalPlaybookFailureEntry] = field(default_factory=list)
    recovery_paths: list[RecoveryPath] = field(default_factory=list)
    operator_guidance_stalled: str = ""
    operator_commands_stalled: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "curated_pack_id": self.curated_pack_id,
            "label": self.label,
            "description": self.description,
            "failure_entries": [e.to_dict() for e in self.failure_entries],
            "recovery_paths": [r.to_dict() for r in self.recovery_paths],
            "operator_guidance_stalled": self.operator_guidance_stalled,
            "operator_commands_stalled": list(self.operator_commands_stalled),
        }


@dataclass
class CuratedVerticalPack:
    """Curated vertical pack: value pack + workday + experience + trust + paths + surfaces."""
    pack_id: str = ""
    name: str = ""
    description: str = ""
    value_pack_id: str = ""
    workday_preset_id: str = ""
    default_experience_profile_id: str = ""
    trust_review_posture: TrustReviewPosture = field(default_factory=TrustReviewPosture)
    recommended_workday: RecommendedWorkdayProfile = field(default_factory=RecommendedWorkdayProfile)
    recommended_queue: RecommendedQueueProfile = field(default_factory=RecommendedQueueProfile)
    core_workflow_path: CoreWorkflowPath | None = None
    first_value_path: FirstValuePath | None = None
    required_surfaces: RequiredSurfaces = field(default_factory=RequiredSurfaces)
    recommended_operator_bundle_id: str = ""
    recommended_automation_settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "name": self.name,
            "description": self.description,
            "value_pack_id": self.value_pack_id,
            "workday_preset_id": self.workday_preset_id,
            "default_experience_profile_id": self.default_experience_profile_id,
            "trust_review_posture": self.trust_review_posture.to_dict(),
            "recommended_workday": self.recommended_workday.to_dict(),
            "recommended_queue": self.recommended_queue.to_dict(),
            "core_workflow_path": self.core_workflow_path.to_dict() if self.core_workflow_path else None,
            "first_value_path": self.first_value_path.to_dict() if self.first_value_path else None,
            "required_surfaces": self.required_surfaces.to_dict(),
            "recommended_operator_bundle_id": self.recommended_operator_bundle_id,
            "recommended_automation_settings": dict(self.recommended_automation_settings),
        }
