"""
Active work context model (M32A).

Explicit models for: active work context, focus target, inferred project/task family,
work mode, confidence/evidence, source contribution, session transition, context decay.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkMode(str, Enum):
    """Current work mode inferred from signals (attention/flow state)."""
    UNKNOWN = "unknown"
    FOCUSED = "focused"           # sustained single project/task
    SWITCHING = "switching"       # recent project or task change
    INTERRUPTED = "interrupted"   # break or context break
    RETURNING = "returning"       # likely resuming prior context
    IDLE = "idle"                 # no strong signals


class ActivityMode(str, Enum):
    """Explicit activity type inferred from signals (M32D.1)."""
    UNKNOWN = "unknown"
    WRITING = "writing"           # docs, prose (e.g. .md, .docx, .txt)
    REVIEWING = "reviewing"       # review/feedback artifacts
    PLANNING = "planning"         # plans, specs, spreadsheets
    CODING = "coding"             # source code (e.g. .py, .ts, .js)
    COORDINATION = "coordination" # mixed comms/meetings/cal
    ADMIN = "admin"               # admin, config, ops (e.g. .yaml, .json, configs)


class FocusStateKind(str, Enum):
    """Inferred focus state (M32D.1)."""
    UNKNOWN = "unknown"
    SINGLE_FILE = "single_file"       # one file dominates recent events
    MULTI_FILE_SAME_DIR = "multi_file_same_dir"  # several files in same directory
    PROJECT_BROWSE = "project_browse"  # multiple dirs under one project
    SCATTERED = "scattered"           # multiple projects or unrelated paths


class FocusState(BaseModel):
    """Inferred focus state with explanation (M32D.1)."""
    kind: FocusStateKind = Field(default=FocusStateKind.UNKNOWN)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = Field(default="", description="Why the system believes this focus state")
    signal_summary: str = Field(default="", description="Short signal summary e.g. file counts, dirs")


class SessionTransitionKind(str, Enum):
    """Kind of session transition detected."""
    SESSION_START = "session_start"
    PROJECT_SWITCH = "project_switch"
    DEEP_WORK_CONTINUATION = "deep_work_continuation"
    INTERRUPTION = "interruption"
    RETURN_TO_WORK = "return_to_work"


class FocusTarget(BaseModel):
    """What the user appears to be focused on (path, app, or abstract label)."""
    kind: str = Field(default="", description="path | app | domain | task_label")
    value: str = Field(default="", description="e.g. path, app name, domain, label")
    display_name: str = Field(default="", description="Human-readable short label")


class InferredProject(BaseModel):
    """Inferred project association from observation/graph."""
    project_id: str = Field(default="", description="Stable id or label")
    label: str = Field(default="", description="Human-readable name")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class InferredTaskFamily(BaseModel):
    """Inferred task family or routine (e.g. editing docs, coding)."""
    task_id: str = Field(default="", description="Stable id or label")
    label: str = Field(default="", description="Human-readable name")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class SourceContribution(BaseModel):
    """Contribution of one signal source to the fused context."""
    source: str = Field(default="", description="file | app | browser | terminal | calendar | teaching | graph | session")
    weight: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_summary: str = Field(default="")
    signals_count: int = Field(default=0)


class ActiveWorkContext(BaseModel):
    """Current active work context: fused from observation + graph + session."""

    context_id: str = Field(default="", description="Stable id for this snapshot")
    timestamp_utc: str = Field(default="", description="When context was computed")
    # Inferred focus and associations
    focus_target: FocusTarget | None = Field(default=None)
    inferred_project: InferredProject | None = Field(default=None)
    inferred_task_family: InferredTaskFamily | None = Field(default=None)
    work_mode: WorkMode = Field(default=WorkMode.UNKNOWN)
    # Activity mode and focus state (M32D.1)
    activity_mode: ActivityMode = Field(default=ActivityMode.UNKNOWN, description="Inferred activity: writing, reviewing, planning, coding, coordination, admin")
    focus_state: FocusState | None = Field(default=None, description="Inferred focus state with reason")
    activity_mode_reason: str = Field(default="", description="Deeper summary: why the system believes this activity mode")
    focus_state_reason: str = Field(default="", description="Deeper summary: why the system believes this focus state")
    # Confidence and evidence
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_summary: list[str] = Field(default_factory=list)
    source_contributions: list[SourceContribution] = Field(default_factory=list)
    # Staleness
    is_stale: bool = Field(default=False, description="True if based on old or no recent signals")
    last_signal_utc: str = Field(default="", description="Timestamp of most recent signal used")
    # Optional session/project hints from session layer
    session_hint: str = Field(default="")
    project_hint: str = Field(default="")


class SessionTransitionEvent(BaseModel):
    """A detected session transition (start, project switch, interruption, etc.)."""

    transition_id: str = Field(default="")
    kind: SessionTransitionKind = Field(default=SessionTransitionKind.SESSION_START)
    timestamp_utc: str = Field(default="")
    from_project: str = Field(default="")
    to_project: str = Field(default="")
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# Context decay: consider context stale if no signal in this many seconds (first-draft constant)
CONTEXT_STALE_SECONDS = 900  # 15 minutes
