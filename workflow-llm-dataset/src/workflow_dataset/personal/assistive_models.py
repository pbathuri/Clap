"""
Typed models for the style-aware assistive loop.

Used by style_suggestion_engine, draft_structure_engine, graph persistence, and CLI.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StyleAwareSuggestion(BaseModel):
    """A single style-aware suggestion; stored locally, never executed without user approval."""

    suggestion_id: str = Field(..., description="Stable unique ID")
    suggestion_type: str = Field(..., description="organization | workflow | style | draft_creation")
    project_id: str = Field(default="", description="Project or folder context")
    domain: str = Field(default="", description="creative, design, finance, ops, etc.")
    title: str = Field(default="")
    description: str = Field(default="")
    rationale: str = Field(default="", description="Explainable reason for this suggestion")
    supporting_signals: list[str] | list[dict[str, Any]] = Field(default_factory=list)
    style_profile_refs: list[str] = Field(default_factory=list, description="profile_id refs")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    priority: int = Field(default=0, description="Higher = more salient")
    created_utc: str = Field(default="")
    status: str = Field(default="pending", description="pending | accepted | dismissed")


class DraftStructure(BaseModel):
    """A draft structure or template outline (not final content)."""

    draft_id: str = Field(...)
    draft_type: str = Field(..., description="e.g. project_brief, report_outline, workbook_scaffold")
    project_id: str = Field(default="")
    domain: str = Field(default="")
    title: str = Field(default="")
    structure_outline: str = Field(default="", description="Markdown or bullet outline")
    recommended_sections: list[str] = Field(default_factory=list)
    suggested_naming: list[str] = Field(default_factory=list)
    suggested_assets_or_tables: list[str] = Field(default_factory=list)
    style_profile_refs: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    created_utc: str = Field(default="")
