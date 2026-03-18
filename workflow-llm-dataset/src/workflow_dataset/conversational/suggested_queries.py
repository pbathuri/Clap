"""
M29H.1: Suggested next questions and better follow-up prompts when ambiguity remains.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.conversational.intents import (
    INTENT_STATUS_QUERY,
    INTENT_NEXT_ACTION_QUERY,
    INTENT_BLOCKED_STATE_QUERY,
    INTENT_APPROVAL_REVIEW_QUERY,
    INTENT_WHAT_CHANGED,
    INTENT_EXECUTION_PREVIEW_REQUEST,
    INTENT_PLAN_PREVIEW_REQUEST,
    INTENT_PROJECT_SWITCH_REQUEST,
    INTENT_UNKNOWN,
)


# Follow-up prompts when intent is unknown or ambiguous (better than generic "try these")
AMBIGUITY_FOLLOW_UP_PROMPTS = [
    "What should I do next?",
    "Why is founder_case_alpha blocked?",
    "What changed since yesterday?",
    "What's in the approval queue?",
    "Status",
    "Show me what would happen if I approve the next action.",
    "Preview the current plan",
]


def get_suggested_queries(
    intent_type: str,
    scope: dict[str, Any],
    state: dict[str, Any] | None,
) -> list[str]:
    """
    Return suggested next questions the operator might ask, given the current intent and scope.
    Grounded in typical follow-ups; not exhaustive.
    """
    suggestions: list[str] = []

    if intent_type == INTENT_NEXT_ACTION_QUERY:
        suggestions = [
            "Why is my current project blocked?",
            "What's in the approval queue?",
            "What changed recently?",
            "Status",
            "Should I switch project?",
        ]
    elif intent_type == INTENT_BLOCKED_STATE_QUERY:
        pid = scope.get("project_id") or "this project"
        suggestions = [
            f"Why did we choose {pid}?",
            "What should I do next?",
            "What would unblock it?",
            "Progress recovery for this project",
            "Status",
        ]
    elif intent_type == INTENT_APPROVAL_REVIEW_QUERY or intent_type == INTENT_EXECUTION_PREVIEW_REQUEST:
        suggestions = [
            "What should I do next?",
            "Show me what would happen if I approve the next action.",
            "Why is this action in the queue?",
            "Status",
            "Preview the current plan",
        ]
    elif intent_type == INTENT_WHAT_CHANGED:
        suggestions = [
            "What should I do next?",
            "Why is anything blocked?",
            "Status",
            "Portfolio stalled projects",
        ]
    elif intent_type == INTENT_PLAN_PREVIEW_REQUEST:
        suggestions = [
            "What should I do next?",
            "What's in the approval queue?",
            "Why is the current goal blocked?",
        ]
    elif intent_type == INTENT_PROJECT_SWITCH_REQUEST:
        suggestions = [
            "What should I do next?",
            "Why is founder_case_alpha blocked?",
            "Status",
        ]
    elif intent_type == INTENT_STATUS_QUERY:
        suggestions = [
            "What should I do next?",
            "What changed recently?",
            "What's in the approval queue?",
            "Why is my current project blocked?",
        ]
    else:
        suggestions = list(AMBIGUITY_FOLLOW_UP_PROMPTS[:5])

    return suggestions[:6]


def get_follow_up_prompts_when_ambiguous(
    raw_phrase: str,
    role: str | None = None,
) -> list[str]:
    """
    When confidence is low or intent unknown, return better follow-up prompts.
    Optionally tailor by role (operator, reviewer).
    """
    base = list(AMBIGUITY_FOLLOW_UP_PROMPTS)
    if role == "reviewer":
        return [
            "What's in the approval queue?",
            "Show me what would happen if I approve the next action.",
            "Why is this action in the queue?",
            "Lanes awaiting review",
            "Status",
        ][:6]
    if role == "operator":
        return [
            "What should I do next?",
            "Why is founder_case_alpha blocked?",
            "What changed recently?",
            "Status",
            "Should I switch project?",
        ][:6]
    return base[:6]
