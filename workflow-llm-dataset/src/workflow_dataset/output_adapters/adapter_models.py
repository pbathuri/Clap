"""
M13: Models for toolchain-native output adapters and bundles.

Local-only; sandbox-first; adoptable via existing apply flow.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class OutputAdapterRequest(BaseModel):
    """Request to produce a toolchain-native output bundle from a reviewed/refined artifact."""

    adapter_request_id: str = Field(default="")
    generation_id: str = Field(default="")
    review_id: str = Field(default="")
    artifact_id: str = Field(default="")
    project_id: str = Field(default="")
    domain: str = Field(default="", description="creative, design, finance, ops")
    adapter_type: str = Field(default="", description="spreadsheet, creative_package, design_package, ops_handoff")
    source_artifact_path: str = Field(default="")
    workspace_path: str = Field(default="")
    created_utc: str = Field(default="")


class OutputBundle(BaseModel):
    """A toolchain-native output bundle produced by an adapter."""

    bundle_id: str = Field(default="")
    adapter_request_id: str = Field(default="")
    bundle_type: str = Field(default="")
    workspace_path: str = Field(default="")
    output_paths: list[str] = Field(default_factory=list, description="Relative paths in workspace")
    manifest_path: str = Field(default="")
    created_utc: str = Field(default="")


class OutputBundleManifest(BaseModel):
    """Manifest for an output bundle: provenance, paths, adapter used. M14: population flags."""

    manifest_id: str = Field(default="")
    bundle_id: str = Field(default="")
    source_artifact_refs: list[str] = Field(default_factory=list)
    generated_paths: list[str] = Field(default_factory=list)
    adapter_used: str = Field(default="")
    style_profile_refs: list[str] = Field(default_factory=list)
    revision_note: str = Field(default="")
    created_utc: str = Field(default="")
    # M14: content population and provenance
    populated_paths: list[str] = Field(default_factory=list, description="Paths that were content-populated from source")
    scaffold_only_paths: list[str] = Field(default_factory=list, description="Paths that are scaffold/template only")
    fallback_used: bool = Field(default=False, description="True if source was weak and scaffold fallback was used")
    xlsx_created: bool = Field(default=False, description="True if optional XLSX workbook was written")
    population_result_ref: str = Field(default="", description="Optional ref to population result id for audit")
