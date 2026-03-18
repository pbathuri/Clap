"""
M32E–M32H: Assist suggestion model — just-in-time assist engine.

Explicit models for: assist suggestion, suggestion reason, triggering context,
confidence/evidence, usefulness score, interruptiveness score, affected project/session,
required operator action, dismissal/snooze/accept state.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SuggestionStatus(str, Enum):
    """Lifecycle state of an assist suggestion."""
    PENDING = "pending"
    SNOOZED = "snoozed"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"


class SuggestionType(str, Enum):
    """Kind of assist suggestion (actionable category)."""
    NEXT_STEP = "next_step"
    DRAFT_SUMMARY = "draft_summary"
    BLOCKED_REVIEW = "blocked_review"
    RESUME_ROUTINE = "resume_routine"
    OPEN_ARTIFACT = "open_artifact"
    USE_PREFERENCE = "use_preference"
    REMIND = "remind"
    OTHER = "other"


class TriggeringContext(BaseModel):
    """What triggered this suggestion (live context snapshot)."""
    source: str = Field(default="", description="e.g. progress_board, goal_plan, inbox, routines, skills, packs")
    summary: str = Field(default="", description="Short human-readable summary")
    signals: list[str] = Field(default_factory=list)
    project_id: str = Field(default="")
    session_id: str = Field(default="")


class SuggestionReason(BaseModel):
    """Explainable reason for the suggestion."""
    title: str = Field(default="")
    description: str = Field(default="")
    evidence: list[str] = Field(default_factory=list)


class AssistSuggestion(BaseModel):
    """
    Single just-in-time assist suggestion.
    Stored locally; never executed without operator action. Accept only records outcome.
    """

    suggestion_id: str = Field(..., description="Stable unique ID (e.g. sug_...)")
    suggestion_type: str = Field(..., description="next_step | draft_summary | blocked_review | resume_routine | open_artifact | use_preference | remind | other")
    title: str = Field(default="")
    description: str = Field(default="")
    reason: SuggestionReason | None = Field(default=None)
    triggering_context: TriggeringContext | None = Field(default=None)

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    usefulness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Higher = more useful in context")
    interruptiveness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Higher = more disruptive; prefer lower when ranking")

    affected_project_id: str = Field(default="")
    affected_session_id: str = Field(default="")
    required_operator_action: str = Field(default="", description="What operator can do: e.g. run command, open path, confirm")

    status: str = Field(default="pending", description="pending | snoozed | accepted | dismissed | held_back")
    snoozed_until_utc: str = Field(default="", description="If snoozed, hide until this time (ISO)")
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")

    # M32H.1: Why this suggestion was held back (quiet hours, focus-safe, interruptibility policy)
    held_back_reason: str = Field(default="", description="Human-readable reason when status=held_back")

    supporting_signals: list[str] | list[dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = self.model_dump()
        if self.reason:
            d["reason"] = self.reason.model_dump()
        if self.triggering_context:
            d["triggering_context"] = self.triggering_context.model_dump()
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AssistSuggestion:
        reason = d.get("reason")
        if isinstance(reason, dict):
            d = {**d, "reason": SuggestionReason(**reason)}
        ctx = d.get("triggering_context")
        if isinstance(ctx, dict):
            d = {**d, "triggering_context": TriggeringContext(**ctx)}
        return cls(**d)
