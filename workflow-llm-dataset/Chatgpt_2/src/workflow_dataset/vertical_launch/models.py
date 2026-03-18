"""
M39I–M39L: Vertical launch kit and success-proof models — launch kit, first-run path,
setup checklist, success proof metric, first-value checkpoint, operator playbook,
supported/unsupported boundaries, recovery/escalation guidance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequiredSetupChecklist:
    """Required setup before launch can start: env, approvals, surfaces."""
    checklist_id: str = ""
    label: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)  # [{id, label, checked, blocking, command_hint}]
    all_passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "checklist_id": self.checklist_id,
            "label": self.label,
            "items": list(self.items),
            "all_passed": self.all_passed,
        }


@dataclass
class FirstRunLaunchPath:
    """First-run launch path: entry command, ordered steps, required surfaces."""
    path_id: str = ""
    label: str = ""
    entry_point: str = ""
    step_titles: list[str] = field(default_factory=list)
    required_surface_ids: list[str] = field(default_factory=list)
    first_value_milestone_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "label": self.label,
            "entry_point": self.entry_point,
            "step_titles": list(self.step_titles),
            "required_surface_ids": list(self.required_surface_ids),
            "first_value_milestone_id": self.first_value_milestone_id,
        }


@dataclass
class SuccessProofMetric:
    """One success proof metric: id, label, condition, status."""
    proof_id: str = ""
    label: str = ""
    description: str = ""
    reached_when: str = ""
    status: str = "pending"  # pending | met | failed
    reached_at_utc: str = ""
    cohort_id: str = ""
    path_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "label": self.label,
            "description": self.description,
            "reached_when": self.reached_when,
            "status": self.status,
            "reached_at_utc": self.reached_at_utc,
            "cohort_id": self.cohort_id,
            "path_id": self.path_id,
        }


@dataclass
class FirstValueCheckpoint:
    """First-value checkpoint: milestone id, label, reached flag."""
    checkpoint_id: str = ""
    label: str = ""
    milestone_id: str = ""
    reached: bool = False
    reached_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "label": self.label,
            "milestone_id": self.milestone_id,
            "reached": self.reached,
            "reached_at_utc": self.reached_at_utc,
        }


@dataclass
class SupportedUnsupportedBoundaries:
    """Supported vs unsupported boundaries for this launch kit."""
    supported_surface_ids: list[str] = field(default_factory=list)
    unsupported_surface_ids: list[str] = field(default_factory=list)
    supported_workflow_ids: list[str] = field(default_factory=list)
    out_of_scope_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "supported_surface_ids": list(self.supported_surface_ids),
            "unsupported_surface_ids": list(self.unsupported_surface_ids),
            "supported_workflow_ids": list(self.supported_workflow_ids),
            "out_of_scope_hint": self.out_of_scope_hint,
        }


@dataclass
class RecoveryEscalationGuidance:
    """Recovery and escalation guidance for this launch kit."""
    recovery_path_id: str = ""
    label: str = ""
    steps_summary: list[str] = field(default_factory=list)
    escalation_command: str = ""
    when_to_narrow_scope: str = ""
    when_to_escalate_cohort: str = ""
    trust_review_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_path_id": self.recovery_path_id,
            "label": self.label,
            "steps_summary": list(self.steps_summary),
            "escalation_command": self.escalation_command,
            "when_to_narrow_scope": self.when_to_narrow_scope,
            "when_to_escalate_cohort": self.when_to_escalate_cohort,
            "trust_review_hint": self.trust_review_hint,
        }


@dataclass
class OperatorSupportPlaybook:
    """Operator support playbook for this launch kit: setup, first-value coaching, recovery, escalation."""
    playbook_id: str = ""
    launch_kit_id: str = ""
    label: str = ""
    setup_guidance: str = ""
    first_value_coaching: str = ""
    common_recovery_guidance: str = ""
    when_to_narrow_scope: str = ""
    when_to_escalate_downgrade_cohort: str = ""
    trust_operator_review_hint: str = ""
    commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "launch_kit_id": self.launch_kit_id,
            "label": self.label,
            "setup_guidance": self.setup_guidance,
            "first_value_coaching": self.first_value_coaching,
            "common_recovery_guidance": self.common_recovery_guidance,
            "when_to_narrow_scope": self.when_to_narrow_scope,
            "when_to_escalate_downgrade_cohort": self.when_to_escalate_downgrade_cohort,
            "trust_operator_review_hint": self.trust_operator_review_hint,
            "commands": list(self.commands),
        }


@dataclass
class VerticalLaunchKit:
    """Vertical launch kit: one launchable unit per vertical."""
    launch_kit_id: str = ""
    vertical_id: str = ""
    curated_pack_id: str = ""
    label: str = ""
    description: str = ""
    first_run_path: FirstRunLaunchPath = field(default_factory=FirstRunLaunchPath)
    required_setup: RequiredSetupChecklist = field(default_factory=RequiredSetupChecklist)
    success_proof_metrics: list[SuccessProofMetric] = field(default_factory=list)
    first_value_checkpoints: list[FirstValueCheckpoint] = field(default_factory=list)
    operator_playbook: OperatorSupportPlaybook = field(default_factory=OperatorSupportPlaybook)
    supported_unsupported: SupportedUnsupportedBoundaries = field(default_factory=SupportedUnsupportedBoundaries)
    recovery_escalation: list[RecoveryEscalationGuidance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "launch_kit_id": self.launch_kit_id,
            "vertical_id": self.vertical_id,
            "curated_pack_id": self.curated_pack_id,
            "label": self.label,
            "description": self.description,
            "first_run_path": self.first_run_path.to_dict(),
            "required_setup": self.required_setup.to_dict(),
            "success_proof_metrics": [m.to_dict() for m in self.success_proof_metrics],
            "first_value_checkpoints": [c.to_dict() for c in self.first_value_checkpoints],
            "operator_playbook": self.operator_playbook.to_dict(),
            "supported_unsupported": self.supported_unsupported.to_dict(),
            "recovery_escalation": [r.to_dict() for r in self.recovery_escalation],
        }


# ----- M39L.1 Value dashboards + rollout review -----

ROLLOUT_CONTINUE = "continue"
ROLLOUT_NARROW = "narrow"
ROLLOUT_PAUSE = "pause"
ROLLOUT_EXPAND = "expand"


@dataclass
class RolloutDecision:
    """Recorded rollout decision for a vertical: continue / narrow / pause / expand."""
    decision_id: str = ""
    vertical_id: str = ""
    launch_kit_id: str = ""
    decision: str = ROLLOUT_CONTINUE  # continue | narrow | pause | expand
    rationale: str = ""
    recorded_at_utc: str = ""
    recorded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "vertical_id": self.vertical_id,
            "launch_kit_id": self.launch_kit_id,
            "decision": self.decision,
            "rationale": self.rationale,
            "recorded_at_utc": self.recorded_at_utc,
            "recorded_by": self.recorded_by,
        }


@dataclass
class RolloutReviewPack:
    """Vertical rollout review pack: evidence summary, what's working/not, recommended decision, operator summary."""
    vertical_id: str = ""
    launch_kit_id: str = ""
    curated_pack_id: str = ""
    label: str = ""
    evidence_summary: str = ""
    what_is_working: list[str] = field(default_factory=list)
    what_is_not_working: list[str] = field(default_factory=list)
    recommended_decision: str = ROLLOUT_CONTINUE
    recommended_rationale: str = ""
    operator_summary: str = ""
    proof_met_count: int = 0
    proof_pending_count: int = 0
    first_value_reached: bool = False
    blocked_step_index: int = 0
    previous_decisions: list[RolloutDecision] = field(default_factory=list)
    generated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertical_id": self.vertical_id,
            "launch_kit_id": self.launch_kit_id,
            "curated_pack_id": self.curated_pack_id,
            "label": self.label,
            "evidence_summary": self.evidence_summary,
            "what_is_working": list(self.what_is_working),
            "what_is_not_working": list(self.what_is_not_working),
            "recommended_decision": self.recommended_decision,
            "recommended_rationale": self.recommended_rationale,
            "operator_summary": self.operator_summary,
            "proof_met_count": self.proof_met_count,
            "proof_pending_count": self.proof_pending_count,
            "first_value_reached": self.first_value_reached,
            "blocked_step_index": self.blocked_step_index,
            "previous_decisions": [d.to_dict() for d in self.previous_decisions],
            "generated_at_utc": self.generated_at_utc,
        }
