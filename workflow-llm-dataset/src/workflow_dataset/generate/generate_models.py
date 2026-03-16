"""
Pydantic models for sandboxed multimodal generation scaffolding (M10).

Generation requests, style packs, prompt packs, asset plans, variant plans, manifests.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GenerationStatus(str, Enum):
    """Status of a generation request."""

    PLANNED_ONLY = "planned_only"
    PROMPT_PACK_ONLY = "prompt_pack_only"
    BACKEND_READY = "backend_ready"
    BACKEND_EXECUTED = "backend_executed"
    BACKEND_FAILED = "backend_failed"
    ERROR = "error"
    SKIPPED = "skipped"


class BackendExecutionRecord(BaseModel):
    """Record of a single backend execution run. Auditable, local-only."""

    record_id: str = Field(default="")
    backend_name: str = Field(default="")
    backend_version: str = Field(default="")
    execution_status: str = Field(default="", description="success | failed | partial")
    generated_output_paths: list[str] = Field(default_factory=list)
    execution_log: list[str] = Field(default_factory=list)
    error_message: str = Field(default="")
    used_llm: bool = Field(default=False)
    used_fallback: bool = Field(default=False)
    executed_utc: str = Field(default="")


class GenerationRequest(BaseModel):
    """A request to produce generation scaffolding (style pack, prompt pack, asset plan)."""

    generation_id: str = Field(..., description="Stable unique ID")
    session_id: str = Field(default="")
    project_id: str = Field(default="")
    domain: str = Field(default="", description="creative, design, finance, ops, etc.")
    generation_type: str = Field(default="", description="image_pack, shot_plan, design_variant, report_variant, etc.")
    source_ref: str = Field(default="", description="draft_id, suggestion_id, or query ref")
    source_type: str = Field(default="", description="draft | suggestion | project | query")
    use_style_profile: bool = Field(default=True)
    use_imitation_candidate: bool = Field(default=True)
    use_llm: bool = Field(default=False)
    status: GenerationStatus = Field(default=GenerationStatus.PLANNED_ONLY)
    created_utc: str = Field(default="")


class StylePack(BaseModel):
    """Generation-facing style profile derived from observed patterns."""

    style_pack_id: str = Field(...)
    project_id: str = Field(default="")
    domain: str = Field(default="")
    style_profile_refs: list[str] = Field(default_factory=list)
    imitation_candidate_refs: list[str] = Field(default_factory=list)
    naming_patterns: list[str] = Field(default_factory=list)
    layout_patterns: list[str] = Field(default_factory=list)
    artifact_bundle_patterns: list[str] = Field(default_factory=list)
    export_patterns: list[str] = Field(default_factory=list)
    revision_patterns: list[str] = Field(default_factory=list)
    tone_or_visual_hints: list[str] = Field(default_factory=list, description="Evidence-based only")
    deliverable_shapes: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")


class PromptPack(BaseModel):
    """Structured prompts for generation (image, keyframe, storyboard, etc.)."""

    prompt_pack_id: str = Field(...)
    generation_id: str = Field(default="")
    prompt_family: str = Field(default="", description="image, keyframe, storyboard, report_narrative, etc.")
    prompt_text: str = Field(default="")
    negative_constraints: list[str] = Field(default_factory=list)
    structural_constraints: list[str] = Field(default_factory=list)
    style_pack_refs: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")


class ShotItem(BaseModel):
    """Single shot or keyframe in a plan."""

    shot_id: str = Field(default="")
    title: str = Field(default="")
    description: str = Field(default="")
    sequence_order: int = Field(default=0)
    prompt_ref: str = Field(default="")


class SceneItem(BaseModel):
    """Scene or section in a plan."""

    scene_id: str = Field(default="")
    title: str = Field(default="")
    items: list[str] = Field(default_factory=list)


class DesignVariant(BaseModel):
    """A design or report variant in a plan."""

    variant_id: str = Field(default="")
    name: str = Field(default="")
    description: str = Field(default="")
    output_family: str = Field(default="")
    constraints: list[str] = Field(default_factory=list)


class AssetPlan(BaseModel):
    """Plan of target outputs, assets, shots, and file targets."""

    asset_plan_id: str = Field(...)
    generation_id: str = Field(default="")
    target_outputs: list[str] = Field(default_factory=list, description="Output family or type labels")
    required_assets: list[str] = Field(default_factory=list)
    optional_assets: list[str] = Field(default_factory=list)
    shot_list: list[ShotItem] = Field(default_factory=list)
    scene_list: list[SceneItem] = Field(default_factory=list)
    design_variants: list[DesignVariant] = Field(default_factory=list)
    filenames: list[str] = Field(default_factory=list)
    folder_targets: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")


class VariantPlan(BaseModel):
    """Plan for document/report/dashboard variants."""

    variant_plan_id: str = Field(...)
    generation_id: str = Field(default="")
    variant_type: str = Field(default="", description="report, dashboard, workbook, presentation")
    variants: list[DesignVariant] = Field(default_factory=list)
    narrative_outline: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")


class GenerationManifest(BaseModel):
    """Manifest of a generation run: packs, plans, workspace, backend status, execution records."""

    manifest_id: str = Field(...)
    generation_id: str = Field(default="")
    workspace_path: str = Field(default="")
    style_pack_refs: list[str] = Field(default_factory=list)
    prompt_pack_refs: list[str] = Field(default_factory=list)
    asset_plan_refs: list[str] = Field(default_factory=list)
    variant_plan_refs: list[str] = Field(default_factory=list)
    backend_requested: str = Field(default="")
    backend_executed: str = Field(default="")
    status: GenerationStatus = Field(default=GenerationStatus.PROMPT_PACK_ONLY)
    created_utc: str = Field(default="")
    # M11: backend execution records and generated outputs
    execution_records: list[BackendExecutionRecord] = Field(default_factory=list)
    generated_output_paths: list[str] = Field(default_factory=list)
    # In-memory refs for convenience (not always persisted in same file)
    prompt_packs: list[PromptPack] = Field(default_factory=list)
    asset_plans: list[AssetPlan] = Field(default_factory=list)
    style_packs: list[StylePack] = Field(default_factory=list)
