"""M52H.1: First-30s hero, role previews, memory narrative, next-step card."""

from __future__ import annotations

from workflow_dataset.investor_mission_control.narrative_m52h1 import (
    build_memory_story,
    build_role_switch_previews,
    hero_headline,
    next_step_after_first_value,
    investor_flow_lines,
)
from workflow_dataset.investor_mission_control.models import (
    MissionControlInvestorHome,
    Hero30Surface,
    FirstValueSurface,
    NextStepCard,
    RoleSwitchPreviewState,
    RolePreviewCard,
    MemoryBootstrapSurface,
    ReadinessStateSnapshot,
    RoleStateSurface,
    ReadyToAssistSurface,
    TrustPostureSurface,
    ActivityTimelineState,
    MissionControlSidePanelState,
)
from workflow_dataset.investor_mission_control.render import (
    format_investor_mission_control_home,
    format_first_30_only,
)


def test_build_memory_story_with_themes() -> None:
    intro, lines = build_memory_story(3, 2, [], ["Planning", "Ops"], [], True)
    assert "3" in intro and "2" in intro
    assert any("Planning" in L for L in lines)


def test_build_role_switch_three() -> None:
    prev = build_role_switch_previews("founder_operator_demo")
    assert len(prev) == 3
    active = [x for x in prev if x["is_active"]]
    assert len(active) == 1
    assert active[0]["preset_id"] == "founder_operator_demo"


def test_next_step_after_workspace() -> None:
    lbl, cmd = next_step_after_first_value("workflow-dataset workspace home")
    assert "ready-state" in cmd


def test_hero_headline_ready_vs_not() -> None:
    assert "live" in hero_headline(True).lower()
    assert "almost" in hero_headline(False).lower()


def test_investor_flow_lines() -> None:
    assert len(investor_flow_lines(True)) >= 3


def test_format_home_m52h1_has_first_look() -> None:
    home = MissionControlInvestorHome(
        hero_30=Hero30Surface(
            eyebrow="LOCAL",
            headline="Your shell is live",
            subline="Acting as: Founder.",
            trust_chip="Simulate-first",
        ),
        first_value=FirstValueSurface(
            headline="Open home",
            why_this_matters="x",
            command="workflow-dataset workspace home",
            subcopy_tight="Calm command center.",
            next_step_label="Then",
            next_step_command="demo onboarding ready-state",
        ),
        next_step_card=NextStepCard(label="Then", command="demo onboarding ready-state"),
        role_switch_previews=RoleSwitchPreviewState(
            cards=[
                RolePreviewCard(preset_id="a", label="L", hook="h", switch_command="c", is_active=True)
            ]
        ),
        memory=MemoryBootstrapSurface(
            narrative_intro="We read samples.",
            insight_lines=["Theme: x."],
            bounded_note="Bounded.",
        ),
        readiness=ReadinessStateSnapshot(capability="full", headline="OK"),
        role=RoleStateSurface(active_role_label="Founder"),
        ready_surface=ReadyToAssistSurface(ready=True, status_headline="Ready"),
        trust=TrustPostureSurface(headline="Control", body="Simulate"),
        timeline=ActivityTimelineState(),
        side_panel=MissionControlSidePanelState(),
        narrative_flow_steps=["1. x"],
    )
    text = format_investor_mission_control_home(home)
    assert "FIRST LOOK" in text
    assert "YOUR NEXT MOVE" in text
    assert "THEN" in text
    assert "Other roles" in text
    assert "What it learned" in text


def test_format_first_30_only() -> None:
    home = MissionControlInvestorHome(
        hero_30=Hero30Surface(headline="H", trust_chip="T"),
        first_value=FirstValueSurface(headline="F", command="cmd"),
        next_step_card=NextStepCard(command="next"),
    )
    t = format_first_30_only(home)
    assert "H" in t and "cmd" in t and "next" in t


def test_build_populates_m52h1_fields(tmp_path) -> None:
    from workflow_dataset.investor_mission_control.build import build_mission_control_investor_home

    h = build_mission_control_investor_home(tmp_path)
    assert h.hero_30.headline
    assert len(h.role_switch_previews.cards) >= 1
    assert h.next_step_card.command
    assert h.memory.narrative_intro
    d = h.to_dict()
    assert "hero_30" in d and "narrative_flow_steps" in d
