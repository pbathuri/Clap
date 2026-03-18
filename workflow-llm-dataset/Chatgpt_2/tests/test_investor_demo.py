"""
M51I–M51L: Investor demo session, narrative, first-value artifact, supervised action.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.investor_demo.models import (
    DemoNarrativeStage,
    STAGE_ORDER,
    PresenterGuidanceNote,
    DemoMissionControlPanel,
    DegradedDemoWarning,
)
from workflow_dataset.investor_demo.narrative import guidance_for_stage, next_stage
from workflow_dataset.investor_demo.session_store import (
    start_demo_session,
    load_demo_session,
    advance_demo_stage,
    session_path,
)
from workflow_dataset.investor_demo.first_value import build_first_value_demo_path
from workflow_dataset.investor_demo.supervised import build_supervised_action_demo
from workflow_dataset.investor_demo.presentation_mc import format_demo_mission_control_text


def test_stage_order_length() -> None:
    assert len(STAGE_ORDER) == 8
    assert STAGE_ORDER[0] == DemoNarrativeStage.STARTUP_READINESS


def test_guidance_for_stage() -> None:
    g = guidance_for_stage(DemoNarrativeStage.STARTUP_READINESS)
    assert g.headline
    assert len(g.talking_points) >= 1
    assert g.caution


def test_next_stage() -> None:
    assert next_stage(DemoNarrativeStage.STARTUP_READINESS.value) == DemoNarrativeStage.ROLE_ONBOARDING.value
    assert next_stage(DemoNarrativeStage.CLOSING_MISSION_CONTROL_SUMMARY.value) is None


def test_start_demo_session(tmp_path: Path) -> None:
    sess = start_demo_session(repo_root=tmp_path, vertical_id="test_vertical", role_demo_pack_id="founder_operator")
    assert sess.session_id
    assert sess.current_stage == DemoNarrativeStage.STARTUP_READINESS.value
    assert sess.vertical_id == "test_vertical"
    assert session_path(tmp_path).exists()


def test_load_and_advance_session(tmp_path: Path) -> None:
    start_demo_session(repo_root=tmp_path, vertical_id="v1")
    s2 = advance_demo_stage(repo_root=tmp_path)
    assert s2 is not None
    assert s2.current_stage == DemoNarrativeStage.ROLE_ONBOARDING.value
    loaded = load_demo_session(tmp_path)
    assert loaded is not None
    assert loaded.current_stage == DemoNarrativeStage.ROLE_ONBOARDING.value


def test_advance_to_completion(tmp_path: Path) -> None:
    start_demo_session(repo_root=tmp_path)
    sess = load_demo_session(tmp_path)
    for _ in range(len(STAGE_ORDER) - 1):
        sess = advance_demo_stage(repo_root=tmp_path)
        assert sess is not None
    assert sess.completion.completed or sess.current_stage == DemoNarrativeStage.CLOSING_MISSION_CONTROL_SUMMARY.value
    sess = advance_demo_stage(repo_root=tmp_path)
    assert sess is not None
    assert sess.completion.completed


def test_build_first_value_demo_path(tmp_path: Path) -> None:
    path = build_first_value_demo_path(tmp_path)
    assert path.artifact_markdown
    assert "# Investor demo" in path.artifact_markdown
    assert path.next_safe_command
    assert path.opportunity_line


def test_build_supervised_action_demo() -> None:
    demo = build_supervised_action_demo()
    assert demo.card_id
    assert demo.preview.get("what_would_happen")
    assert demo.trust_posture == "simulate_only"
    assert "mission-control" in (demo.preview.get("command_hint") or demo.preview.get("what_would_happen", ""))


def test_format_demo_mission_control_text() -> None:
    panel = DemoMissionControlPanel(
        device_readiness_line="ok",
        chosen_role_demo_pack="x",
        memory_bootstrap_summary="m",
        active_project_context="c",
        first_value_opportunity="fv",
        recommended_safe_action="a",
        evidence_system_learned="e",
        supervised_and_safe_posture="s",
        degraded_warnings=[DegradedDemoWarning(warning_id="w1", message="Test degraded", source="t")],
    )
    text = format_demo_mission_control_text(panel)
    assert "Investor demo" in text
    assert "Degraded" in text
    assert "Test degraded" in text
