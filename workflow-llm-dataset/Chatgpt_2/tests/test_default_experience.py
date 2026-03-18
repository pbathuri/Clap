"""
M37A–M37D: Tests for default experience — surface classification, simplified modes, profiles, calm home, store.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.default_experience.models import (
    SURFACE_ADVANCED,
    SURFACE_DEFAULT_VISIBLE,
    SURFACE_EXPERT,
    DefaultExperienceProfile,
    DefaultWorkdayModeSet,
    USER_MODE_FOCUS,
    USER_MODE_START,
)
from workflow_dataset.default_experience.surfaces import (
    DEFAULT_VISIBLE_SURFACES,
    ADVANCED_SURFACES,
    EXPERT_SURFACES,
    get_all_surfaces,
    get_surface_by_id,
    surfaces_hidden_by_default,
    default_visible_surface_ids,
)
from workflow_dataset.default_experience.modes import (
    SIMPLIFIED_MODE_SET,
    get_simplified_mode_mapping,
    internal_state_to_user_mode,
)
from workflow_dataset.default_experience.profiles import (
    get_profile,
    list_profile_ids,
    PROFILE_CALM_DEFAULT,
    PROFILE_FIRST_USER,
    PROFILE_FULL,
)
from workflow_dataset.default_experience.store import (
    get_active_default_profile_id,
    set_active_default_profile_id,
    DEFAULT_PROFILE_ID,
)
from workflow_dataset.workday.models import WorkdayState


def test_surface_classification_default_visible() -> None:
    """Default-visible surfaces are classified and not hidden by default."""
    default_ids = default_visible_surface_ids()
    assert "workspace_home" in default_ids or "day_status" in default_ids
    for s in DEFAULT_VISIBLE_SURFACES:
        assert s.classification == SURFACE_DEFAULT_VISIBLE
        assert s.hidden_by_default is False


def test_surface_classification_advanced_expert() -> None:
    """Advanced and expert surfaces exist and are hidden by default."""
    assert len(ADVANCED_SURFACES) >= 1
    assert len(EXPERT_SURFACES) >= 1
    for s in ADVANCED_SURFACES + EXPERT_SURFACES:
        assert s.classification in (SURFACE_ADVANCED, SURFACE_EXPERT)
        assert s.hidden_by_default is True


def test_get_surface_by_id() -> None:
    """get_surface_by_id returns surface or None."""
    assert get_surface_by_id("mission_control") is not None
    assert get_surface_by_id("nonexistent") is None


def test_surfaces_hidden_by_default() -> None:
    """Surfaces hidden by default are exactly advanced + expert."""
    hidden = surfaces_hidden_by_default()
    default_visible = {s.surface_id for s in DEFAULT_VISIBLE_SURFACES}
    for s in hidden:
        assert s.surface_id not in default_visible


def test_simplified_mode_mapping() -> None:
    """Six user-facing modes with internal state mapping."""
    mapping = get_simplified_mode_mapping()
    assert len(mapping) == 6
    mode_ids = {m["mode_id"] for m in mapping}
    assert USER_MODE_START in mode_ids
    assert USER_MODE_FOCUS in mode_ids
    assert "review" in mode_ids
    assert "operator" in mode_ids
    assert "wrap_up" in mode_ids
    assert "resume" in mode_ids


def test_internal_state_to_user_mode() -> None:
    """Internal workday states map to user-facing modes."""
    assert internal_state_to_user_mode(WorkdayState.NOT_STARTED.value) == USER_MODE_START
    assert internal_state_to_user_mode(WorkdayState.STARTUP.value) == USER_MODE_START
    assert internal_state_to_user_mode(WorkdayState.FOCUS_WORK.value) == USER_MODE_FOCUS
    assert internal_state_to_user_mode(WorkdayState.REVIEW_AND_APPROVALS.value) == "review"
    assert internal_state_to_user_mode(WorkdayState.SHUTDOWN.value) == "resume"
    assert internal_state_to_user_mode(WorkdayState.RESUME_PENDING.value) == "resume"


def test_profiles_list_and_get() -> None:
    """Profiles first_user, calm_default, full exist."""
    ids = list_profile_ids()
    assert PROFILE_FIRST_USER in ids
    assert PROFILE_CALM_DEFAULT in ids
    assert PROFILE_FULL in ids
    p = get_profile(PROFILE_CALM_DEFAULT)
    assert p is not None
    assert p.profile_id == PROFILE_CALM_DEFAULT
    assert p.default_home_format == "calm"
    full_p = get_profile(PROFILE_FULL)
    assert full_p is not None
    assert full_p.default_home_format == "full"


def test_store_get_set_profile(tmp_path: Path) -> None:
    """Active profile can be read and written."""
    default_before = get_active_default_profile_id(tmp_path)
    assert default_before == DEFAULT_PROFILE_ID
    set_active_default_profile_id(PROFILE_FULL, tmp_path)
    assert get_active_default_profile_id(tmp_path) == PROFILE_FULL
    set_active_default_profile_id(PROFILE_CALM_DEFAULT, tmp_path)
    assert get_active_default_profile_id(tmp_path) == PROFILE_CALM_DEFAULT


def test_calm_home_format() -> None:
    """Calm default home returns narrowed sections (focus, next, approvals, carry-forward, project, automation/health)."""
    from workflow_dataset.default_experience.calm_home import format_calm_default_home
    from workflow_dataset.workspace.models import WorkspaceHomeSnapshot, ActiveWorkContext
    snapshot = WorkspaceHomeSnapshot(
        context=ActiveWorkContext(
            active_project_id="proj1",
            active_project_title="Test Project",
            next_recommended_action="review",
            next_recommended_detail="Check inbox",
        ),
        approval_queue_summary="2 pending",
        trust_health_summary="OK",
    )
    out = format_calm_default_home(snapshot=snapshot)
    assert "Workspace Home (calm default)" in out
    assert "[Current focus]" in out
    assert "[Next best action]" in out
    assert "[Urgent approvals" in out
    assert "[Carry-forward" in out
    assert "[Most relevant project]" in out
    assert "[Automation / health]" in out
    assert "proj1" in out or "Test Project" in out
    assert "workflow-dataset workspace home" in out or "day status" in out


def test_preserved_advanced_access() -> None:
    """Advanced and expert surfaces remain listable (preserved access)."""
    all_s = get_all_surfaces()
    advanced_expert = [s for s in all_s if s.classification in (SURFACE_ADVANCED, SURFACE_EXPERT)]
    assert len(advanced_expert) >= len(ADVANCED_SURFACES) + len(EXPERT_SURFACES)
    mission = get_surface_by_id("mission_control")
    assert mission is not None
    assert "mission-control" in (mission.command_hint or "")


# ----- M37D.1: Onboarding defaults + progressive disclosure + role calm -----


def test_onboarding_defaults() -> None:
    """Onboarding defaults provide recommended first command and safe surfaces."""
    from workflow_dataset.default_experience.onboarding_defaults import (
        get_onboarding_defaults,
        recommended_first_command,
        get_safe_first_surfaces,
    )
    d = get_onboarding_defaults()
    assert "calm_default" in d.recommended_first_command or "workspace home" in d.recommended_first_command
    assert d.avoid_expert_surfaces_until_explicit is True
    assert recommended_first_command() == d.recommended_first_command
    safe = get_safe_first_surfaces()
    assert isinstance(safe, list)
    # Safe first surfaces = default_visible ids (no expert)
    for sid in safe:
        assert sid in default_visible_surface_ids()


def test_onboarding_safe_surface_and_next_after_home() -> None:
    """M37D.1: is_safe_for_first_user and recommended_next_after_home."""
    from workflow_dataset.default_experience.onboarding_defaults import (
        is_safe_for_first_user,
        recommended_next_after_home,
    )
    assert "day status" in recommended_next_after_home()
    assert is_safe_for_first_user("workspace_home") or is_safe_for_first_user("day_status")
    assert is_safe_for_first_user("trust_cockpit") is False
    assert is_safe_for_first_user("nonexistent") is False


def test_progressive_disclosure_paths() -> None:
    """Progressive disclosure path: default -> advanced -> expert with show-me-more commands."""
    from workflow_dataset.default_experience.disclosure_paths import (
        get_progressive_disclosure_paths,
        get_show_more_commands,
        format_show_more_footer,
    )
    from workflow_dataset.default_experience.models import TIER_DEFAULT, TIER_ADVANCED, TIER_EXPERT
    paths = get_progressive_disclosure_paths()
    assert len(paths) >= 1
    default_steps = get_show_more_commands(TIER_DEFAULT)
    assert len(default_steps) >= 1
    assert any(s.to_tier == TIER_ADVANCED for s in default_steps)
    footer = format_show_more_footer()
    assert "[Show me more]" in footer[0]
    assert "defaults paths" in "\n".join(footer).lower()


def test_disclosure_path_by_tier() -> None:
    """M37D.1: Disclosure steps grouped by from_tier (default, advanced, expert)."""
    from workflow_dataset.default_experience.disclosure_paths import get_disclosure_path_by_tier
    by_tier = get_disclosure_path_by_tier()
    assert "default" in by_tier
    assert "advanced" in by_tier
    assert "expert" in by_tier
    assert len(by_tier["default"]) >= 1
    assert len(by_tier["advanced"]) >= 1
    # Each step has label and command
    for steps in by_tier.values():
        for s in steps:
            assert "label" in s and "command" in s


def test_role_calm_profiles() -> None:
    """Role-specific calm profiles exist and map from workday preset (M37D.1)."""
    from workflow_dataset.default_experience.profiles import (
        get_profile,
        list_role_calm_profile_ids,
        get_calm_profile_for_workday_role,
        PROFILE_FOUNDER_CALM,
        PROFILE_ANALYST_CALM,
    )
    role_ids = list_role_calm_profile_ids()
    assert PROFILE_FOUNDER_CALM in role_ids
    assert PROFILE_ANALYST_CALM in role_ids
    assert len(role_ids) == 5
    assert get_calm_profile_for_workday_role("founder_operator") == PROFILE_FOUNDER_CALM
    assert get_calm_profile_for_workday_role("analyst") == PROFILE_ANALYST_CALM
    assert get_calm_profile_for_workday_role("unknown") is None
    p = get_profile(PROFILE_FOUNDER_CALM)
    assert p is not None
    assert p.default_home_format == "calm"
    assert "founder" in p.label.lower() or "operator" in p.label.lower()


def test_calm_home_includes_show_more() -> None:
    """Calm home output includes Show me more section (M37D.1)."""
    from workflow_dataset.default_experience.calm_home import format_calm_default_home
    from workflow_dataset.workspace.models import WorkspaceHomeSnapshot, ActiveWorkContext
    snapshot = WorkspaceHomeSnapshot(context=ActiveWorkContext(), trust_health_summary="OK")
    out = format_calm_default_home(snapshot=snapshot)
    assert "[Show me more]" in out
    assert "defaults paths" in out.lower()
