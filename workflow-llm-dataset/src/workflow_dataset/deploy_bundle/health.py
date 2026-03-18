"""
M40E–M40H: Deployment health summary — validation, upgrade/rollback readiness, recovery posture, blocked risks.
"""

from __future__ import annotations

from workflow_dataset.deploy_bundle.registry import get_deployment_bundle
from workflow_dataset.deploy_bundle.store import get_active_bundle
from workflow_dataset.deploy_bundle.validation import validate_bundle
from workflow_dataset.deploy_bundle.upgrade_rollback import get_supported_upgrade_path, get_rollback_readiness
from workflow_dataset.deploy_bundle.models import DeploymentHealthSummary


def build_deployment_health_summary(
    bundle_id: str = "",
    repo_root: object = None,
) -> DeploymentHealthSummary:
    """
    Build deployment health summary for mission control and reports.
    If bundle_id is empty, use active bundle id.
    """
    active = get_active_bundle(repo_root)
    active_id = active.get("active_bundle_id", "")
    if not bundle_id:
        bundle_id = active_id or "founder_operator_prod"
    bundle = get_deployment_bundle(bundle_id)
    if not bundle:
        return DeploymentHealthSummary(
            bundle_id=bundle_id,
            validation_passed=False,
            validation_errors=[f"Bundle not found: {bundle_id}"],
            active_bundle_id=active_id,
        )
    validation = validate_bundle(bundle_id, repo_root)
    upgrade_path = get_supported_upgrade_path(bundle_id, repo_root)
    rollback = get_rollback_readiness(bundle_id, repo_root)
    blocked: list[str] = []
    if validation.errors:
        blocked.extend(validation.errors[:5])
    if upgrade_path.get("blocked_reasons"):
        blocked.extend(upgrade_path["blocked_reasons"][:3])
    if not rollback.get("ready", False) and bundle.supported_rollback_path.supported:
        blocked.append("Rollback: no checkpoint found; create one before upgrade.")
    recovery_summary = (
        bundle.recovery_posture.degraded_startup_guidance[:100] + "..."
        if len(bundle.recovery_posture.degraded_startup_guidance) > 100
        else bundle.recovery_posture.degraded_startup_guidance
    )
    return DeploymentHealthSummary(
        bundle_id=bundle_id,
        validation_passed=validation.passed,
        validation_errors=list(validation.errors),
        validation_warnings=list(validation.warnings),
        upgrade_readiness=upgrade_path.get("can_proceed", False),
        upgrade_readiness_reason="; ".join(upgrade_path.get("blocked_reasons", [])) or "OK",
        rollback_readiness=rollback.get("ready", False),
        rollback_readiness_reason="Checkpoint available" if rollback.get("latest_checkpoint_id") else "No checkpoint",
        recovery_posture_summary=recovery_summary,
        blocked_deployment_risks=blocked,
        active_bundle_id=active_id,
    )
