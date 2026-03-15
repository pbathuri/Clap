"""
M19: Models for trial feedback — single entry and session summary.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrialFeedbackEntry(BaseModel):
    """Single feedback entry for a task/session."""

    feedback_id: str = Field(default="")
    user_id_or_alias: str = Field(default="", description="Optional alias; no PII")
    session_id: str = Field(default="")
    task_id: str = Field(default="")
    workflow_type: str = Field(default="")
    outcome_rating: str = Field(default="", description="completed | partial | failed")
    usefulness_rating: int = Field(default=0, ge=0, le=5, description="1-5")
    trust_rating: int = Field(default=0, ge=0, le=5, description="1-5")
    style_match_rating: int = Field(default=0, ge=0, le=5, description="1-5")
    confusion_points: str = Field(default="")
    failure_points: str = Field(default="")
    freeform_feedback: str = Field(default="")
    created_utc: str = Field(default="")


class TrialSessionSummary(BaseModel):
    """Summary for one trial session."""

    summary_id: str = Field(default="")
    user_id_or_alias: str = Field(default="")
    session_id: str = Field(default="")
    tasks_attempted: int = Field(default=0)
    tasks_completed: int = Field(default=0)
    top_praise_points: str = Field(default="")
    top_failure_points: str = Field(default="")
    top_requested_features: str = Field(default="")
    created_utc: str = Field(default="")
