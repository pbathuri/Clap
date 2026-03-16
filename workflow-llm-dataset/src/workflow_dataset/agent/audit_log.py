"""
Agent action audit log: proposed, approved, executed, failed.

Device-local only; see docs/schemas/AGENT_ACTION_LOG.md.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ActionLogRecord(BaseModel):
    """Single audit log entry."""

    log_id: str
    timestamp_utc: str = Field(..., description="ISO 8601")
    mode: str = Field(..., description="observe | simulate | assist | automate")
    action_type: str = Field(..., description="e.g. file_write, api_call, suggestion_only")
    intent: str = Field(default="", description="Human-readable intent")
    target: str | dict[str, Any] = Field(default="")
    outcome: str = Field(
        ...,
        description="proposed | approved | rejected | executed | failed | skipped",
    )
    details: dict[str, Any] = Field(default_factory=dict)
    approval_id: str | None = None
    user_override: str | None = None


def append_log(
    log_store: Any,
    record: ActionLogRecord,
) -> None:
    """Append one record to the audit log. TODO: implement persistence."""
    pass


def query_log(
    log_store: Any,
    since_utc: str | None = None,
    mode: str | None = None,
    outcome: str | None = None,
    limit: int = 1000,
) -> list[ActionLogRecord]:
    """Query audit log. TODO: implement."""
    return []
