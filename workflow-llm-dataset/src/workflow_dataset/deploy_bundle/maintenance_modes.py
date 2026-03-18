"""
M40H.1: Maintenance modes — upgrade, recovery, audit review, safe pause. Operator guidance for pause/repair.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.deploy_bundle.models import (
    MaintenanceMode,
    MaintenanceModeReport,
    MODE_UPGRADE,
    MODE_RECOVERY,
    MODE_AUDIT_REVIEW,
    MODE_SAFE_PAUSE,
    PROFILE_CAREFUL_PRODUCTION_CUT,
)
from workflow_dataset.deploy_bundle.profiles import get_deployment_profile


def _upgrade_mode() -> MaintenanceMode:
    return MaintenanceMode(
        mode_id=MODE_UPGRADE,
        name="Upgrade",
        description="Deployment is in upgrade mode: version or bundle update in progress.",
        when_to_use="During or immediately after running deploy-bundle build or install_upgrade apply.",
        operator_guidance_pause="Pause real runs and operator-mode automation during upgrade. Run only simulate or read-only commands until upgrade and validation succeed.",
        operator_guidance_repair="If upgrade fails: run deploy-bundle recovery-report; use rollback checkpoint if available (workflow-dataset upgrade rollback). Then run deploy-bundle validate.",
        recommended_actions=[
            "workflow-dataset deploy-bundle validate",
            "workflow-dataset package install-check",
            "workflow-dataset deploy-bundle upgrade-path",
        ],
        blocks_real_run=True,
        blocks_operator_mode=True,
    )


def _recovery_mode() -> MaintenanceMode:
    return MaintenanceMode(
        mode_id=MODE_RECOVERY,
        name="Recovery",
        description="Deployment is in recovery: fixing install, readiness, or rollback.",
        when_to_use="When validation fails, upgrade is blocked, or rollback is needed.",
        operator_guidance_pause="Keep deployment paused until recovery steps complete. Do not run real jobs or enable operator mode until deploy-bundle validate passes.",
        operator_guidance_repair="Run deploy-bundle recovery-report and follow applicable recovery cases. Fix install check, approval scope, or rollback; then validate again.",
        recommended_actions=[
            "workflow-dataset deploy-bundle recovery-report",
            "workflow-dataset deploy-bundle validate",
            "workflow-dataset vertical-packs recovery --id <curated_pack> --step <N> if path blocked",
        ],
        blocks_real_run=True,
        blocks_operator_mode=True,
    )


def _audit_review_mode() -> MaintenanceMode:
    return MaintenanceMode(
        mode_id=MODE_AUDIT_REVIEW,
        name="Audit review",
        description="Deployment is under audit or review: optional pause for inspection.",
        when_to_use="When operator wants to review state, triage, or handoff without running new jobs.",
        operator_guidance_pause="Optional pause: real runs and operator mode can continue if approval gates are in place. Use this mode to run mission-control and triage without changing state.",
        operator_guidance_repair="No repair required for audit. Exit audit_review when review is complete.",
        recommended_actions=[
            "workflow-dataset mission-control report",
            "workflow-dataset cohort health",
            "workflow-dataset deploy-bundle show",
        ],
        blocks_real_run=False,
        blocks_operator_mode=False,
    )


def _safe_pause_mode() -> MaintenanceMode:
    return MaintenanceMode(
        mode_id=MODE_SAFE_PAUSE,
        name="Safe pause",
        description="Deployment is in safe pause: no real runs, no operator-mode automation.",
        when_to_use="When operator needs to stop all automated and real runs temporarily (e.g. before upgrade, during incident).",
        operator_guidance_pause="Deployment is paused. Do not run real jobs or enable operator mode until pause is lifted.",
        operator_guidance_repair="To resume: clear maintenance mode (or set to normal), run deploy-bundle validate, then resume workflows as needed.",
        recommended_actions=[
            "workflow-dataset deploy-bundle validate",
            "workflow-dataset deploy-bundle show",
        ],
        blocks_real_run=True,
        blocks_operator_mode=True,
    )


BUILTIN_MAINTENANCE_MODES: list[MaintenanceMode] = [
    _upgrade_mode(),
    _recovery_mode(),
    _audit_review_mode(),
    _safe_pause_mode(),
]


def get_maintenance_mode(mode_id: str) -> MaintenanceMode | None:
    """Return maintenance mode by id."""
    for m in BUILTIN_MAINTENANCE_MODES:
        if m.mode_id == mode_id:
            return m
    return None


def list_maintenance_mode_ids() -> list[str]:
    """Return all built-in maintenance mode ids."""
    return [m.mode_id for m in BUILTIN_MAINTENANCE_MODES]


def build_maintenance_mode_report(
    repo_root: object = None,
) -> MaintenanceModeReport:
    """
    Build maintenance mode report: active profile, active mode, should_pause, should_repair,
    operator guidance. Uses store for active profile/mode; infers should_repair from deploy_bundle health.
    """
    from workflow_dataset.deploy_bundle.store import get_active_bundle, get_deploy_bundle_dir
    from pathlib import Path

    root = Path(repo_root).resolve() if repo_root else None
    if root is None:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()

    active = get_active_bundle(repo_root=root)
    profile_id = active.get("deployment_profile_id", "") or PROFILE_CAREFUL_PRODUCTION_CUT
    mode_id = active.get("maintenance_mode_id", "")

    profile = get_deployment_profile(profile_id)
    mode = get_maintenance_mode(mode_id) if mode_id else None

    report = MaintenanceModeReport(
        active_profile_id=profile_id,
        active_maintenance_mode_id=mode_id,
        profile=profile.to_dict() if profile else {},
        maintenance_mode=mode.to_dict() if mode else {},
    )

    # Should pause: if in upgrade/recovery/safe_pause, or if health is blocked
    if mode:
        report.should_pause = mode.blocks_real_run or mode.blocks_operator_mode
        report.pause_reason = mode.operator_guidance_pause or ""
        report.operator_guidance_summary = mode.operator_guidance_pause
        report.recommended_actions = list(mode.recommended_actions)
    if profile:
        if not report.operator_guidance_summary:
            report.operator_guidance_summary = profile.pause_guidance or profile.repair_guidance
        if not report.recommended_actions:
            report.recommended_actions = []

    # Should repair: when validation fails or blocked_risks
    try:
        from workflow_dataset.deploy_bundle.health import build_deployment_health_summary
        bundle_id = active.get("active_bundle_id", "") or "founder_operator_prod"
        health = build_deployment_health_summary(bundle_id=bundle_id, repo_root=root)
        if not health.validation_passed or health.blocked_deployment_risks:
            report.should_repair = True
            report.repair_reason = "; ".join(health.blocked_deployment_risks[:3]) if health.blocked_deployment_risks else "Validation failed."
            if not report.operator_guidance_summary and profile:
                report.operator_guidance_summary = profile.repair_guidance
            report.recommended_actions = list(report.recommended_actions) or [
                "workflow-dataset deploy-bundle validate",
                "workflow-dataset deploy-bundle recovery-report",
            ]
    except Exception:
        pass

    return report
