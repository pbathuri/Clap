"""
M12: Models for generated output review, refinement, variant management, and adoption.

Local-only; no cloud; auditability preserved.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratedArtifactReview(BaseModel):
    """Review metadata for a generated artifact (preview, provenance, backend)."""

    review_id: str = Field(default="")
    generation_id: str = Field(default="")
    artifact_id: str = Field(default="")
    artifact_type: str = Field(default="", description="markdown, html, text, json, csv")
    preview_path: str = Field(default="", description="Absolute path to artifact file")
    summary: str = Field(default="")
    provenance_refs: list[str] = Field(default_factory=list)
    style_pack_refs: list[str] = Field(default_factory=list)
    prompt_pack_refs: list[str] = Field(default_factory=list)
    backend_used: str = Field(default="")
    used_llm: bool = Field(default=False)
    used_fallback: bool = Field(default=False)
    created_utc: str = Field(default="")


class VariantRecord(BaseModel):
    """A variant of a generated artifact (refined or alternate)."""

    variant_id: str = Field(default="")
    base_artifact_id: str = Field(default="")
    generation_id: str = Field(default="")
    variant_type: str = Field(default="", description="refined, alternate, preferred")
    revision_note: str = Field(default="")
    created_utc: str = Field(default="")
    output_paths: list[str] = Field(default_factory=list)
    used_llm_refinement: bool = Field(default=False)


class RefineRequest(BaseModel):
    """Request to refine a generated document artifact."""

    refine_id: str = Field(default="")
    artifact_id: str = Field(default="")
    generation_id: str = Field(default="")
    refine_mode: str = Field(default="deterministic", description="deterministic | llm")
    use_llm: bool = Field(default=False)
    style_constraints: list[str] = Field(default_factory=list)
    structural_constraints: list[str] = Field(default_factory=list)
    user_instruction: str = Field(default="")
    created_utc: str = Field(default="")


class AdoptionCandidate(BaseModel):
    """Generated outputs selected for adoption into apply flow."""

    adoption_id: str = Field(default="")
    artifact_id: str = Field(default="")
    generation_id: str = Field(default="")
    workspace_path: str = Field(default="", description="Generation sandbox workspace path")
    candidate_paths: list[str] = Field(default_factory=list, description="Relative paths in workspace")
    target_project_id: str = Field(default="")
    ready_for_apply: bool = Field(default=False)
    created_utc: str = Field(default="")
