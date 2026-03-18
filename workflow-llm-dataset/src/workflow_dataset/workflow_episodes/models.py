"""
M33A–M33D: Workflow episode model — episode, stage, linked activity, handoff gap, next-step, transition.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStage(str, Enum):
    """First-draft workflow stages."""
    UNKNOWN = "unknown"
    INTAKE = "intake"           # gathering / discovery
    DRAFTING = "drafting"       # creating / editing
    REVIEW = "review"           # reviewing / feedback
    APPROVAL_DECISION = "approval_decision"  # approval / sign-off
    EXECUTION_FOLLOWUP = "execution_followup"  # running / follow-up
    HANDOFF_WRAPUP = "handoff_wrapup"  # handoff / wrap-up


class WorkflowEpisodeType(str, Enum):
    """M33D.1: Workflow episode types for clearer context."""
    UNKNOWN = "unknown"
    DOCUMENT_HANDOFF = "document_handoff"       # doc creation, review, handoff
    APPROVAL_CYCLE = "approval_cycle"           # approval / sign-off flow
    RESEARCH_SYNTHESIS = "research_synthesis"   # gather, read, synthesize
    CODING_DEBUGGING = "coding_debugging"       # code edit, run, debug
    MEETING_FOLLOWUP = "meeting_followup"       # post-meeting notes, actions


class HandoffGapKind(str, Enum):
    """Kind of handoff or missing step."""
    MISSING_ARTIFACT = "missing_artifact"
    MISSING_APPROVAL = "missing_approval"
    LIKELY_CONTEXT_SWITCH = "likely_context_switch"
    STALE_EPISODE = "stale_episode"


class EpisodeCloseReason(str, Enum):
    """Why an episode was closed."""
    EXPLICIT = "explicit"
    STALE = "stale"
    NO_SIGNALS = "no_signals"
    SINGLE_ACTION = "single_action"
    CONTEXT_SWITCH = "context_switch"


class LinkedActivity(BaseModel):
    """Single activity linked to an episode (file, app, browser, terminal, notes)."""
    event_id: str = Field(default="", description="Observation event id")
    source: str = Field(default="", description="file | app | browser | terminal | notes")
    timestamp_utc: str = Field(default="")
    activity_type: str = Field(default="", description="Coarse type from payload")
    path: str = Field(default="", description="Path if file/path-based")
    label: str = Field(default="", description="Short display label")
    evidence: str = Field(default="", description="Why linked to this episode")


class InferredProjectAssociation(BaseModel):
    """Project association for the episode."""
    project_id: str = Field(default="")
    label: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class CurrentTaskHypothesis(BaseModel):
    """Current task hypothesis for the episode."""
    task_id: str = Field(default="")
    label: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class HandoffGap(BaseModel):
    """A detected handoff gap (missing artifact, missing approval, likely switch)."""
    kind: HandoffGapKind = Field(default=HandoffGapKind.MISSING_ARTIFACT)
    summary: str = Field(default="", description="Short human-readable summary")
    evidence: list[str] = Field(default_factory=list)
    suggested_action: str = Field(default="", description="Optional suggested next step")


class NextStepCandidate(BaseModel):
    """A candidate next step (e.g. open review, switch to terminal)."""
    label: str = Field(default="")
    context: str = Field(default="", description="e.g. app/tool/context")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class EpisodeTransitionEvent(BaseModel):
    """Episode lifecycle transition (e.g. stage change, episode start/close)."""
    transition_id: str = Field(default="")
    episode_id: str = Field(default="")
    kind: str = Field(default="", description="stage_change | episode_start | episode_close")
    from_stage: str = Field(default="")
    to_stage: str = Field(default="")
    timestamp_utc: str = Field(default="")
    evidence: list[str] = Field(default_factory=list)


class WorkflowEpisode(BaseModel):
    """A workflow episode: bounded in-progress multi-step workflow with linked activities."""

    episode_id: str = Field(default="", description="Stable id")
    started_at_utc: str = Field(default="")
    updated_at_utc: str = Field(default="")
    # Linked activities (file, app, browser, terminal, notes)
    linked_activities: list[LinkedActivity] = Field(default_factory=list)
    # Inferred associations
    inferred_project: InferredProjectAssociation | None = Field(default=None)
    current_task_hypothesis: CurrentTaskHypothesis | None = Field(default=None)
    # Stage and next-step
    stage: WorkflowStage = Field(default=WorkflowStage.UNKNOWN)
    stage_evidence: list[str] = Field(default_factory=list)
    # M33D.1: Episode type and transition clarity
    episode_type: str = Field(default="unknown", description="WorkflowEpisodeType value")
    episode_type_evidence: list[str] = Field(default_factory=list)
    next_step_candidates: list[NextStepCandidate] = Field(default_factory=list)
    handoff_gaps: list[HandoffGap] = Field(default_factory=list)
    # Confidence and evidence
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_summary: list[str] = Field(default_factory=list)
    # Lifecycle
    is_active: bool = Field(default=True)
    closed_at_utc: str = Field(default="")
    close_reason: str = Field(default="", description="EpisodeCloseReason value or empty")

    def to_dict(self) -> dict[str, Any]:
        d = self.model_dump()
        d["stage"] = self.stage.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WorkflowEpisode:
        stage = d.get("stage", "unknown")
        if isinstance(stage, str):
            try:
                d = {**d, "stage": WorkflowStage(stage)}
            except ValueError:
                d = {**d, "stage": WorkflowStage.UNKNOWN}
        return cls.model_validate(d)
