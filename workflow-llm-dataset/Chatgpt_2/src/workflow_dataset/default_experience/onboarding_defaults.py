"""
M37D.1: Safer first-user defaults — recommended first command, safe surfaces, avoid expert until explicit.
"""

from __future__ import annotations

from workflow_dataset.default_experience.models import OnboardingDefaults
from workflow_dataset.default_experience.surfaces import (
    default_visible_surface_ids,
    get_surface_by_id,
    get_all_surfaces,
)
from workflow_dataset.default_experience.models import SURFACE_EXPERT


# Single source of truth for first-user safe defaults (M37D.1)
ONBOARDING_DEFAULTS = OnboardingDefaults(
    recommended_first_command="workflow-dataset workspace home --profile calm_default",
    avoid_expert_surfaces_until_explicit=True,
    safe_first_surface_ids=[],  # filled from default_visible at runtime
    first_step_label="Start here",
)

# Next command to suggest after first (calm home) — keeps user in default tier
RECOMMENDED_NEXT_AFTER_HOME = "workflow-dataset day status"


def get_onboarding_defaults() -> OnboardingDefaults:
    """Return onboarding defaults; safe_first_surface_ids populated from default_visible surfaces."""
    ids = default_visible_surface_ids()
    return OnboardingDefaults(
        recommended_first_command=ONBOARDING_DEFAULTS.recommended_first_command,
        avoid_expert_surfaces_until_explicit=ONBOARDING_DEFAULTS.avoid_expert_surfaces_until_explicit,
        safe_first_surface_ids=list(ids),
        first_step_label=ONBOARDING_DEFAULTS.first_step_label,
    )


def recommended_first_command() -> str:
    """Recommended first command for a new user."""
    return get_onboarding_defaults().recommended_first_command


def recommended_next_after_home() -> str:
    """M37D.1: Recommended next command after viewing calm home (stays in default tier)."""
    return RECOMMENDED_NEXT_AFTER_HOME


def get_safe_first_surfaces() -> list[str]:
    """Surface ids safe to suggest first (default_visible only; no expert)."""
    return list(get_onboarding_defaults().safe_first_surface_ids)


def is_safe_for_first_user(surface_id: str) -> bool:
    """M37D.1: True if surface is safe to suggest to a first-time user (default-visible, not expert)."""
    if not surface_id or not get_onboarding_defaults().avoid_expert_surfaces_until_explicit:
        return False
    safe_ids = set(get_safe_first_surfaces())
    if surface_id in safe_ids:
        return True
    s = get_surface_by_id(surface_id)
    if s is None:
        return False
    return s.classification != SURFACE_EXPERT and not s.hidden_by_default
