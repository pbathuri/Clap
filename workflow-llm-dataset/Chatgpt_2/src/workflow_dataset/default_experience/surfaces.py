"""
M37A–M37D: Surface classification — default_visible vs advanced vs expert.
"""

from __future__ import annotations

from workflow_dataset.default_experience.models import (
    SURFACE_ADVANCED,
    SURFACE_DEFAULT_VISIBLE,
    SURFACE_EXPERT,
    SurfaceClassification,
)

# Surfaces shown by default in calm/first-user experience
DEFAULT_VISIBLE_SURFACES: list[SurfaceClassification] = [
    SurfaceClassification("workspace_home", "Workspace home (calm)", SURFACE_DEFAULT_VISIBLE, "workspace home --profile calm_default", False),
    SurfaceClassification("day_status", "Day status", SURFACE_DEFAULT_VISIBLE, "day status", False),
    SurfaceClassification("queue_summary", "Queue summary", SURFACE_DEFAULT_VISIBLE, "queue summary", False),
    SurfaceClassification("approvals_urgent", "Urgent approvals", SURFACE_DEFAULT_VISIBLE, "inbox list", False),
    SurfaceClassification("continuity_carry_forward", "Carry-forward / resume", SURFACE_DEFAULT_VISIBLE, "day resume", False),
]

# Advanced: power users, not in calm home by default
ADVANCED_SURFACES: list[SurfaceClassification] = [
    SurfaceClassification("workspace_home_full", "Workspace home (full)", SURFACE_ADVANCED, "workspace home", True),
    SurfaceClassification("mission_control", "Mission control report", SURFACE_ADVANCED, "mission-control", True),
    SurfaceClassification("queue_list", "Queue list (all modes)", SURFACE_ADVANCED, "queue list", True),
    SurfaceClassification("review_studio", "Review studio", SURFACE_ADVANCED, "inbox-studio", True),
    SurfaceClassification("timeline", "Timeline", SURFACE_ADVANCED, "timeline latest", True),
    SurfaceClassification("automation_inbox", "Automation inbox", SURFACE_ADVANCED, "automation-inbox list", True),
    SurfaceClassification("day_modes", "Day mode set (all)", SURFACE_ADVANCED, "day modes", True),
]

# Expert: operators, config, policy, trust
EXPERT_SURFACES: list[SurfaceClassification] = [
    SurfaceClassification("trust_cockpit", "Trust cockpit", SURFACE_EXPERT, "trust cockpit", True),
    SurfaceClassification("policy_board", "Human policy", SURFACE_EXPERT, "policy board", True),
    SurfaceClassification("operator_mode", "Operator mode controls", SURFACE_EXPERT, "day mode --set operator_mode", True),
    SurfaceClassification("approvals_policy", "Approvals / policy", SURFACE_EXPERT, "approvals policy", True),
]


def get_all_surfaces() -> list[SurfaceClassification]:
    return DEFAULT_VISIBLE_SURFACES + ADVANCED_SURFACES + EXPERT_SURFACES


def get_surface_by_id(surface_id: str) -> SurfaceClassification | None:
    for s in get_all_surfaces():
        if s.surface_id == surface_id:
            return s
    return None


def surfaces_hidden_by_default() -> list[SurfaceClassification]:
    return [s for s in get_all_surfaces() if s.hidden_by_default]


def default_visible_surface_ids() -> list[str]:
    return [s.surface_id for s in DEFAULT_VISIBLE_SURFACES]
