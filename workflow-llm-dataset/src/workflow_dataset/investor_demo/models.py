"""
M51I–M51L: Investor demo flow — models for session, narrative, panel, supervised action, degraded warnings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DemoNarrativeStage(str, Enum):
    """Ordered narrative stages for investor walkthrough."""
    STARTUP_READINESS = "startup_readiness"
    ROLE_ONBOARDING = "role_onboarding"
    MEMORY_BOOTSTRAP = "memory_bootstrap"
    INFERRED_USER_CONTEXT = "inferred_user_context"
    FIRST_VALUE_RECOMMENDATION = "first_value_recommendation"
    ARTIFACT_GENERATION = "artifact_generation"
    SUPERVISED_OPERATOR_ACTION = "supervised_operator_action"
    CLOSING_MISSION_CONTROL_SUMMARY = "closing_mission_control_summary"


STAGE_ORDER: list[DemoNarrativeStage] = [
    DemoNarrativeStage.STARTUP_READINESS,
    DemoNarrativeStage.ROLE_ONBOARDING,
    DemoNarrativeStage.MEMORY_BOOTSTRAP,
    DemoNarrativeStage.INFERRED_USER_CONTEXT,
    DemoNarrativeStage.FIRST_VALUE_RECOMMENDATION,
    DemoNarrativeStage.ARTIFACT_GENERATION,
    DemoNarrativeStage.SUPERVISED_OPERATOR_ACTION,
    DemoNarrativeStage.CLOSING_MISSION_CONTROL_SUMMARY,
]


@dataclass
class PresenterGuidanceNote:
    """Presenter-facing guidance for one narrative stage."""
    stage_id: str
    headline: str
    talking_points: list[str] = field(default_factory=list)
    caution: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "headline": self.headline,
            "talking_points": list(self.talking_points),
            "caution": self.caution,
        }


@dataclass
class DegradedDemoWarning:
    """Explicit warning when demo should acknowledge degraded or incomplete state."""
    warning_id: str
    message: str
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"warning_id": self.warning_id, "message": self.message, "source": self.source}


@dataclass
class DemoMissionControlPanel:
    """Presentation-safe mission-control subset for storytelling."""
    device_readiness_line: str = ""
    chosen_role_demo_pack: str = ""
    memory_bootstrap_summary: str = ""
    active_project_context: str = ""
    first_value_opportunity: str = ""
    recommended_safe_action: str = ""
    evidence_system_learned: str = ""
    supervised_and_safe_posture: str = ""
    degraded_warnings: list[DegradedDemoWarning] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_readiness_line": self.device_readiness_line,
            "chosen_role_demo_pack": self.chosen_role_demo_pack,
            "memory_bootstrap_summary": self.memory_bootstrap_summary,
            "active_project_context": self.active_project_context,
            "first_value_opportunity": self.first_value_opportunity,
            "recommended_safe_action": self.recommended_safe_action,
            "evidence_system_learned": self.evidence_system_learned,
            "supervised_and_safe_posture": self.supervised_and_safe_posture,
            "degraded_warnings": [w.to_dict() for w in self.degraded_warnings],
        }


@dataclass
class FirstValueDemoPath:
    """First-value slice for investor demo."""
    opportunity_line: str = ""
    rationale_line: str = ""
    next_safe_command: str = ""
    artifact_markdown: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_line": self.opportunity_line,
            "rationale_line": self.rationale_line,
            "next_safe_command": self.next_safe_command,
            "artifact_markdown": self.artifact_markdown,
        }


@dataclass
class SupervisedActionDemo:
    """One supervised, safe action demonstration (preview only)."""
    card_id: str = ""
    title: str = ""
    description: str = ""
    preview: dict[str, Any] = field(default_factory=dict)
    what_happens_on_approval: str = ""
    trust_posture: str = "simulate_only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "title": self.title,
            "description": self.description,
            "preview": dict(self.preview),
            "what_happens_on_approval": self.what_happens_on_approval,
            "trust_posture": self.trust_posture,
        }


@dataclass
class DemoCompletionState:
    """Demo session completion."""
    completed: bool = False
    completed_at_iso: str = ""
    stages_completed: list[str] = field(default_factory=list)
    closing_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "completed": self.completed,
            "completed_at_iso": self.completed_at_iso,
            "stages_completed": list(self.stages_completed),
            "closing_summary": self.closing_summary,
        }


@dataclass
class InvestorDemoSession:
    """Investor demo session state."""
    session_id: str = ""
    started_at_iso: str = ""
    current_stage: str = DemoNarrativeStage.STARTUP_READINESS.value
    vertical_id: str = ""
    role_demo_pack_id: str = "founder_operator"
    presenter_guidance: PresenterGuidanceNote | None = None
    degraded_warnings: list[DegradedDemoWarning] = field(default_factory=list)
    completion: DemoCompletionState = field(default_factory=DemoCompletionState)
    presenter_mode_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at_iso": self.started_at_iso,
            "current_stage": self.current_stage,
            "vertical_id": self.vertical_id,
            "role_demo_pack_id": self.role_demo_pack_id,
            "presenter_guidance": self.presenter_guidance.to_dict() if self.presenter_guidance else None,
            "degraded_warnings": [w.to_dict() for w in self.degraded_warnings],
            "completion": self.completion.to_dict(),
            "presenter_mode_enabled": self.presenter_mode_enabled,
        }


# ----- M51L.1 Presenter mode + 5-minute script -----


@dataclass
class PresenterModeConfig:
    """Presenter mode toggle (persisted alongside session)."""
    enabled: bool = False
    five_minute_script_active: bool = True
    updated_at_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "five_minute_script_active": self.five_minute_script_active,
            "updated_at_iso": self.updated_at_iso,
        }


@dataclass
class DemoScriptBeat:
    """One beat in the 5-minute investor script: show / click / say + degraded line."""
    beat_index: int
    stage_id: str
    start_after_seconds: int
    duration_seconds: int
    show: str
    click_or_run: str
    say: str
    if_degraded_say: str = ""
    narrative_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "beat_index": self.beat_index,
            "stage_id": self.stage_id,
            "start_after_seconds": self.start_after_seconds,
            "duration_seconds": self.duration_seconds,
            "show": self.show,
            "click_or_run": self.click_or_run,
            "say": self.say,
            "if_degraded_say": self.if_degraded_say,
            "narrative_note": self.narrative_note,
        }


@dataclass
class FiveMinuteDemoScript:
    """Full 5-minute script (~300s) aligned to narrative stages."""
    total_target_seconds: int = 300
    beats: list[DemoScriptBeat] = field(default_factory=list)
    degraded_opening_line: str = ""
    script_id: str = "investor_demo_5min_v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "script_id": self.script_id,
            "total_target_seconds": self.total_target_seconds,
            "degraded_opening_line": self.degraded_opening_line,
            "beats": [b.to_dict() for b in self.beats],
        }


@dataclass
class PresenterModeView:
    """Compact presenter-facing view: mode, degraded bridge, current cue."""
    presenter_mode_enabled: bool
    degraded_bridge: str
    is_degraded_demo: bool
    current_stage_id: str
    current_beat: DemoScriptBeat | None
    headline: str
    next_cli_hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "presenter_mode_enabled": self.presenter_mode_enabled,
            "degraded_bridge": self.degraded_bridge,
            "is_degraded_demo": self.is_degraded_demo,
            "current_stage_id": self.current_stage_id,
            "current_beat": self.current_beat.to_dict() if self.current_beat else None,
            "headline": self.headline,
            "next_cli_hints": list(self.next_cli_hints),
        }
