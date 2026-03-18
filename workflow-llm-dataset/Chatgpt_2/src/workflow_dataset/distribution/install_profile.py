"""
M24R–M24U: Pack-aware install profile and field deployment profile.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.distribution.models import FieldDeploymentProfile, PackAwareInstallProfile


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


# Pack id -> default runtime prereqs and trust checks (first-draft)
PACK_DEFAULTS: dict[str, dict[str, Any]] = {
    "founder_ops_starter": {
        "runtime_prerequisites": ["config_exists", "edge_checks", "job_packs_loaded", "macros_available"],
        "pack_provisioning_prerequisites": ["bootstrap_profile", "onboarding_status"],
        "required_capabilities": ["config_exists", "edge_checks", "approval_registry_optional"],
        "required_approvals_setup": ["approval_registry_optional", "path_workspace", "apply_confirm"],
        "trust_readiness_checks": ["trust_cockpit_available", "simulate_first"],
    },
    "analyst_starter": {
        "runtime_prerequisites": ["config_exists", "edge_checks", "job_packs_loaded", "retrieval_optional"],
        "pack_provisioning_prerequisites": ["bootstrap_profile", "onboarding_status"],
        "required_capabilities": ["config_exists", "edge_checks", "approval_registry_optional"],
        "required_approvals_setup": ["approval_registry_optional", "path_workspace", "apply_confirm", "data_export"],
        "trust_readiness_checks": ["trust_cockpit_available", "simulate_first"],
    },
    "developer_starter": {
        "runtime_prerequisites": ["config_exists", "edge_checks", "codebase_task_backend_optional"],
        "pack_provisioning_prerequisites": ["bootstrap_profile", "onboarding_status"],
        "required_capabilities": ["config_exists", "edge_checks", "approval_registry_optional"],
        "required_approvals_setup": ["path_repo", "apply_confirm"],
        "trust_readiness_checks": ["simulate_only_for_task_replay"],
    },
    "document_worker_starter": {
        "runtime_prerequisites": ["config_exists", "edge_checks", "job_packs_loaded", "corpus_optional"],
        "pack_provisioning_prerequisites": ["bootstrap_profile", "onboarding_status"],
        "required_capabilities": ["config_exists", "edge_checks", "approval_registry_optional"],
        "required_approvals_setup": ["approval_registry_optional", "path_workspace", "apply_confirm"],
        "trust_readiness_checks": ["trust_cockpit_available", "simulate_first"],
    },
}


def build_pack_aware_install_profile(
    pack_id: str,
    repo_root: Path | str | None = None,
) -> PackAwareInstallProfile:
    """Build pack-aware install profile for pack_id (starter_kit_id)."""
    root = _repo_root(repo_root)
    profile = PackAwareInstallProfile(pack_id=pack_id)
    try:
        from workflow_dataset.starter_kits.registry import get_kit
        kit = get_kit(pack_id)
        if kit:
            profile.pack_name = getattr(kit, "name", pack_id)
            profile.required_approvals_setup = list(getattr(kit, "approvals_likely_needed", []) or [])
            fvf = getattr(kit, "first_value_flow", None)
            if fvf:
                profile.first_value_steps = ["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate"]
    except Exception:
        pass
    defaults = PACK_DEFAULTS.get(pack_id, {})
    profile.required_capabilities = defaults.get("required_capabilities", ["config_exists", "edge_checks"])
    profile.required_approvals_setup = profile.required_approvals_setup or defaults.get("required_approvals_setup", [])
    profile.runtime_prerequisites = defaults.get("runtime_prerequisites", [])
    profile.pack_provisioning_prerequisites = defaults.get("pack_provisioning_prerequisites", [])
    profile.machine_assumptions = {"local_only": True, "python_required": True}
    return profile


def build_field_deployment_profile(
    pack_id: str,
    repo_root: Path | str | None = None,
) -> FieldDeploymentProfile:
    """Build field deployment profile for pack_id: runtime prereqs, pack prereqs, trust checks, first-value run."""
    root = _repo_root(repo_root)
    pack_profile = build_pack_aware_install_profile(pack_id, root)
    defaults = PACK_DEFAULTS.get(pack_id, {})
    first_run_cmd = ""
    first_run_notes = ""
    try:
        from workflow_dataset.starter_kits.registry import get_kit
        kit = get_kit(pack_id)
        if kit and getattr(kit, "first_value_flow", None):
            fvf = kit.first_value_flow
            first_run_cmd = getattr(fvf, "first_run_command", "") or ""
            first_run_notes = getattr(fvf, "what_to_do_next", "") or ""
    except Exception:
        pass
    return FieldDeploymentProfile(
        profile_id=f"field_{pack_id}",
        pack_id=pack_id,
        pack_name=pack_profile.pack_name,
        description=f"Field deployment profile for {pack_id}.",
        repo_root=str(root),
        generated_at=utc_now_iso(),
        runtime_prerequisites=pack_profile.runtime_prerequisites,
        pack_provisioning_prerequisites=pack_profile.pack_provisioning_prerequisites,
        required_capabilities=pack_profile.required_capabilities,
        required_approvals_setup=pack_profile.required_approvals_setup,
        trust_readiness_checks=defaults.get("trust_readiness_checks", []),
        first_value_run_command=first_run_cmd,
        first_value_run_notes=first_run_notes,
        machine_assumptions=pack_profile.machine_assumptions,
    )
