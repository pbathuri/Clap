"""
M33A–M33D: Workflow episode tracker + cross-app context bridge.

Detect in-progress multi-step workflows, link activity across apps/files/tools,
maintain live episode state, infer stage and handoff gaps. Local-only, explainable.
"""

from workflow_dataset.workflow_episodes.models import (
    WorkflowEpisode,
    WorkflowEpisodeType,
    WorkflowStage,
    LinkedActivity,
    InferredProjectAssociation,
    CurrentTaskHypothesis,
    HandoffGap,
    HandoffGapKind,
    NextStepCandidate,
    EpisodeTransitionEvent,
    EpisodeCloseReason,
)
from workflow_dataset.workflow_episodes.bridge import build_active_episode
from workflow_dataset.workflow_episodes.store import (
    get_current_episode,
    save_current_episode,
    list_recent_episodes,
    get_episodes_dir,
)
from workflow_dataset.workflow_episodes.stage_detection import (
    infer_stage,
    infer_handoff_gaps,
    infer_next_step_candidates,
    infer_episode_type,
)
from workflow_dataset.workflow_episodes.explain import (
    build_episode_explanation,
    build_stage_explanation,
    build_handoff_gaps_explanation,
    build_transition_map_output,
    build_advance_stall_explanation,
)
from workflow_dataset.workflow_episodes.transition_map import get_transition_map

__all__ = [
    "WorkflowEpisode",
    "WorkflowEpisodeType",
    "WorkflowStage",
    "LinkedActivity",
    "InferredProjectAssociation",
    "CurrentTaskHypothesis",
    "HandoffGap",
    "HandoffGapKind",
    "NextStepCandidate",
    "EpisodeTransitionEvent",
    "EpisodeCloseReason",
    "build_active_episode",
    "get_current_episode",
    "save_current_episode",
    "list_recent_episodes",
    "get_episodes_dir",
    "infer_stage",
    "infer_handoff_gaps",
    "infer_next_step_candidates",
    "infer_episode_type",
    "build_episode_explanation",
    "build_stage_explanation",
    "build_handoff_gaps_explanation",
    "build_transition_map_output",
    "build_advance_stall_explanation",
    "get_transition_map",
]
