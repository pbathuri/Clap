"""
M52E Phase A: Demo state models for investor mission-control home.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReadinessStateSnapshot:
    capability: str = "unknown"
    headline: str = ""
    device_ok_for_demo: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "headline": self.headline,
            "device_ok_for_demo": self.device_ok_for_demo,
        }


@dataclass
class Hero30Surface:
    """M52H.1: Above-the-fold hero for first ~30 seconds."""

    eyebrow: str = ""
    headline: str = ""
    subline: str = ""
    trust_chip: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "eyebrow": self.eyebrow,
            "headline": self.headline,
            "subline": self.subline,
            "trust_chip": self.trust_chip,
        }


@dataclass
class RolePreviewCard:
    preset_id: str = ""
    label: str = ""
    hook: str = ""
    switch_command: str = ""
    is_active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "hook": self.hook,
            "switch_command": self.switch_command,
            "is_active": self.is_active,
        }


@dataclass
class RoleSwitchPreviewState:
    cards: list[RolePreviewCard] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"cards": [c.to_dict() for c in self.cards]}


@dataclass
class NextStepCard:
    label: str = ""
    command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "command": self.command}


@dataclass
class RoleStateSurface:
    active_role_label: str = ""
    vertical_pack_display: str = ""
    preset_id: str = ""
    role_one_liner: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_role_label": self.active_role_label,
            "vertical_pack_display": self.vertical_pack_display,
            "preset_id": self.preset_id,
            "role_one_liner": self.role_one_liner,
        }


@dataclass
class MemoryBootstrapSurface:
    headline: str = ""
    files_scanned: int = 0
    memory_units: int = 0
    what_learned_bullets: list[str] = field(default_factory=list)
    bounded_note: str = ""
    narrative_intro: str = ""
    insight_lines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline": self.headline,
            "files_scanned": self.files_scanned,
            "memory_units": self.memory_units,
            "what_learned_bullets": list(self.what_learned_bullets),
            "bounded_note": self.bounded_note,
            "narrative_intro": self.narrative_intro,
            "insight_lines": list(self.insight_lines),
        }


@dataclass
class ReadyToAssistSurface:
    ready: bool = False
    status_headline: str = ""
    confirmation_plain: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "status_headline": self.status_headline,
            "confirmation_plain": self.confirmation_plain,
        }


@dataclass
class FirstValueSurface:
    headline: str = ""
    why_this_matters: str = ""
    command: str = ""
    what_happens_next: str = ""
    subcopy_tight: str = ""
    next_step_label: str = ""
    next_step_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline": self.headline,
            "why_this_matters": self.why_this_matters,
            "command": self.command,
            "what_happens_next": self.what_happens_next,
            "subcopy_tight": self.subcopy_tight,
            "next_step_label": self.next_step_label,
            "next_step_command": self.next_step_command,
        }


@dataclass
class TrustPostureSurface:
    headline: str = ""
    body: str = ""
    simulate_first: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline": self.headline,
            "body": self.body,
            "simulate_first": self.simulate_first,
        }


@dataclass
class ActivityTimelineItem:
    step_id: str = ""
    label: str = ""
    status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {"step_id": self.step_id, "label": self.label, "status": self.status}


@dataclass
class ActivityTimelineState:
    items: list[ActivityTimelineItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"items": [i.to_dict() for i in self.items]}


@dataclass
class MissionControlSidePanelState:
    inbox_summary: str = ""
    intervention_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"inbox_summary": self.inbox_summary, "intervention_note": self.intervention_note}


@dataclass
class MissionControlInvestorHome:
    generated_at_utc: str = ""
    readiness: ReadinessStateSnapshot = field(default_factory=ReadinessStateSnapshot)
    role: RoleStateSurface = field(default_factory=RoleStateSurface)
    memory: MemoryBootstrapSurface = field(default_factory=MemoryBootstrapSurface)
    ready_surface: ReadyToAssistSurface = field(default_factory=ReadyToAssistSurface)
    first_value: FirstValueSurface = field(default_factory=FirstValueSurface)
    trust: TrustPostureSurface = field(default_factory=TrustPostureSurface)
    timeline: ActivityTimelineState = field(default_factory=ActivityTimelineState)
    side_panel: MissionControlSidePanelState = field(default_factory=MissionControlSidePanelState)
    hero_30: Hero30Surface = field(default_factory=Hero30Surface)
    role_switch_previews: RoleSwitchPreviewState = field(default_factory=RoleSwitchPreviewState)
    next_step_card: NextStepCard = field(default_factory=NextStepCard)
    narrative_flow_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at_utc": self.generated_at_utc,
            "readiness": self.readiness.to_dict(),
            "role": self.role.to_dict(),
            "memory": self.memory.to_dict(),
            "ready_to_assist": self.ready_surface.to_dict(),
            "first_value": self.first_value.to_dict(),
            "trust": self.trust.to_dict(),
            "timeline": self.timeline.to_dict(),
            "side_panel": self.side_panel.to_dict(),
            "hero_30": self.hero_30.to_dict(),
            "role_switch_previews": self.role_switch_previews.to_dict(),
            "next_step_card": self.next_step_card.to_dict(),
            "narrative_flow_steps": list(self.narrative_flow_steps),
        }
