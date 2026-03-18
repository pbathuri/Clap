"""M52E–M52H: Investor mission-control workspace."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.investor_mission_control.surfaces import (
    humanize_first_value_command,
    vertical_pack_display_name,
    readiness_headline,
    memory_headline,
)
from workflow_dataset.investor_mission_control.models import (
    MissionControlInvestorHome,
    ReadinessStateSnapshot,
    RoleStateSurface,
    MemoryBootstrapSurface,
    ReadyToAssistSurface,
    FirstValueSurface,
    TrustPostureSurface,
    ActivityTimelineState,
    MissionControlSidePanelState,
    Hero30Surface,
    NextStepCard,
    RoleSwitchPreviewState,
    RolePreviewCard,
)
from workflow_dataset.investor_mission_control.render import format_investor_mission_control_home


def test_humanize_workspace_home() -> None:
    h, w, n = humanize_first_value_command("workflow-dataset workspace home --profile calm_default")
    assert "workspace" in h.lower() or "home" in h.lower()
    assert w
    assert n


def test_humanize_progress_board() -> None:
    h, _, _ = humanize_first_value_command("workflow-dataset progress board")
    assert "follow" in h.lower() or "board" in h.lower()


def test_vertical_pack_display() -> None:
    assert "Founder" in vertical_pack_display_name("founder_operator_core")


def test_readiness_headline() -> None:
    assert readiness_headline("full")[1] is True
    assert readiness_headline("blocked")[1] is False


def test_memory_headline() -> None:
    assert "not complete" in memory_headline(False, 0, 0).lower()
    assert "5" in memory_headline(True, 5, 3)


def test_format_home_contains_sections() -> None:
    home = MissionControlInvestorHome(
        hero_30=Hero30Surface(eyebrow="R", headline="H", subline="S", trust_chip="T"),
        first_value=FirstValueSurface(
            headline="Open home",
            command="workflow-dataset workspace home",
            subcopy_tight="Why",
            next_step_label="Then",
            next_step_command="ready-state",
        ),
        next_step_card=NextStepCard(label="Then", command="ready-state"),
        role_switch_previews=RoleSwitchPreviewState(
            cards=[RolePreviewCard(preset_id="p", label="R", hook="h", switch_command="c")]
        ),
        memory=MemoryBootstrapSurface(
            headline="Loaded",
            what_learned_bullets=["Theme: a"],
            narrative_intro="Intro",
            insight_lines=["i"],
            bounded_note="b",
        ),
        readiness=ReadinessStateSnapshot(capability="full", headline="Ready", device_ok_for_demo=True),
        role=RoleStateSurface(active_role_label="Founder", vertical_pack_display="Founder & ops", preset_id="x"),
        ready_surface=ReadyToAssistSurface(ready=True, status_headline="Ready to assist"),
        trust=TrustPostureSurface(headline="Control", body="Simulate first"),
        timeline=ActivityTimelineState(),
        side_panel=MissionControlSidePanelState(inbox_summary="Inbox clear."),
        narrative_flow_steps=["1. a"],
    )
    text = format_investor_mission_control_home(home)
    assert "Founder" in text
    assert "Open home" in text
    assert "FIRST LOOK" in text
    assert "Trust" in text or "trust" in text.lower()


def test_build_mission_control_investor_home_smoke(tmp_path: Path) -> None:
    from workflow_dataset.investor_mission_control.build import build_mission_control_investor_home

    home = build_mission_control_investor_home(tmp_path)
    assert home.generated_at_utc
    assert home.role.preset_id
    assert home.first_value.command
    assert len(home.timeline.items) == 4


def test_timeline_steps_order() -> None:
    from workflow_dataset.investor_mission_control.build import build_mission_control_investor_home

    h = build_mission_control_investor_home()
    ids = [i.step_id for i in h.timeline.items]
    assert ids == ["env", "role", "memory", "assist"]
