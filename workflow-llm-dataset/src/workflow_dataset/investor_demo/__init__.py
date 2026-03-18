"""
M51I–M51L: Investor demo flow — presentation mission control, narrative session, first-value artifact, supervised action.
"""

from workflow_dataset.investor_demo.models import (
    DemoNarrativeStage,
    STAGE_ORDER,
    PresenterGuidanceNote,
    DegradedDemoWarning,
    DemoMissionControlPanel,
    FirstValueDemoPath,
    SupervisedActionDemo,
    DemoCompletionState,
    InvestorDemoSession,
    PresenterModeConfig,
    DemoScriptBeat,
    FiveMinuteDemoScript,
    PresenterModeView,
)
from workflow_dataset.investor_demo.narrative import guidance_for_stage, next_stage
from workflow_dataset.investor_demo.degraded import collect_degraded_warnings
from workflow_dataset.investor_demo.session_store import (
    start_demo_session,
    load_demo_session,
    advance_demo_stage,
    session_path,
)
from workflow_dataset.investor_demo.presentation_mc import (
    build_demo_mission_control_panel,
    format_demo_mission_control_text,
)
from workflow_dataset.investor_demo.first_value import build_first_value_demo_path
from workflow_dataset.investor_demo.supervised import build_supervised_action_demo
from workflow_dataset.investor_demo.five_minute_script import (
    build_five_minute_demo_script,
    beat_for_stage,
    format_script_compact_text,
)
from workflow_dataset.investor_demo.degraded_narrative import degraded_narrative_bridge
from workflow_dataset.investor_demo.presenter_mode import (
    load_presenter_config,
    set_presenter_mode,
    build_presenter_mode_view,
    format_presenter_mode_text,
    presenter_config_path,
)

__all__ = [
    "DemoNarrativeStage",
    "STAGE_ORDER",
    "PresenterGuidanceNote",
    "DegradedDemoWarning",
    "DemoMissionControlPanel",
    "FirstValueDemoPath",
    "SupervisedActionDemo",
    "DemoCompletionState",
    "InvestorDemoSession",
    "PresenterModeConfig",
    "DemoScriptBeat",
    "FiveMinuteDemoScript",
    "PresenterModeView",
    "guidance_for_stage",
    "next_stage",
    "collect_degraded_warnings",
    "start_demo_session",
    "load_demo_session",
    "advance_demo_stage",
    "session_path",
    "build_demo_mission_control_panel",
    "format_demo_mission_control_text",
    "build_first_value_demo_path",
    "build_supervised_action_demo",
    "build_five_minute_demo_script",
    "beat_for_stage",
    "format_script_compact_text",
    "degraded_narrative_bridge",
    "load_presenter_config",
    "set_presenter_mode",
    "build_presenter_mode_view",
    "format_presenter_mode_text",
    "presenter_config_path",
]
