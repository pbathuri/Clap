"""
M30H.1: Degraded mode profiles — what still works vs what is disabled when subsystems are unavailable.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.reliability.models import DegradedModeProfile


BUILTIN_DEGRADED_PROFILES: list[DegradedModeProfile] = [
    DegradedModeProfile(
        profile_id="install_blocked",
        name="Install blocked",
        description="Install check failed; first-run and upgrade paths blocked.",
        disabled_subsystems=["install", "distribution"],
        still_works=["inbox read-only", "trust status", "workspace read-only", "recovery suggest"],
        disabled_flows=["golden_first_run", "project_plan_approve_simulate", "pack_install_behavior_query", "recovery_blocked_upgrade"],
        operator_explanation="Install or prerequisites failed. You can still run inbox, trust status, workspace read-only, and recovery suggest. First-run, plan/approve/simulate, pack install, and upgrade recovery are disabled until install check passes.",
    ),
    DegradedModeProfile(
        profile_id="packs_unavailable",
        name="Packs unavailable",
        description="Pack registry or behavior resolution unavailable.",
        disabled_subsystems=["packs", "runtime_mesh"],
        still_works=["golden_first_run (if install passed)", "inbox", "trust", "planner compile (no pack context)", "recovery suggest"],
        disabled_flows=["pack_install_behavior_query", "behavior_resolution", "workspace_command_query"],
        operator_explanation="Packs or runtime mesh unavailable. First-run and inbox/trust/planner may still work. Pack install path and workspace command query are disabled. Use recovery guide: broken_pack_state or missing_runtime_capability.",
    ),
    DegradedModeProfile(
        profile_id="approval_blocked",
        name="Approval / policy blocked",
        description="Approval registry missing or policy blocks execution.",
        disabled_subsystems=["trust", "human_policy"],
        still_works=["simulate only", "inbox", "planner", "workspace", "pack list", "recovery suggest"],
        disabled_flows=["real apply", "approval_gated_execution", "review_inbox_approve_progress"],
        operator_explanation="Approvals or policy not ready. Simulate-only, inbox, planner, workspace, and pack list still work. Real apply and approval-gated execution are disabled. Use recovery guide: blocked_approval_policy.",
    ),
    DegradedModeProfile(
        profile_id="workspace_degraded",
        name="Workspace degraded",
        description="Active work context or workspace state invalid.",
        disabled_subsystems=["workspace"],
        still_works=["golden_first_run", "inbox", "trust", "pack_install_behavior_query (up to behavior_resolution)", "recovery suggest"],
        disabled_flows=["workspace_command_query", "command_center_workspace_filter"],
        operator_explanation="Workspace context unavailable. Core flows and pack/behavior checks can still run; workspace command query and workspace-filtered command center are disabled. Use recovery guide: invalid_workspace_state.",
    ),
    DegradedModeProfile(
        profile_id="planner_blocked",
        name="Planner / project blocked",
        description="Plan compile or project state unavailable.",
        disabled_subsystems=["planner", "executor"],
        still_works=["golden_first_run", "inbox", "trust", "pack_install_behavior_query", "recovery suggest"],
        disabled_flows=["project_plan_approve_simulate", "plan_preview", "simulate_available"],
        operator_explanation="Planner or executor unavailable. First-run, inbox, trust, and pack path may work. Project plan/approve/simulate and plan preview are disabled. Use recovery guide: stuck_project_session_agent.",
    ),
    DegradedModeProfile(
        profile_id="full_degraded",
        name="Multiple subsystems degraded",
        description="More than one subsystem unavailable; minimal safe set only.",
        disabled_subsystems=[],
        still_works=["recovery suggest", "recovery guide", "reliability list", "reliability report"],
        disabled_flows=["golden_first_run", "project_plan_approve_simulate", "pack_install_behavior_query", "recovery_blocked_upgrade", "review_inbox_approve_progress"],
        operator_explanation="Multiple subsystems down. Only recovery and reliability commands are recommended. Run reliability report and recovery suggest to identify fixes.",
    ),
]


def list_profile_ids() -> list[str]:
    """Return all built-in degraded profile IDs."""
    return [p.profile_id for p in BUILTIN_DEGRADED_PROFILES]


def get_profile(profile_id: str) -> DegradedModeProfile | None:
    """Return degraded profile by id."""
    for p in BUILTIN_DEGRADED_PROFILES:
        if p.profile_id == profile_id:
            return p
    return None


def resolve_profile_for_subsystem(subsystem: str) -> DegradedModeProfile | None:
    """Return the profile that corresponds to this subsystem being unavailable (first match)."""
    for p in BUILTIN_DEGRADED_PROFILES:
        if subsystem in p.disabled_subsystems:
            return p
    return get_profile("full_degraded")


def resolve_profile_for_unavailable_subsystems(subsystems: list[str]) -> DegradedModeProfile:
    """Return best-matching profile when given list of unavailable subsystems. Prefer specific profile if one matches; else full_degraded."""
    if not subsystems:
        return get_profile("full_degraded") or BUILTIN_DEGRADED_PROFILES[-1]
    for p in BUILTIN_DEGRADED_PROFILES:
        if p.profile_id == "full_degraded":
            continue
        if set(subsystems) & set(p.disabled_subsystems):
            return p
    return get_profile("full_degraded") or BUILTIN_DEGRADED_PROFILES[-1]


def profile_to_dict(p: DegradedModeProfile) -> dict[str, Any]:
    """Serialize profile for CLI/report."""
    return {
        "profile_id": p.profile_id,
        "name": p.name,
        "description": p.description,
        "disabled_subsystems": p.disabled_subsystems,
        "still_works": p.still_works,
        "disabled_flows": p.disabled_flows,
        "operator_explanation": p.operator_explanation,
    }
