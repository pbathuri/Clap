"""
M40E–M40H: Production deployment bundle registry — built-in bundles for chosen verticals.
"""

from __future__ import annotations

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.deploy_bundle.models import (
    ProductionDeploymentBundle,
    BundleContents,
    RequiredRuntimeProfile,
    RequiredPacksAssets,
    SupportedUpgradePath,
    SupportedRollbackPath,
    RecoveryPosture,
)


def _founder_operator_prod() -> ProductionDeploymentBundle:
    return ProductionDeploymentBundle(
        bundle_id="founder_operator_prod",
        name="Founder / Operator (production cut)",
        description="Production deployment bundle for founder/operator vertical: morning ops, weekly status, supervised operator trust, local-first.",
        version="1.0",
        curated_pack_id="founder_operator_core",
        contents=BundleContents(
            curated_pack_id="founder_operator_core",
            required_runtime=RequiredRuntimeProfile(
                min_python="3.11",
                required_capabilities=["config_exists", "edge_checks", "approval_registry_optional", "job_packs_loaded", "macros_available"],
                runtime_prerequisites=["config_exists", "edge_checks", "job_packs_loaded", "macros_available"],
                machine_assumptions={"local_only": True, "python_required": True},
            ),
            required_packs=RequiredPacksAssets(
                pack_ids=[],
                value_pack_id="founder_ops_plus",
                workflow_ids=["morning_ops", "weekly_status_from_notes", "weekly_status", "morning_reporting"],
                required_approvals_setup=["approval_registry_optional", "path_workspace", "path_repo", "apply_confirm"],
            ),
            allowed_trust_preset_ids=["supervised_operator", "cautious", "bounded_trusted_routine"],
            required_queue_day_workspace_refs={
                "workday_preset_id": "founder_operator",
                "default_experience_profile_id": "founder_calm",
            },
            support_recovery_refs=[
                "docs/rollout/OPERATOR_RUNBOOKS.md",
                "docs/rollout/RECOVERY_ESCALATION.md",
                "workflow-dataset recovery suggest --case failed_upgrade",
                "workflow-dataset vertical-packs recovery --id founder_operator_core --step <N>",
            ],
            excluded_surface_ids=[],
            quarantined_surface_metadata={},
        ),
        supported_upgrade_path=SupportedUpgradePath(
            from_version_min="0.1.0",
            to_version_max="1.x",
            channel_ids=["stable", "preview"],
            reversible=True,
            migration_hints=["Run workflow-dataset package install-check before and after upgrade.", "Create rollback checkpoint before upgrade."],
        ),
        supported_rollback_path=SupportedRollbackPath(
            supported=True,
            checkpoint_required_before_upgrade=True,
            rollback_hints=["Use workflow-dataset upgrade rollback --checkpoint <id> if upgrade fails.", "Checkpoint is created automatically before apply_upgrade."],
        ),
        recovery_posture=RecoveryPosture(
            applicable_recovery_case_ids=["failed_upgrade", "blocked_approval_policy", "stuck_project_session_agent", "invalid_workspace_state", "broken_pack_state"],
            vertical_playbook_id="founder_operator_playbook",
            degraded_startup_guidance="If startup fails: run workflow-dataset package install-check; run workflow-dataset vertical-packs progress; run workflow-dataset recovery suggest.",
            recovery_doc_refs=["docs/rollout/RECOVERY_ESCALATION.md", "workflow-dataset vertical-packs playbook --id founder_operator_core"],
        ),
        generated_at=utc_now_iso(),
    )


BUILTIN_DEPLOYMENT_BUNDLES: list[ProductionDeploymentBundle] = [
    _founder_operator_prod(),
]


def get_deployment_bundle(bundle_id: str) -> ProductionDeploymentBundle | None:
    """Return production deployment bundle by id."""
    for b in BUILTIN_DEPLOYMENT_BUNDLES:
        if b.bundle_id == bundle_id:
            return b
    return None


def list_deployment_bundle_ids() -> list[str]:
    """Return all built-in deployment bundle ids."""
    return [b.bundle_id for b in BUILTIN_DEPLOYMENT_BUNDLES]
