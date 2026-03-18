"""
M29E–M29H: Conversational command center — intent model, NL interpreter, explainability, action preview.
"""

from workflow_dataset.conversational.intents import (
    ParsedIntent,
    INTENT_STATUS_QUERY,
    INTENT_EXPLANATION_QUERY,
    INTENT_NEXT_ACTION_QUERY,
    INTENT_BLOCKED_STATE_QUERY,
    INTENT_APPROVAL_REVIEW_QUERY,
    INTENT_PROJECT_SWITCH_REQUEST,
    INTENT_PLAN_PREVIEW_REQUEST,
    INTENT_EXECUTION_PREVIEW_REQUEST,
    INTENT_POLICY_QUESTION,
    INTENT_ARTIFACT_LOOKUP,
    INTENT_WHAT_CHANGED,
    INTENT_UNKNOWN,
)
from workflow_dataset.conversational.interpreter import parse_natural_language
from workflow_dataset.conversational.ask import ask
from workflow_dataset.conversational.suggested_queries import get_suggested_queries, get_follow_up_prompts_when_ambiguous
from workflow_dataset.conversational.dialogues import (
    list_guided_dialogues,
    get_dialogue_definition,
    get_dialogue_for_intent,
    FLOW_UNBLOCK_PROJECT,
    FLOW_APPROVE_AND_RUN,
    FLOW_SWITCH_AND_PLAN,
    FLOW_REVIEW_LANES,
)
from workflow_dataset.conversational.roles import get_role_suggested_commands, get_roles

__all__ = [
    "ParsedIntent",
    "INTENT_STATUS_QUERY",
    "INTENT_EXPLANATION_QUERY",
    "INTENT_NEXT_ACTION_QUERY",
    "INTENT_BLOCKED_STATE_QUERY",
    "INTENT_APPROVAL_REVIEW_QUERY",
    "INTENT_PROJECT_SWITCH_REQUEST",
    "INTENT_PLAN_PREVIEW_REQUEST",
    "INTENT_EXECUTION_PREVIEW_REQUEST",
    "INTENT_POLICY_QUESTION",
    "INTENT_ARTIFACT_LOOKUP",
    "INTENT_WHAT_CHANGED",
    "INTENT_UNKNOWN",
    "parse_natural_language",
    "ask",
    "get_suggested_queries",
    "get_follow_up_prompts_when_ambiguous",
    "list_guided_dialogues",
    "get_dialogue_definition",
    "get_dialogue_for_intent",
    "FLOW_UNBLOCK_PROJECT",
    "FLOW_APPROVE_AND_RUN",
    "FLOW_SWITCH_AND_PLAN",
    "FLOW_REVIEW_LANES",
    "get_role_suggested_commands",
    "get_roles",
]
