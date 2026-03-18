"""
M32E–M32H: Just-in-time assist engine + suggestion queue.

Generate timely assistance from live context; persist in a reviewable queue;
prioritize by usefulness/confidence; support accept/snooze/dismiss.
"""

from workflow_dataset.assist_engine.models import (
    AssistSuggestion,
    SuggestionReason,
    TriggeringContext,
    SuggestionStatus,
    SuggestionType,
)
from workflow_dataset.assist_engine.store import (
    save_suggestion,
    load_suggestion,
    list_suggestions,
    update_status,
    list_dismissed_patterns,
)
from workflow_dataset.assist_engine.generation import generate_assist_suggestions
from workflow_dataset.assist_engine.queue import (
    run_now,
    get_queue,
    accept_suggestion,
    dismiss_suggestion,
    snooze_suggestion,
)
from workflow_dataset.assist_engine.explain import explain_suggestion
from workflow_dataset.assist_engine.policy import load_policy, apply_policy
from workflow_dataset.assist_engine.policy_models import (
    AssistPolicyConfig,
    QuietHoursWindow,
    FocusSafeRule,
    InterruptibilityRule,
)

__all__ = [
    "AssistSuggestion",
    "SuggestionReason",
    "TriggeringContext",
    "SuggestionStatus",
    "SuggestionType",
    "save_suggestion",
    "load_suggestion",
    "list_suggestions",
    "update_status",
    "list_dismissed_patterns",
    "generate_assist_suggestions",
    "run_now",
    "get_queue",
    "accept_suggestion",
    "dismiss_suggestion",
    "snooze_suggestion",
    "explain_suggestion",
    "load_policy",
    "apply_policy",
    "AssistPolicyConfig",
    "QuietHoursWindow",
    "FocusSafeRule",
    "InterruptibilityRule",
]
