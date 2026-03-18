"""
M39I–M39L: Build vertical launch kits from curated packs and vertical playbooks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_launch.models import (
    VerticalLaunchKit,
    FirstRunLaunchPath,
    RequiredSetupChecklist,
    SuccessProofMetric,
    FirstValueCheckpoint,
    SupportedUnsupportedBoundaries,
    RecoveryEscalationGuidance,
    OperatorSupportPlaybook,
)
from workflow_dataset.vertical_packs.registry import get_curated_pack
from workflow_dataset.vertical_packs.playbooks import get_playbook_for_vertical
from workflow_dataset.vertical_launch.success_proof import DEFAULT_PROOF_METRICS


def _first_run_path_from_pack(pack_id: str) -> FirstRunLaunchPath:
    pack = get_curated_pack(pack_id)
    if not pack or not pack.first_value_path:
        return FirstRunLaunchPath(
            path_id=f"{pack_id}_first_run",
            label="First run",
            entry_point="workflow-dataset package first-run",
            step_titles=["Bootstrap", "Runtime check", "Onboard approvals", "First simulate", "First real run"],
            required_surface_ids=["workspace_home", "queue_summary", "approvals_urgent"],
            first_value_milestone_id="first_simulate_done",
        )
    p = pack.first_value_path
    return FirstRunLaunchPath(
        path_id=p.path_id,
        label=p.label,
        entry_point=p.entry_point,
        step_titles=[s.title for s in p.steps],
        required_surface_ids=list(p.required_surface_ids),
        first_value_milestone_id=p.first_value_milestone_id or "first_simulate_done",
    )


def _setup_checklist_for_pack(pack_id: str) -> RequiredSetupChecklist:
    return RequiredSetupChecklist(
        checklist_id=f"{pack_id}_setup",
        label="Required setup",
        items=[
            {"id": "env_ready", "label": "Environment ready", "checked": False, "blocking": True, "command_hint": "workflow-dataset package first-run"},
            {"id": "approvals_minimal", "label": "Approvals minimal", "checked": False, "blocking": True, "command_hint": "workflow-dataset onboard status"},
            {"id": "surfaces_available", "label": "Surfaces available", "checked": False, "blocking": False, "command_hint": "workflow-dataset vertical-packs first-value --id " + pack_id},
        ],
        all_passed=False,
    )


def _checkpoints_from_pack(pack_id: str) -> list[FirstValueCheckpoint]:
    pack = get_curated_pack(pack_id)
    if not pack or not pack.first_value_path:
        return [
            FirstValueCheckpoint("cp_first_run", "First run", "first_run_completed", False),
            FirstValueCheckpoint("cp_first_simulate", "First simulate", "first_simulate_done", False),
            FirstValueCheckpoint("cp_first_real", "First real run", "first_real_done", False),
        ]
    return [
        FirstValueCheckpoint(f"cp_{m.milestone_id}", m.label, m.milestone_id, False)
        for m in pack.first_value_path.milestones
    ]


def _supported_unsupported_from_pack(pack_id: str) -> SupportedUnsupportedBoundaries:
    pack = get_curated_pack(pack_id)
    if not pack:
        return SupportedUnsupportedBoundaries(out_of_scope_hint="Curated pack not found.")
    req = pack.required_surfaces
    workflow_ids = (pack.core_workflow_path.workflow_ids if pack.core_workflow_path else []) or []
    return SupportedUnsupportedBoundaries(
        supported_surface_ids=list(req.required_surface_ids) + list(req.optional_surface_ids),
        unsupported_surface_ids=[],
        supported_workflow_ids=workflow_ids,
        out_of_scope_hint="Stay within required and optional surfaces for this vertical.",
    )


def _recovery_escalation_from_playbook(playbook: Any) -> list[RecoveryEscalationGuidance]:
    if not playbook:
        return []
    out = []
    for r in getattr(playbook, "recovery_paths", []) or []:
        out.append(RecoveryEscalationGuidance(
            recovery_path_id=getattr(r, "recovery_path_id", ""),
            label=getattr(r, "label", ""),
            steps_summary=[getattr(s, "label", "") for s in getattr(r, "steps", [])],
            escalation_command="workflow-dataset vertical-packs recovery --id " + getattr(playbook, "curated_pack_id", ""),
            when_to_narrow_scope="If user repeatedly fails at same step, narrow to simulate-only or reduce surfaces.",
            when_to_escalate_cohort="If triage recommends downgrade or critical issues on supported surface.",
            trust_review_hint="workflow-dataset trust cockpit",
        ))
    return out


def build_launch_kit_for_vertical(curated_pack_id: str, vertical_id: str = "") -> VerticalLaunchKit:
    """Build a vertical launch kit from a curated pack id. vertical_id defaults to curated_pack_id."""
    pack = get_curated_pack(curated_pack_id)
    playbook = get_playbook_for_vertical(curated_pack_id)
    vid = vertical_id or curated_pack_id
    launch_kit_id = f"{curated_pack_id}_launch"
    label = f"{pack.name} launch" if pack else f"{curated_pack_id} launch"
    description = pack.description if pack else f"Launch kit for {curated_pack_id}."

    operator = OperatorSupportPlaybook(
        playbook_id=getattr(playbook, "playbook_id", f"{curated_pack_id}_playbook"),
        launch_kit_id=launch_kit_id,
        label=playbook.label if playbook else f"Operator playbook for {curated_pack_id}",
        setup_guidance="Complete required setup: env ready, onboard approvals, then run first-value path.",
        first_value_coaching="Follow first-value path steps; use vertical-packs first-value --id " + curated_pack_id,
        common_recovery_guidance=getattr(playbook, "operator_guidance_stalled", "Run recovery for the blocked step; see vertical-packs recovery.") if playbook else "Use vertical-packs recovery --id " + curated_pack_id,
        when_to_narrow_scope="If user stalls repeatedly, narrow to simulate-only or fewer surfaces.",
        when_to_escalate_downgrade_cohort="If cohort health recommends downgrade or critical supported-surface issues.",
        trust_operator_review_hint="workflow-dataset trust cockpit; review before_real gates.",
        commands=getattr(playbook, "operator_commands_stalled", ["workflow-dataset vertical-packs progress"]) if playbook else ["workflow-dataset vertical-packs progress"],
    )

    return VerticalLaunchKit(
        launch_kit_id=launch_kit_id,
        vertical_id=vid,
        curated_pack_id=curated_pack_id,
        label=label,
        description=description,
        first_run_path=_first_run_path_from_pack(curated_pack_id),
        required_setup=_setup_checklist_for_pack(curated_pack_id),
        success_proof_metrics=list(DEFAULT_PROOF_METRICS),
        first_value_checkpoints=_checkpoints_from_pack(curated_pack_id),
        operator_playbook=operator,
        supported_unsupported=_supported_unsupported_from_pack(curated_pack_id),
        recovery_escalation=_recovery_escalation_from_playbook(playbook),
    )


def list_launch_kits() -> list[VerticalLaunchKit]:
    """List all launch kits (built from curated packs that have playbooks)."""
    from workflow_dataset.vertical_packs.playbooks import list_vertical_playbook_ids
    ids = list_vertical_playbook_ids()
    return [build_launch_kit_for_vertical(pid) for pid in ids]
