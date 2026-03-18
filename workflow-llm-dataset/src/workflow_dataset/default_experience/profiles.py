"""
M37A–M37D / M37D.1: Default experience profiles — first_user, calm_default, full; role-specific calm (M37D.1).
"""

from __future__ import annotations

from workflow_dataset.default_experience.models import DefaultExperienceProfile

PROFILE_FIRST_USER = "first_user"
PROFILE_CALM_DEFAULT = "calm_default"
PROFILE_FULL = "full"

# M37D.1: Role-specific calm profiles (map 1:1 to workday presets; remain calm)
PROFILE_FOUNDER_CALM = "founder_calm"
PROFILE_ANALYST_CALM = "analyst_calm"
PROFILE_DEVELOPER_CALM = "developer_calm"
PROFILE_DOCUMENT_CALM = "document_heavy_calm"
PROFILE_SUPERVISION_CALM = "supervision_heavy_calm"

ROLE_CALM_PROFILE_IDS: list[str] = [
    PROFILE_FOUNDER_CALM,
    PROFILE_ANALYST_CALM,
    PROFILE_DEVELOPER_CALM,
    PROFILE_DOCUMENT_CALM,
    PROFILE_SUPERVISION_CALM,
]

# Workday preset_id -> default experience profile_id (role calm)
WORKDAY_PRESET_TO_CALM_PROFILE: dict[str, str] = {
    "founder_operator": PROFILE_FOUNDER_CALM,
    "analyst": PROFILE_ANALYST_CALM,
    "developer": PROFILE_DEVELOPER_CALM,
    "document_heavy": PROFILE_DOCUMENT_CALM,
    "supervision_heavy": PROFILE_SUPERVISION_CALM,
}

FIRST_USER_PROFILE = DefaultExperienceProfile(
    profile_id=PROFILE_FIRST_USER,
    label="First user",
    description="Narrowest default: calm home, single entry, minimal sections.",
    default_home_format="calm",
    default_entry_command="workflow-dataset workspace home --profile calm_default",
    show_areas_section=False,
    max_mission_control_sections=0,
)

CALM_DEFAULT_PROFILE = DefaultExperienceProfile(
    profile_id=PROFILE_CALM_DEFAULT,
    label="Calm default",
    description="Daily default: calm home, six modes, advanced surfaces hidden by default.",
    default_home_format="calm",
    default_entry_command="workflow-dataset workspace home --profile calm_default",
    show_areas_section=False,
    max_mission_control_sections=0,
)

FULL_PROFILE = DefaultExperienceProfile(
    profile_id=PROFILE_FULL,
    label="Full",
    description="No narrowing: full workspace home, all areas, full mission control.",
    default_home_format="full",
    default_entry_command="workflow-dataset workspace home",
    show_areas_section=True,
    max_mission_control_sections=0,
)

# Role calm profiles: calm home, no areas section; entry command stays calm (M37D.1)
FOUNDER_CALM_PROFILE = DefaultExperienceProfile(
    profile_id=PROFILE_FOUNDER_CALM,
    label="Founder / Operator (calm)",
    description="Calm default for founder/operator: portfolio and approvals first; operator mode when needed.",
    default_home_format="calm",
    default_entry_command="workflow-dataset workspace home --profile calm_default",
    show_areas_section=False,
    max_mission_control_sections=0,
)
ANALYST_CALM_PROFILE = DefaultExperienceProfile(
    profile_id=PROFILE_ANALYST_CALM,
    label="Analyst (calm)",
    description="Calm default for analyst: focus work first; review when queue has items.",
    default_home_format="calm",
    default_entry_command="workflow-dataset workspace home --profile calm_default",
    show_areas_section=False,
    max_mission_control_sections=0,
)
DEVELOPER_CALM_PROFILE = DefaultExperienceProfile(
    profile_id=PROFILE_DEVELOPER_CALM,
    label="Developer (calm)",
    description="Calm default for developer: focus or operator mode; review before wrap.",
    default_home_format="calm",
    default_entry_command="workflow-dataset workspace home --profile calm_default",
    show_areas_section=False,
    max_mission_control_sections=0,
)
DOCUMENT_CALM_PROFILE = DefaultExperienceProfile(
    profile_id=PROFILE_DOCUMENT_CALM,
    label="Document-heavy (calm)",
    description="Calm default for document-heavy: documents and artifacts first; review queue regularly.",
    default_home_format="calm",
    default_entry_command="workflow-dataset workspace home --profile calm_default",
    show_areas_section=False,
    max_mission_control_sections=0,
)
SUPERVISION_CALM_PROFILE = DefaultExperienceProfile(
    profile_id=PROFILE_SUPERVISION_CALM,
    label="Supervision-heavy (calm)",
    description="Calm default for supervision-heavy: clear approvals and review first; then focus or operator.",
    default_home_format="calm",
    default_entry_command="workflow-dataset workspace home --profile calm_default",
    show_areas_section=False,
    max_mission_control_sections=0,
)

_PROFILES: dict[str, DefaultExperienceProfile] = {
    PROFILE_FIRST_USER: FIRST_USER_PROFILE,
    PROFILE_CALM_DEFAULT: CALM_DEFAULT_PROFILE,
    PROFILE_FULL: FULL_PROFILE,
    PROFILE_FOUNDER_CALM: FOUNDER_CALM_PROFILE,
    PROFILE_ANALYST_CALM: ANALYST_CALM_PROFILE,
    PROFILE_DEVELOPER_CALM: DEVELOPER_CALM_PROFILE,
    PROFILE_DOCUMENT_CALM: DOCUMENT_CALM_PROFILE,
    PROFILE_SUPERVISION_CALM: SUPERVISION_CALM_PROFILE,
}


def get_profile(profile_id: str) -> DefaultExperienceProfile | None:
    return _PROFILES.get(profile_id.strip())


def list_profile_ids() -> list[str]:
    return list(_PROFILES.keys())


def list_role_calm_profile_ids() -> list[str]:
    """M37D.1: Role-specific calm profile ids (founder_calm, analyst_calm, etc.)."""
    return list(ROLE_CALM_PROFILE_IDS)


def get_calm_profile_for_workday_role(workday_preset_id: str) -> str | None:
    """M37D.1: Map workday preset id to default experience profile id (role calm). Returns None if unknown."""
    return WORKDAY_PRESET_TO_CALM_PROFILE.get((workday_preset_id or "").strip())
