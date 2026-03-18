"""
M40I: Production runbook assembly from vertical playbook + static operating/support/recovery steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.production_launch.models import (
    DailyOperatingReviewStep,
    OperatingChecklistItem,
    ProductionRunbook,
    RecoveryEscalationPath,
    SupportPath,
    TrustedRoutineReviewStep,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _static_operating_checklist() -> list[OperatingChecklistItem]:
    """Default pre-launch operating checklist items."""
    return [
        OperatingChecklistItem("env_health", "Environment health required_ok", "workflow-dataset health", True),
        OperatingChecklistItem("release_readiness", "Release readiness not blocked", "workflow-dataset release readiness", True),
        OperatingChecklistItem("vertical_scope", "Vertical scope and surface policy known", "workflow-dataset verticals scope-report", True),
        OperatingChecklistItem("trust_cockpit", "Trust/approval registry present", "workflow-dataset trust cockpit", True),
        OperatingChecklistItem("first_value_path", "First-value path progress acceptable", "workflow-dataset vertical-packs first-value", False),
    ]


def _static_daily_review() -> list[DailyOperatingReviewStep]:
    """Default daily operating review steps."""
    return [
        DailyOperatingReviewStep("mission_control", "Mission control snapshot", "workflow-dataset mission-control", "daily"),
        DailyOperatingReviewStep("release_readiness", "Release readiness status", "workflow-dataset release readiness", "daily"),
        DailyOperatingReviewStep("triage", "Triage / cohort health", "workflow-dataset release triage", "daily"),
        DailyOperatingReviewStep("launch_decision", "Launch decision pack", "workflow-dataset launch-decision-pack", "daily"),
    ]


def _static_recovery_paths() -> list[RecoveryEscalationPath]:
    """Default recovery/escalation path refs."""
    return [
        RecoveryEscalationPath("recovery_guide", "Recovery guide", "workflow-dataset recovery guide --case failed_upgrade", "Install/upgrade and recovery"),
        RecoveryEscalationPath("recovery_suggest", "Recovery suggest by subsystem", "workflow-dataset recovery suggest --subsystem executor", "Executor/run blocked"),
        RecoveryEscalationPath("vertical_recovery", "Vertical pack recovery", "workflow-dataset vertical-packs recovery --id <pack_id> --step <N>", "Path stalled"),
    ]


def _static_support_paths() -> list[SupportPath]:
    """Default support path refs."""
    return [
        SupportPath("release_triage", "Release triage", "workflow-dataset release triage"),
        SupportPath("supportability", "Supportability report", "workflow-dataset release supportability"),
        SupportPath("handoff_pack", "Handoff pack", "workflow-dataset release handoff-pack"),
    ]


def _static_trusted_routine_steps() -> list[TrustedRoutineReviewStep]:
    """Default trusted routine review steps."""
    return [
        TrustedRoutineReviewStep("trust_cockpit", "Trust cockpit and approvals", "workflow-dataset trust cockpit", "pre_launch"),
        TrustedRoutineReviewStep("reliability_run", "Reliability golden-path run", "workflow-dataset reliability run", "pre_launch"),
    ]


def get_production_runbook(
    vertical_id: str,
    repo_root: Path | str | None = None,
) -> ProductionRunbook:
    """
    Build production runbook for the given vertical. Merges vertical playbook (recovery paths, operator guidance)
    with static operating checklist, daily review, support paths, and trusted routine steps.
    """
    root = _repo_root(repo_root)
    label = f"Production runbook: {vertical_id}" if vertical_id else "Production runbook (no vertical)"

    operating_checklist = list(_static_operating_checklist())
    daily_review = list(_static_daily_review())
    recovery_paths = list(_static_recovery_paths())
    support_paths = list(_static_support_paths())
    trusted_steps = list(_static_trusted_routine_steps())

    # Merge vertical playbook recovery paths and operator guidance if available
    if vertical_id:
        try:
            from workflow_dataset.vertical_packs.playbooks import get_playbook_for_vertical
            vp = get_playbook_for_vertical(vertical_id)
            if vp:
                label = f"Production runbook: {vp.label}"
                for rp in vp.recovery_paths:
                    recovery_paths.append(RecoveryEscalationPath(
                        rp.path_id,
                        rp.label,
                        rp.steps[0].command if rp.steps else "",
                        rp.label,
                    ))
                # Add operator commands when stalled as a recovery path ref
                if vp.operator_commands_stalled:
                    recovery_paths.append(RecoveryEscalationPath(
                        "vertical_stalled",
                        "Path stalled — operator commands",
                        vp.operator_commands_stalled[0] if vp.operator_commands_stalled else "",
                        vp.operator_guidance_stalled or "",
                    ))
        except Exception:
            pass

    return ProductionRunbook(
        vertical_id=vertical_id,
        label=label,
        description="First-draft production runbook for operating and supporting the chosen vertical after release.",
        operating_checklist=operating_checklist,
        daily_operating_review=daily_review,
        recovery_paths=recovery_paths,
        support_paths=support_paths,
        trusted_routine_review_steps=trusted_steps,
    )
