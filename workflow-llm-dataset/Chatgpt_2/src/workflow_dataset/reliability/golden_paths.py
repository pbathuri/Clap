"""
M30E–M30H: Golden-path scenario set — clean install → onboard → workspace; project → plan → approve → simulate; etc.
"""

from __future__ import annotations

from workflow_dataset.reliability.models import GoldenPathScenario


# Step IDs used by harness: either acceptance journey steps or custom gather step_ids.
# Custom steps (e.g. workspace_open, project_plan_approve_simulate) are implemented in harness via gather_*.
ACCEPTANCE_FIRST_RUN_STEPS = [
    "install_readiness",
    "bootstrap_profile",
    "onboard_approvals",
    "select_pack",
    "run_first_simulate",
    "inspect_trust",
    "inspect_inbox",
]

BUILTIN_GOLDEN_PATHS: list[GoldenPathScenario] = [
    GoldenPathScenario(
        path_id="golden_first_run",
        name="Clean install → onboard → first workspace open",
        description="Install check, bootstrap profile, onboard approvals, select pack, first simulate, trust, inbox.",
        step_ids=ACCEPTANCE_FIRST_RUN_STEPS,
        subsystem_tags=["install", "onboarding", "packs", "trust", "inbox"],
    ),
    GoldenPathScenario(
        path_id="project_plan_approve_simulate",
        name="Project open → plan compile → approval → simulated execution",
        description="Project/plan state, approval readiness, simulate availability.",
        step_ids=["install_readiness", "bootstrap_profile", "project_plan_ready", "approval_ready", "simulate_available"],
        subsystem_tags=["install", "planner", "approvals", "executor"],
    ),
    GoldenPathScenario(
        path_id="pack_install_behavior_query",
        name="Pack install → behavior resolution → workspace command query",
        description="Pack registry, behavior resolution, workspace command availability.",
        step_ids=["install_readiness", "pack_registry_ready", "behavior_resolution", "workspace_command_query"],
        subsystem_tags=["packs", "runtime_mesh", "workspace"],
    ),
    GoldenPathScenario(
        path_id="recovery_blocked_upgrade",
        name="Recovery from blocked upgrade or broken pack state",
        description="Detect blocked upgrade or broken pack; validate recovery path (readiness only).",
        step_ids=["install_readiness", "upgrade_blockers", "pack_health"],
        subsystem_tags=["install", "packs", "distribution"],
    ),
    GoldenPathScenario(
        path_id="review_inbox_approve_progress",
        name="Review inbox → approve/defer → progress update",
        description="Inbox, approval/defer capability, progress board.",
        step_ids=["inspect_inbox", "approval_registry_ready", "progress_board_ready"],
        subsystem_tags=["inbox", "trust", "progress"],
    ),
]


def list_path_ids() -> list[str]:
    """Return all built-in golden path IDs."""
    return [p.path_id for p in BUILTIN_GOLDEN_PATHS]


def get_path(path_id: str) -> GoldenPathScenario | None:
    """Return golden path by id."""
    for p in BUILTIN_GOLDEN_PATHS:
        if p.path_id == path_id:
            return p
    return None
