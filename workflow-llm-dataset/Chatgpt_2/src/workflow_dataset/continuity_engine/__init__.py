"""
M36I–M36L: Continuity engine — morning entry, shutdown wrap-up, resume flow, changes since last, carry-forward.
Closes the loop between yesterday, today, active work, and next resume.
"""

from workflow_dataset.continuity_engine.models import (
    ContinuitySnapshot,
    ChangeSinceLastSession,
    MorningEntryBrief,
    ShutdownSummary,
    InterruptedWorkChain,
    ResumeCard,
    CarryForwardItem,
    UnresolvedBlockerContinuation,
    NextSessionRecommendation,
    DailyRhythmTemplate,
    RhythmPhase,
    CarryForwardPolicyOutput,
    NextDayOperatingRecommendation,
    CARRY_FORWARD_CLASS_URGENT,
    CARRY_FORWARD_CLASS_OPTIONAL,
    CARRY_FORWARD_CLASS_AUTOMATED_FOLLOW_UP,
)
from workflow_dataset.continuity_engine.store import (
    get_continuity_dir,
    get_last_session_end_utc,
    save_last_session_end,
    load_last_shutdown,
    save_last_shutdown,
    load_carry_forward,
    save_carry_forward,
    load_next_session_recommendation,
    save_next_session_recommendation,
)
from workflow_dataset.continuity_engine.changes import build_changes_since_last_session
from workflow_dataset.continuity_engine.morning_flow import build_morning_entry_flow
from workflow_dataset.continuity_engine.shutdown_flow import build_shutdown_summary, build_carry_forward_list
from workflow_dataset.continuity_engine.resume_flow import (
    build_resume_flow,
    get_strongest_resume_target,
    detect_interrupted_work,
)

__all__ = [
    "ContinuitySnapshot",
    "ChangeSinceLastSession",
    "MorningEntryBrief",
    "ShutdownSummary",
    "InterruptedWorkChain",
    "ResumeCard",
    "CarryForwardItem",
    "UnresolvedBlockerContinuation",
    "NextSessionRecommendation",
    "get_continuity_dir",
    "get_last_session_end_utc",
    "save_last_session_end",
    "load_last_shutdown",
    "save_last_shutdown",
    "load_carry_forward",
    "save_carry_forward",
    "load_next_session_recommendation",
    "save_next_session_recommendation",
    "build_changes_since_last_session",
    "build_morning_entry_flow",
    "build_shutdown_summary",
    "build_carry_forward_list",
    "build_resume_flow",
    "get_strongest_resume_target",
    "detect_interrupted_work",
    "DailyRhythmTemplate",
    "RhythmPhase",
    "CarryForwardPolicyOutput",
    "NextDayOperatingRecommendation",
    "CARRY_FORWARD_CLASS_URGENT",
    "CARRY_FORWARD_CLASS_OPTIONAL",
    "CARRY_FORWARD_CLASS_AUTOMATED_FOLLOW_UP",
    "list_rhythm_templates",
    "get_rhythm_template",
    "get_recommended_first_phase",
    "apply_carry_forward_policy",
    "build_next_day_operating_recommendation",
]
