"""
M23N Phase 2: Guided onboarding flow. Local environment readiness, detected capabilities,
required approvals and why they matter, what remains blocked, recommended next steps.
CLI: workflow-dataset onboard, onboard status, onboard bootstrap.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.onboarding.bootstrap_profile import (
    build_bootstrap_profile,
    load_bootstrap_profile,
    save_bootstrap_profile,
    get_bootstrap_profile_path,
    BootstrapProfile,
)


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root().resolve()
    except Exception:
        return Path.cwd().resolve()


def get_onboarding_status(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> dict[str, Any]:
    """
    Return current onboarding status: profile (if any), env readiness, capabilities,
    approval status, blocked items, next steps. Read-only.
    """
    root = _repo_root(repo_root)
    status: dict[str, Any] = {
        "profile_path": str(get_bootstrap_profile_path(root)),
        "profile_exists": get_bootstrap_profile_path(root).exists(),
        "profile": None,
        "env_ready": False,
        "capabilities_detected": [],
        "approval_summary": {},
        "blocked_or_unavailable": [],
        "recommended_next_steps": [],
    }

    profile = load_bootstrap_profile(root)
    if profile is None:
        profile = build_bootstrap_profile(repo_root=root, config_path=config_path)
    status["profile"] = profile

    # Env readiness: config exists, edge checks
    config_file = root / config_path
    status["env_ready"] = config_file.exists() and profile.edge_ready
    status["edge_ready"] = profile.edge_ready
    status["edge_checks"] = f"{profile.edge_checks_passed}/{profile.edge_checks_total}"

    # Capabilities
    status["capabilities_detected"] = [
        {
            "adapter_id": a.get("adapter_id"),
            "available": a.get("available"),
            "supports_real": a.get("supports_real_execution"),
        }
        for a in profile.adapters_available
    ]

    # Approval summary
    status["approval_summary"] = {
        "registry_exists": profile.approval_registry_exists,
        "approved_paths_count": profile.approved_paths_count,
        "approved_apps_count": profile.approved_apps_count,
        "approved_action_scopes_count": profile.approved_action_scopes_count,
        "ready_for_real": profile.ready_for_real,
    }

    # Blocked: want real execution but no approvals
    if profile.trusted_real_actions and not profile.ready_for_real and not profile.approval_registry_exists:
        status["blocked_or_unavailable"].append(
            "Real execution is not allowed: no approval registry. Run 'workflow-dataset onboard bootstrap' or add data/local/capability_discovery/approvals.yaml."
        )
    elif not profile.approval_registry_exists and profile.capabilities_summary.get("action_scopes_count", 0) > 0:
        status["blocked_or_unavailable"].append(
            "Approval registry missing. Path and action scopes are not yet approved; real execution will be blocked until you approve them."
        )

    # Simulate-only areas (informational)
    for adapter_id in profile.simulate_only_adapters[:5]:
        status["blocked_or_unavailable"].append(f"Adapter {adapter_id!r} is simulate-only (no real execution).")

    # Recommended next steps
    if not profile.approval_registry_exists:
        status["recommended_next_steps"].append("Run 'workflow-dataset onboard bootstrap' to create a bootstrap profile and review approvals.")
        status["recommended_next_steps"].append("Run 'workflow-dataset onboard approve' to approve path/app/action scopes (optional).")
    if not profile.setup_session_id:
        status["recommended_next_steps"].append("Run 'workflow-dataset setup init' then 'workflow-dataset setup run' for artifact/setup onboarding.")
    if not profile.recommended_job_packs:
        status["recommended_next_steps"].append("Run 'workflow-dataset jobs seed' (if available) to install example job packs, then 'workflow-dataset onboard bootstrap' to refresh.")
    if not status["recommended_next_steps"]:
        status["recommended_next_steps"].append("Run 'workflow-dataset onboard' to see the full onboarding flow, or 'workflow-dataset console' for the operator console.")

    return status


def run_onboarding_flow(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
    *,
    persist_profile: bool = True,
) -> dict[str, Any]:
    """
    Run the onboarding flow: build profile, persist if requested, return status.
    Does not auto-grant approvals; user must run approval bootstrap separately.
    """
    root = _repo_root(repo_root)
    profile = build_bootstrap_profile(repo_root=root, config_path=config_path)
    if persist_profile:
        save_bootstrap_profile(profile, root)
    return get_onboarding_status(repo_root=root, config_path=config_path)


def format_onboarding_status(status: dict[str, Any]) -> str:
    """Format onboarding status as human-readable text."""
    lines = [
        "# Onboarding status",
        "",
        f"Profile path: {status.get('profile_path', '')}",
        f"Profile exists: {status.get('profile_exists')}",
        f"Environment ready: {status.get('env_ready')}",
        f"Edge checks: {status.get('edge_checks', '0/0')}",
        "",
        "## Approval summary",
        "",
    ]
    asum = status.get("approval_summary") or {}
    lines.append(f"- Registry exists: {asum.get('registry_exists')}")
    lines.append(f"- Approved paths: {asum.get('approved_paths_count', 0)}")
    lines.append(f"- Approved apps: {asum.get('approved_apps_count', 0)}")
    lines.append(f"- Approved action scopes: {asum.get('approved_action_scopes_count', 0)}")
    lines.append(f"- Ready for real execution: {asum.get('ready_for_real')}")
    lines.append("")

    blocked = status.get("blocked_or_unavailable") or []
    if blocked:
        lines.append("## Blocked or unavailable")
        lines.append("")
        for b in blocked[:15]:
            lines.append(f"- {b}")
        lines.append("")

    steps = status.get("recommended_next_steps") or []
    if steps:
        lines.append("## Recommended next steps")
        lines.append("")
        for s in steps:
            lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)
