"""
Live work context fusion and session detection (M32).

Fuses bounded observation + personal graph + session into current active-work context.
Detects session transitions (start, project switch, deep work, interruption, return).
Local-only; no new data collection. Substrate for context-aware assistance.
"""

from workflow_dataset.live_context.models import (
    ActiveWorkContext,
    ActivityMode,
    FocusState,
    FocusStateKind,
    FocusTarget,
    InferredProject,
    InferredTaskFamily,
    WorkMode,
    SourceContribution,
    SessionTransitionEvent,
    SessionTransitionKind,
)
from workflow_dataset.live_context.fusion import fuse_active_context
from workflow_dataset.live_context.session_detector import detect_transitions
from workflow_dataset.live_context.state import (
    get_live_context_state,
    save_live_context_state,
    get_recent_transitions,
    append_transition,
)

__all__ = [
    "ActiveWorkContext",
    "ActivityMode",
    "FocusState",
    "FocusStateKind",
    "FocusTarget",
    "InferredProject",
    "InferredTaskFamily",
    "WorkMode",
    "SourceContribution",
    "SessionTransitionEvent",
    "SessionTransitionKind",
    "fuse_active_context",
    "detect_transitions",
    "get_live_context_state",
    "save_live_context_state",
    "get_recent_transitions",
    "append_transition",
]
