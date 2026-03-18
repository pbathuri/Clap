"""
M36D.1: Tests for workday presets by role (founder_operator, analyst, developer, document_heavy, supervision_heavy).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.workday.models import WorkdayState
from workflow_dataset.workday.presets import (
    WorkdayPreset,
    BUILTIN_WORKDAY_PRESETS,
    get_workday_preset,
    list_workday_presets,
    PRESET_FOUNDER_OPERATOR,
    PRESET_SUPERVISION_HEAVY,
    EMPHASIS_HIGH,
    OPERATOR_MODE_PREFERRED,
)
from workflow_dataset.workday.store import (
    get_active_workday_preset_id,
    set_active_workday_preset_id,
    load_workday_state,
    save_workday_state,
)
from workflow_dataset.workday.surface import build_daily_operating_surface


def test_list_workday_presets() -> None:
    """All five role presets exist."""
    presets = list_workday_presets()
    assert len(presets) >= 5
    ids = {p.preset_id for p in presets}
    assert "founder_operator" in ids
    assert "analyst" in ids
    assert "developer" in ids
    assert "document_heavy" in ids
    assert "supervision_heavy" in ids


def test_get_workday_preset() -> None:
    """get_workday_preset returns preset by id."""
    p = get_workday_preset(PRESET_FOUNDER_OPERATOR)
    assert p is not None
    assert p.preset_id == PRESET_FOUNDER_OPERATOR
    assert p.default_transition_after_startup == WorkdayState.REVIEW_AND_APPROVALS.value
    assert p.queue_review_emphasis == EMPHASIS_HIGH
    assert p.operator_mode_usage == OPERATOR_MODE_PREFERRED
    assert get_workday_preset("nonexistent") is None


def test_founder_operator_preset_defaults() -> None:
    """Founder/operator preset: review first, high queue emphasis, preferred operator mode."""
    p = get_workday_preset(PRESET_FOUNDER_OPERATOR)
    assert p is not None
    assert WorkdayState.REVIEW_AND_APPROVALS.value in p.default_day_states
    assert p.default_transition_after_startup == WorkdayState.REVIEW_AND_APPROVALS.value
    assert p.role_operating_hint


def test_supervision_heavy_preset_defaults() -> None:
    """Supervision-heavy: review first, high emphasis, preferred operator mode."""
    p = get_workday_preset(PRESET_SUPERVISION_HEAVY)
    assert p is not None
    assert p.default_transition_after_startup == WorkdayState.REVIEW_AND_APPROVALS.value
    assert p.queue_review_emphasis == EMPHASIS_HIGH


def test_active_preset_persistence(tmp_path: Path) -> None:
    """set_active_workday_preset_id persists; get_active_workday_preset_id reads it."""
    assert get_active_workday_preset_id(tmp_path) is None
    set_active_workday_preset_id(PRESET_FOUNDER_OPERATOR, tmp_path)
    assert get_active_workday_preset_id(tmp_path) == PRESET_FOUNDER_OPERATOR


def test_surface_includes_preset_when_set(tmp_path: Path) -> None:
    """When active preset is set, surface includes preset_id and role_operating_hint."""
    from workflow_dataset.workday.models import WorkdayStateRecord
    set_active_workday_preset_id(PRESET_FOUNDER_OPERATOR, tmp_path)
    save_workday_state(
        WorkdayStateRecord(state=WorkdayState.STARTUP.value, day_id="2025-03-16"),
        tmp_path,
    )
    surf = build_daily_operating_surface(tmp_path)
    assert surf.preset_id == PRESET_FOUNDER_OPERATOR
    assert "Portfolio" in surf.role_operating_hint or "approvals" in surf.role_operating_hint.lower()


def test_surface_startup_recommends_preset_transition(tmp_path: Path) -> None:
    """With founder_operator preset and state=startup, recommended transition is review_and_approvals."""
    set_active_workday_preset_id(PRESET_FOUNDER_OPERATOR, tmp_path)
    from workflow_dataset.workday.models import WorkdayStateRecord
    save_workday_state(
        WorkdayStateRecord(state=WorkdayState.STARTUP.value, day_id="2025-03-16"),
        tmp_path,
    )
    surf = build_daily_operating_surface(tmp_path)
    assert surf.current_workday_state == WorkdayState.STARTUP.value
    assert surf.next_recommended_transition == WorkdayState.REVIEW_AND_APPROVALS.value


def test_workday_preset_to_dict() -> None:
    """WorkdayPreset.to_dict is serializable."""
    p = get_workday_preset(PRESET_FOUNDER_OPERATOR)
    assert p is not None
    d = p.to_dict()
    assert d["preset_id"] == p.preset_id
    assert "default_day_states" in d
    assert "quick_actions" in d
    p2 = WorkdayPreset.from_dict(d)
    assert p2.preset_id == p.preset_id
    assert p2.default_transition_after_startup == p.default_transition_after_startup
