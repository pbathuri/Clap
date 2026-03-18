"""
M37A–M37D: Default experience model — default-visible vs advanced vs expert surfaces,
default workday mode set, first-user profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Surface classification
SURFACE_DEFAULT_VISIBLE = "default_visible"
SURFACE_ADVANCED = "advanced"
SURFACE_EXPERT = "expert"

# User-facing mode labels (simplified)
USER_MODE_START = "start"
USER_MODE_FOCUS = "focus"
USER_MODE_REVIEW = "review"
USER_MODE_OPERATOR = "operator"
USER_MODE_WRAP_UP = "wrap_up"
USER_MODE_RESUME = "resume"

DEFAULT_USER_MODES = (
    USER_MODE_START,
    USER_MODE_FOCUS,
    USER_MODE_REVIEW,
    USER_MODE_OPERATOR,
    USER_MODE_WRAP_UP,
    USER_MODE_RESUME,
)


@dataclass
class SurfaceClassification:
    """Classification of a surface: default_visible, advanced, or expert."""
    surface_id: str = ""
    label: str = ""
    classification: str = SURFACE_ADVANCED  # default_visible | advanced | expert
    command_hint: str = ""
    hidden_by_default: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "label": self.label,
            "classification": self.classification,
            "command_hint": self.command_hint,
            "hidden_by_default": self.hidden_by_default,
        }


@dataclass
class DefaultWorkdayModeSet:
    """User-facing mode: label and mapped internal states."""
    mode_id: str = ""
    label: str = ""
    internal_states: list[str] = field(default_factory=list)  # workday state machine values
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "label": self.label,
            "internal_states": list(self.internal_states),
            "description": self.description,
        }


@dataclass
class DefaultExperienceProfile:
    """Default experience profile: first_user, calm_default, full (no narrowing)."""
    profile_id: str = ""
    label: str = ""
    description: str = ""
    default_home_format: str = "calm"  # calm | full
    default_entry_command: str = ""
    show_areas_section: bool = False
    max_mission_control_sections: int = 0  # 0 = use full when mission-control run; or limit for a "default" report variant

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "description": self.description,
            "default_home_format": self.default_home_format,
            "default_entry_command": self.default_entry_command,
            "show_areas_section": self.show_areas_section,
            "max_mission_control_sections": self.max_mission_control_sections,
        }


# M37D.1: Progressive disclosure tiers
TIER_DEFAULT = "default"
TIER_ADVANCED = "advanced"
TIER_EXPERT = "expert"


@dataclass
class DisclosureStep:
    """One step on the progressive disclosure path: from_tier -> to_tier, label, command."""
    from_tier: str = ""
    to_tier: str = ""
    label: str = ""
    command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_tier": self.from_tier,
            "to_tier": self.to_tier,
            "label": self.label,
            "command": self.command,
        }


@dataclass
class OnboardingDefaults:
    """M37D.1: Safer first-user defaults — recommended first command, surfaces to avoid suggesting first."""
    recommended_first_command: str = "workflow-dataset workspace home --profile calm_default"
    avoid_expert_surfaces_until_explicit: bool = True
    safe_first_surface_ids: list[str] = field(default_factory=list)  # default_visible only for first user
    first_step_label: str = "Start here"

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_first_command": self.recommended_first_command,
            "avoid_expert_surfaces_until_explicit": self.avoid_expert_surfaces_until_explicit,
            "safe_first_surface_ids": list(self.safe_first_surface_ids),
            "first_step_label": self.first_step_label,
        }
