"""
Pydantic models for the local assistive agent loop.

Used by session store, response builder, and CLI.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentQuery(BaseModel):
    """A single user query to the assistive agent."""

    query_id: str = Field(..., description="Stable unique ID")
    session_id: str = Field(default="", description="Agent session id")
    user_text: str = Field(default="", description="Raw user input")
    project_id: str = Field(default="", description="Optional project scope")
    domain: str = Field(default="", description="Optional domain hint")
    requested_mode: str = Field(default="", description="e.g. explain, next_step, refine")
    created_utc: str = Field(default="")


class AgentResponse(BaseModel):
    """A single agent response with evidence and refs."""

    response_id: str = Field(...)
    query_id: str = Field(default="")
    response_type: str = Field(default="", description="explain_project, next_step, explain_suggestion, etc.")
    title: str = Field(default="")
    answer: str = Field(default="")
    supporting_evidence: list[str] = Field(default_factory=list)
    retrieved_context_refs: list[str] = Field(default_factory=list, description="doc_id or corpus refs")
    graph_refs: list[str] = Field(default_factory=list)
    style_profile_refs: list[str] = Field(default_factory=list)
    suggestion_refs: list[str] = Field(default_factory=list)
    draft_refs: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    used_retrieval: bool = Field(default=False)
    used_llm: bool = Field(default=False)
    created_utc: str = Field(default="")


class AgentSession(BaseModel):
    """A local agent session (conversation scope)."""

    session_id: str = Field(...)
    started_utc: str = Field(default="")
    last_active_utc: str = Field(default="")
    project_scope: str = Field(default="", description="Current project filter")
    domain_scope: str = Field(default="", description="Current domain filter")
    use_llm: bool = Field(default=False)
    use_retrieval: bool = Field(default=True)
    message_history_summary: list[str] = Field(default_factory=list, description="Short summary of turns; not full content")
