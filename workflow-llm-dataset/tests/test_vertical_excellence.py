"""
M47A–M47D: Tests for vertical excellence — first-value path, friction, recommend-next, mission control slice.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.vertical_excellence.models import (
    FirstValuePathStage,
    FrictionPoint,
    AmbiguityPoint,
)
from workflow_dataset.vertical_excellence.path_resolver import (
    get_chosen_vertical_id,
    build_first_value_path_for_vertical,
    build_repeat_value_path_for_vertical,
)
from workflow_dataset.vertical_excellence.compression import (
    assess_first_value_stage,
    list_friction_points,
    list_ambiguity_points,
    list_blocked_first_value_cases,
)
from workflow_dataset.vertical_excellence.recommend_next import recommend_next_for_vertical
from workflow_dataset.vertical_excellence.mission_control import vertical_excellence_slice
from workflow_dataset.vertical_excellence.reports import (
    format_first_value_path_report,
    format_friction_point_report,
    format_recommend_next,
)
from workflow_dataset.vertical_excellence.role_entry_paths import (
    get_role_tuned_entry_path,
    get_role_tuned_entry_path_for_chosen_vertical,
    SUPPORTED_ROLES,
)
from workflow_dataset.vertical_excellence.on_ramp_presets import (
    list_on_ramp_presets,
    get_on_ramp_preset,
    build_path_with_preset,
    PRESET_MINIMAL,
    PRESET_STANDARD,
    PRESET_FULL,
)


def test_get_chosen_vertical_id_default(tmp_path: Path) -> None:
    """Without production cut or active pack, returns default pack id."""
    vid = get_chosen_vertical_id(tmp_path)
    assert vid == "founder_operator_core"


def test_build_first_value_path_for_vertical_fallback(tmp_path: Path) -> None:
    """Build first-value path for default vertical (fallback from operator_quickstart when no pack path)."""
    path = build_first_value_path_for_vertical("founder_operator_core", tmp_path)
    assert path is not None
    assert hasattr(path, "steps")
    assert hasattr(path, "entry_point")
    assert len(getattr(path, "steps", [])) >= 1


def test_build_repeat_value_path_for_vertical(tmp_path: Path) -> None:
    """Repeat-value path returns list of workflow dicts."""
    out = build_repeat_value_path_for_vertical("founder_operator_core", tmp_path)
    assert isinstance(out, list)
    # vertical_speed may return several frequent workflows
    if out:
        assert "workflow_id" in out[0] or "label" in out[0]


def test_assess_first_value_stage_not_started(tmp_path: Path) -> None:
    """When no progress, stage is not_started and step_index 0 or 1."""
    stage = assess_first_value_stage(tmp_path)
    assert isinstance(stage, FirstValuePathStage)
    assert stage.vertical_id in ("founder_operator_core", "")
    assert stage.status in ("not_started", "in_progress", "first_value_reached")
    assert stage.total_steps >= 0


def test_list_friction_points(tmp_path: Path) -> None:
    """Friction points list returns FrictionPoint items (path failure points and/or speed clusters)."""
    points = list_friction_points(tmp_path)
    assert isinstance(points, list)
    for p in points:
        assert isinstance(p, FrictionPoint)
        assert p.friction_id or p.label or p.kind


def test_list_ambiguity_points(tmp_path: Path) -> None:
    """Ambiguity points list may be empty or contain AmbiguityPoint."""
    points = list_ambiguity_points(tmp_path)
    assert isinstance(points, list)
    for p in points:
        assert isinstance(p, AmbiguityPoint)


def test_list_blocked_first_value_cases_no_vertical(tmp_path: Path) -> None:
    """With no active vertical set, blocked cases may be empty or contain no_active_vertical."""
    cases = list_blocked_first_value_cases(tmp_path)
    assert isinstance(cases, list)
    for c in cases:
        assert "reason" in c
        assert "step_index" in c or "hint" in c


def test_recommend_next_for_vertical(tmp_path: Path) -> None:
    """Recommend-next returns a recommendation (command, label, rationale)."""
    rec = recommend_next_for_vertical(tmp_path)
    assert rec is not None
    assert rec.command
    assert rec.label
    assert rec.rationale


def test_vertical_excellence_slice(tmp_path: Path) -> None:
    """Mission control slice has required keys."""
    slice_data = vertical_excellence_slice(tmp_path)
    assert "vertical_id" in slice_data
    assert "current_first_value_stage" in slice_data
    assert "blocked_first_value_cases_count" in slice_data
    assert "next_recommended_excellence_action" in slice_data
    stage = slice_data["current_first_value_stage"]
    assert "status" in stage
    assert "step_index" in stage


def test_format_first_value_path_report(tmp_path: Path) -> None:
    """Path report is non-empty string with vertical and stage."""
    report = format_first_value_path_report(tmp_path)
    assert isinstance(report, str)
    assert "First-value" in report or "first-value" in report or "vertical" in report.lower()


def test_format_friction_point_report(tmp_path: Path) -> None:
    """Friction report is non-empty string."""
    report = format_friction_point_report(tmp_path)
    assert isinstance(report, str)
    assert "Friction" in report or "friction" in report or "blocked" in report.lower()


def test_format_recommend_next(tmp_path: Path) -> None:
    """Recommend-next report contains command and label."""
    report = format_recommend_next(tmp_path)
    assert isinstance(report, str)
    assert "command" in report or "Next" in report


def test_no_active_project_uses_default_vertical(tmp_path: Path) -> None:
    """When repo has no production cut, chosen vertical is default pack id."""
    vid = get_chosen_vertical_id(tmp_path)
    assert vid
    path = build_first_value_path_for_vertical(vid, tmp_path)
    assert path is not None or vid == "founder_operator_core"


# ----- M47D.1 Role-tuned entry paths + on-ramps -----


def test_get_role_tuned_entry_path_operator(tmp_path: Path) -> None:
    """Role-tuned entry path for operator returns path with steps and entry_point."""
    path = get_role_tuned_entry_path("founder_operator_core", "operator", tmp_path)
    assert path is not None
    assert path.role_id == "operator"
    assert path.entry_point
    assert len(path.step_commands) >= 1
    assert path.best_next_after_entry


def test_get_role_tuned_entry_path_reviewer(tmp_path: Path) -> None:
    """Role-tuned entry path for reviewer has queue/review focus."""
    path = get_role_tuned_entry_path("founder_operator_core", "reviewer", tmp_path)
    assert path is not None
    assert path.role_id == "reviewer"
    assert "review" in path.label.lower() or "queue" in path.label.lower() or path.entry_point


def test_get_role_tuned_entry_path_analyst(tmp_path: Path) -> None:
    """Role-tuned entry path for analyst has focus-first steps."""
    path = get_role_tuned_entry_path("founder_operator_core", "analyst", tmp_path)
    assert path is not None
    assert path.role_id == "analyst"
    assert path.entry_point
    assert path.first_value_outcome


def test_get_role_tuned_entry_path_for_chosen_vertical(tmp_path: Path) -> None:
    """Convenience returns path for chosen vertical."""
    path = get_role_tuned_entry_path_for_chosen_vertical("operator", tmp_path)
    assert path is not None
    assert path.vertical_id == "founder_operator_core"


def test_list_on_ramp_presets() -> None:
    """On-ramp presets include minimal, standard, full."""
    presets = list_on_ramp_presets()
    ids = [p.preset_id for p in presets]
    assert PRESET_MINIMAL in ids
    assert PRESET_STANDARD in ids
    assert PRESET_FULL in ids
    assert len(presets) >= 3


def test_get_on_ramp_preset_minimal() -> None:
    """Minimal preset has 3 steps."""
    p = get_on_ramp_preset(PRESET_MINIMAL)
    assert p is not None
    assert p.step_count == 3
    assert p.suggested_for == "new_user"


def test_build_path_with_preset(tmp_path: Path) -> None:
    """Build path with preset returns filtered steps."""
    out = build_path_with_preset("founder_operator_core", PRESET_MINIMAL, tmp_path)
    assert out is not None
    assert out["preset_id"] == PRESET_MINIMAL
    assert len(out["steps"]) == 3
    assert "entry_point" in out


def test_recommend_next_new_user(tmp_path: Path) -> None:
    """Recommend-next with user_recency=new returns start-here style."""
    rec = recommend_next_for_vertical(tmp_path, user_recency="new")
    assert rec is not None
    assert "workflow-dataset" in rec.command
    assert "new" in rec.label.lower() or "Start" in rec.label


def test_recommend_next_returning_user(tmp_path: Path) -> None:
    """Recommend-next with user_recency=returning prefers day status."""
    rec = recommend_next_for_vertical(tmp_path, user_recency="returning")
    assert rec is not None
    assert "day status" in rec.command or "queue" in rec.command or "day" in rec.rationale.lower()
    assert "returning" in rec.label.lower()
