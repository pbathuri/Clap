"""
Pydantic models for sandboxed artifact materialization (M7).

Used by workspace manager, artifact builder, manifest store, and CLI.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MaterializationRequest(BaseModel):
    """A request to materialize outputs in the sandbox."""

    request_id: str = Field(..., description="Stable unique ID")
    session_id: str = Field(default="", description="Agent/setup session")
    project_id: str = Field(default="", description="Project scope")
    source_type: str = Field(default="", description="suggestion | draft | query")
    source_ref: str = Field(default="", description="suggestion_id, draft_id, or query ref")
    materialization_mode: str = Field(default="sandbox", description="sandbox only for M7")
    output_family: str = Field(default="", description="text | table | folder_scaffold | creative_scaffold")
    created_utc: str = Field(default="")


class MaterializedArtifact(BaseModel):
    """A single materialized output artifact in the sandbox."""

    artifact_id: str = Field(...)
    request_id: str = Field(default="")
    project_id: str = Field(default="")
    artifact_type: str = Field(default="", description="e.g. markdown_brief, csv_tracker")
    sandbox_path: str = Field(default="", description="Relative or absolute path inside workspace")
    manifest_path: str = Field(default="", description="Path to manifest if stored separately")
    title: str = Field(default="")
    summary: str = Field(default="")
    provenance_refs: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")


class MaterializationManifest(BaseModel):
    """Manifest of a materialization run: outputs, provenance, and flags."""

    manifest_id: str = Field(...)
    request_id: str = Field(default="")
    output_paths: list[str] = Field(default_factory=list, description="Paths written in workspace")
    generated_from: str = Field(default="", description="draft_type, suggestion_id, or query")
    style_profile_refs: list[str] = Field(default_factory=list)
    suggestion_refs: list[str] = Field(default_factory=list)
    draft_refs: list[str] = Field(default_factory=list)
    llm_used: bool = Field(default=False)
    retrieval_used: bool = Field(default=False)
    created_utc: str = Field(default="")
    artifacts: list[MaterializedArtifact] = Field(default_factory=list)
