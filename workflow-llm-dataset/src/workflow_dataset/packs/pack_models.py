"""
M22: Full capability pack manifest schema and validation. Aligns with CAPABILITY_PACK_MANIFEST and safe recipe model.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PackManifest(BaseModel):
    """Full capability pack manifest for install and resolution."""

    pack_id: str = Field(default="")
    name: str = Field(default="")
    version: str = Field(default="0.1.0")
    description: str = Field(default="")
    # Role/domain tags for resolution
    role_tags: list[str] = Field(default_factory=list, description="e.g. ops, analyst")
    industry_tags: list[str] = Field(default_factory=list)
    workflow_tags: list[str] = Field(default_factory=list, description="e.g. reporting, simulation")
    task_tags: list[str] = Field(default_factory=list, description="e.g. summarize, scaffold")
    # Modes and models
    supported_modes: list[str] = Field(default_factory=list, description="baseline, adapter, retrieval, adapter_retrieval")
    required_models: list[str] = Field(default_factory=list)
    recommended_models: list[str] = Field(default_factory=list)
    # Config
    retrieval_profile: dict[str, Any] = Field(default_factory=dict, description="top_k, corpus_filter, etc.")
    prompts: list[dict[str, Any]] = Field(default_factory=list)
    templates: list[str] = Field(default_factory=list, description="workflow/task template ids")
    output_adapters: list[str] = Field(default_factory=list)
    parser_profiles: list[str] = Field(default_factory=list)
    optional_wrappers: list[str] = Field(default_factory=list, description="e.g. ollama_ref")
    # Recipe and safety
    recipe_steps: list[dict[str, Any]] = Field(default_factory=list, description="Declarative steps only")
    safety_policies: dict[str, Any] = Field(
        default_factory=lambda: {"sandbox_only": True, "require_apply_confirm": True, "no_network_default": True}
    )
    safety_constraints: list[str] = Field(default_factory=list)
    hardware_constraints: list[str] = Field(default_factory=list, description="e.g. macos, linux, cpu, gpu")
    # Legacy/compat
    workflow_templates: list[str] = Field(default_factory=list)
    evaluation_tasks: list[str] = Field(default_factory=list)
    retrieval_config: dict[str, Any] = Field(default_factory=dict)
    parser_config: dict[str, Any] = Field(default_factory=dict)
    orchestration: dict[str, Any] = Field(default_factory=dict)
    release_modes: list[str] = Field(default_factory=list)
    # Provenance
    license: str = Field(default="")
    source_repo: str = Field(default="")
    role_industry_workflow_tags: list[str] = Field(default_factory=list)
    installer_recipes: list[dict[str, Any]] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    supported_os_hardware: list[str] = Field(default_factory=list)
    # Optional signature/checksum for future verification
    signature_metadata: dict[str, Any] = Field(default_factory=dict)


def validate_pack_manifest(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate dict against PackManifest and safety policy. Return (valid, errors)."""
    errors: list[str] = []
    if not data.get("pack_id"):
        errors.append("pack_id is required")
    if not data.get("name"):
        errors.append("name is required")
    if not data.get("version"):
        errors.append("version is required")
    try:
        manifest = PackManifest.model_validate(data)
        sp = manifest.safety_policies
        if sp.get("sandbox_only") is False:
            errors.append("safety_policies.sandbox_only must not be false")
        if sp.get("require_apply_confirm") is False:
            errors.append("safety_policies.require_apply_confirm must not be false")
        if sp.get("no_network_default") is False:
            errors.append("safety_policies.no_network_default must not be false")
    except Exception as e:
        errors.append(str(e))
    return len(errors) == 0, errors
