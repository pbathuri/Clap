"""
M29E–M29H: Conversational intent model — explicit intents for status, explanation, next-action, blocked, approval, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Intent types
INTENT_STATUS_QUERY = "status_query"
INTENT_EXPLANATION_QUERY = "explanation_query"
INTENT_NEXT_ACTION_QUERY = "next_action_query"
INTENT_BLOCKED_STATE_QUERY = "blocked_state_query"
INTENT_APPROVAL_REVIEW_QUERY = "approval_review_query"
INTENT_PROJECT_SWITCH_REQUEST = "project_switch_request"
INTENT_PLAN_PREVIEW_REQUEST = "plan_preview_request"
INTENT_EXECUTION_PREVIEW_REQUEST = "execution_preview_request"
INTENT_POLICY_QUESTION = "policy_question"
INTENT_ARTIFACT_LOOKUP = "artifact_lookup"
INTENT_WHAT_CHANGED = "what_changed"
INTENT_UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Result of mapping natural language to an explicit intent."""
    intent_type: str
    scope: dict[str, Any] = field(default_factory=dict)  # e.g. project_id, goal_id, pack_ref
    confidence: float = 0.0  # 0..1
    ambiguity_note: str = ""
    suggested_command: str = ""
    raw_phrase: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_type": self.intent_type,
            "scope": dict(self.scope),
            "confidence": self.confidence,
            "ambiguity_note": self.ambiguity_note,
            "suggested_command": self.suggested_command,
            "raw_phrase": self.raw_phrase,
        }
