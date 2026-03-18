"""
M24N–M24Q: Outcome capture + session memory + improvement signals.
Transparent session outcome intelligence; no hidden continual learning.
"""

from workflow_dataset.outcomes.models import (
    BLOCKED_CAUSES,
    OUTCOME_KINDS,
    BlockedCause,
    UsefulnessConfirmation,
    IncompleteWork,
    FollowUpRecommendation,
    TaskOutcome,
    ArtifactOutcome,
    SessionOutcome,
)
from workflow_dataset.outcomes.store import (
    get_outcomes_dir,
    get_sessions_dir,
    save_session_outcome,
    get_session_outcome,
    list_session_outcomes,
    load_outcome_history,
)
from workflow_dataset.outcomes.patterns import (
    repeated_block_patterns,
    repeated_success_patterns,
    most_useful_per_pack,
)
from workflow_dataset.outcomes.signals import generate_improvement_signals
from workflow_dataset.outcomes.bridge import (
    outcome_to_correction_suggestions,
    pack_refinement_suggestions,
    next_run_recommendations,
)
from workflow_dataset.outcomes.report import (
    format_session_outcome,
    format_patterns,
    format_recommend_improvements,
    format_pack_scorecard,
    format_improvement_backlog,
)
from workflow_dataset.outcomes.scorecard import build_pack_scorecard, build_improvement_backlog

__all__ = [
    "BLOCKED_CAUSES",
    "OUTCOME_KINDS",
    "BlockedCause",
    "UsefulnessConfirmation",
    "IncompleteWork",
    "FollowUpRecommendation",
    "TaskOutcome",
    "ArtifactOutcome",
    "SessionOutcome",
    "get_outcomes_dir",
    "get_sessions_dir",
    "save_session_outcome",
    "get_session_outcome",
    "list_session_outcomes",
    "load_outcome_history",
    "repeated_block_patterns",
    "repeated_success_patterns",
    "most_useful_per_pack",
    "generate_improvement_signals",
    "outcome_to_correction_suggestions",
    "pack_refinement_suggestions",
    "next_run_recommendations",
    "format_session_outcome",
    "format_patterns",
    "format_recommend_improvements",
    "format_pack_scorecard",
    "format_improvement_backlog",
    "build_pack_scorecard",
    "build_improvement_backlog",
]
