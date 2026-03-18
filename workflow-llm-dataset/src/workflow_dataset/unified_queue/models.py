"""
M36E–M36H: Unified work queue models.
M36H.1: Queue view mode, sections by project/episode, overloaded summary.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceSubsystem(str, Enum):
    """Origin of the queue item."""
    APPROVAL_QUEUE = "approval_queue"
    AUTOMATION_INBOX = "automation_inbox"
    REVIEW_STUDIO = "review_studio"
    LANES = "lanes"
    ACTION_CARDS = "action_cards"
    ASSIST = "assist"
    PROJECT_NEXT = "project_next"
    PORTFOLIO_NEXT = "portfolio_next"
    IN_FLOW_DRAFT = "in_flow_draft"
    BLOCKED_RUN = "blocked_run"
    RESUME_CONTINUITY = "resume_continuity"


class ActionabilityClass(str, Enum):
    """What kind of action the item needs."""
    NEEDS_APPROVAL = "needs_approval"
    NEEDS_REVIEW = "needs_review"
    EXECUTABLE = "executable"
    DEFERRED = "deferred"
    BLOCKED = "blocked"


class RoutingTarget(str, Enum):
    """Where to route when accepted."""
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEW = "review"
    WORKSPACE = "workspace"
    AUTOMATION_FOLLOW_UP = "automation_follow_up"
    DRAFT_COMPOSER = "draft_composer"


class UnifiedQueueItem(BaseModel):
    """One normalized item in the unified work queue."""

    item_id: str = Field(default="", description="Stable id (e.g. uq_xxx)")
    source_subsystem: SourceSubsystem = Field(default=SourceSubsystem.REVIEW_STUDIO)
    source_ref: str = Field(default="", description="Original id in source system")
    actionability_class: ActionabilityClass = Field(default=ActionabilityClass.NEEDS_REVIEW)
    priority: str = Field(default="medium", description="urgent | high | medium | low")
    urgency_score: float = Field(default=0.5, ge=0, le=1)
    value_score: float = Field(default=0.5, ge=0, le=1)
    trust_score: float = Field(default=0.5, ge=0, le=1)
    routing_target: str = Field(default="", description="RoutingTarget value")
    blocked_reason: str = Field(default="")
    state: str = Field(default="pending", description="pending | deferred | dismissed")
    section_id: str = Field(default="", description="Assigned section: blocked, approval, focus_ready, review_ready, operator_ready, wrap_up")
    project_id: str = Field(default="", description="For section-by-project")
    episode_id: str = Field(default="", description="For section-by-episode")
    label: str = Field(default="")
    summary: str = Field(default="")
    entity_refs: dict[str, str] = Field(default_factory=dict)
    created_at: str = Field(default="")
    mode_tags: list[str] = Field(default_factory=list, description="focus_ready, review_ready, operator_ready, wrap_up")


# ----- M36H.1 Queue sections (by project or episode) -----


class QueueSection(BaseModel):
    """A named section of the queue (e.g. by project or episode)."""

    section_id: str = Field(default="")
    label: str = Field(default="")
    project_id: str = Field(default="")
    episode_id: str = Field(default="")
    item_ids: list[str] = Field(default_factory=list)
    count: int = Field(default=0)


# ----- M36H.1 Mode-aware queue view -----


class QueueViewMode(str, Enum):
    """Bundled view by operator mode."""
    FOCUS = "focus"
    REVIEW = "review"
    OPERATOR = "operator"
    WRAP_UP = "wrap_up"


class ModeAwareQueueView(BaseModel):
    """A queue view filtered/grouped by mode (focus, review, operator, wrap-up)."""

    mode: QueueViewMode = Field(default=QueueViewMode.FOCUS)
    label: str = Field(default="", description="e.g. Focus mode")
    description: str = Field(default="")
    item_ids: list[str] = Field(default_factory=list)
    sections: list[QueueSection] = Field(default_factory=list, description="Sections in this view")
    total_count: int = Field(default=0)
    generated_at_utc: str = Field(default="")


# ----- M36H.1 Overloaded-queue summary -----


class QueueSummary(BaseModel):
    """Summary of the queue; stronger fields when overloaded."""

    total_count: int = Field(default=0)
    is_overloaded: bool = Field(default=False)
    overload_threshold: int = Field(default=20)
    by_section: dict[str, int] = Field(default_factory=dict, description="section_id -> count")
    by_mode: dict[str, int] = Field(default_factory=dict, description="mode -> count (focus_ready, review_ready, etc.)")
    top_blocked_item_id: str = Field(default="")
    top_blocked_summary: str = Field(default="")
    recommended_cap: int = Field(default=10, description="Suggested max items to show in default list")
    overflow_message: str = Field(default="", description="Operator-facing message when overloaded")
    suggested_action: str = Field(default="", description="e.g. Use queue view --mode focus to narrow")
    generated_at_utc: str = Field(default="")
