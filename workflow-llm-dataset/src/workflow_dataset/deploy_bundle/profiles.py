"""
M40H.1: Deployment profiles — demo, internal production-like, careful production cut.
"""

from __future__ import annotations

from workflow_dataset.deploy_bundle.models import (
    DeploymentProfile,
    PROFILE_DEMO,
    PROFILE_INTERNAL_PRODUCTION_LIKE,
    PROFILE_CAREFUL_PRODUCTION_CUT,
)


def _demo_profile() -> DeploymentProfile:
    return DeploymentProfile(
        profile_id=PROFILE_DEMO,
        name="Demo",
        description="Demo deployment: showcase flows, simulate-only or approval-gated real runs. Not for sustained production use.",
        profile_type=PROFILE_DEMO,
        recommended_bundle_ids=["founder_operator_prod"],
        allow_operator_mode=True,
        allow_real_run_with_approval=True,
        pause_guidance="Pause demo when preparing for a live audience or when environment is unstable. Prefer simulate for demos.",
        repair_guidance="If demo fails repeatedly, switch to recovery maintenance mode and run workflow-dataset deploy-bundle recovery-report; fix install or approval scope.",
    )


def _internal_production_like_profile() -> DeploymentProfile:
    return DeploymentProfile(
        profile_id=PROFILE_INTERNAL_PRODUCTION_LIKE,
        name="Internal production-like",
        description="Internal production-like: real workflows with approval gates, operator mode allowed. For internal teams before careful production cut.",
        profile_type=PROFILE_INTERNAL_PRODUCTION_LIKE,
        recommended_bundle_ids=["founder_operator_prod"],
        allow_operator_mode=True,
        allow_real_run_with_approval=True,
        pause_guidance="Pause when upgrading or when triage/reliability reports show unresolved issues. Use safe_pause mode during upgrades.",
        repair_guidance="If validation fails or upgrade blocks, enter recovery mode; run deploy-bundle validate and recovery-report. Resolve blockers before resuming.",
    )


def _careful_production_cut_profile() -> DeploymentProfile:
    return DeploymentProfile(
        profile_id=PROFILE_CAREFUL_PRODUCTION_CUT,
        name="Careful production cut",
        description="Careful production cut: frozen scope, validated bundle, upgrade/rollback readiness required. For sustained production use.",
        profile_type=PROFILE_CAREFUL_PRODUCTION_CUT,
        recommended_bundle_ids=["founder_operator_prod"],
        allow_operator_mode=True,
        allow_real_run_with_approval=True,
        pause_guidance="Pause when deploy-bundle validate fails, upgrade is in progress, or rollback readiness is lost. Do not run real jobs until repair completes.",
        repair_guidance="Run deploy-bundle validate and recovery-report. Fix all validation errors; ensure rollback checkpoint exists before any upgrade. Resume only when validation_passed and upgrade_readiness are true.",
    )


BUILTIN_DEPLOYMENT_PROFILES: list[DeploymentProfile] = [
    _demo_profile(),
    _internal_production_like_profile(),
    _careful_production_cut_profile(),
]


def get_deployment_profile(profile_id: str) -> DeploymentProfile | None:
    """Return deployment profile by id."""
    for p in BUILTIN_DEPLOYMENT_PROFILES:
        if p.profile_id == profile_id:
            return p
    return None


def list_deployment_profile_ids() -> list[str]:
    """Return all built-in deployment profile ids."""
    return [p.profile_id for p in BUILTIN_DEPLOYMENT_PROFILES]
