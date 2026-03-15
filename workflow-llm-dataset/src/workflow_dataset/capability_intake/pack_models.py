"""
M21: Capability pack manifest model. Local schema only; no cloud marketplace.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PackManifest(BaseModel):
    """Minimal capability pack manifest schema."""

    pack_id: str = Field(default="")
    name: str = Field(default="")
    version: str = Field(default="0.1.0")
    description: str = Field(default="")
    recommended_models: list[str] = Field(default_factory=list)
    prompts: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_config: dict[str, Any] = Field(default_factory=dict)
    parser_config: dict[str, Any] = Field(default_factory=dict)
    workflow_templates: list[str] = Field(default_factory=list)
    evaluation_tasks: list[str] = Field(default_factory=list)
    safety_policies: dict[str, Any] = Field(
        default_factory=lambda: {"sandbox_only": True, "require_apply_confirm": True, "no_network_default": True}
    )
    orchestration: dict[str, Any] = Field(default_factory=dict)
    output_adapters: list[str] = Field(default_factory=list)
    release_modes: list[str] = Field(default_factory=list)
    license: str = Field(default="")
    source_repo: str = Field(default="")
    role_industry_workflow_tags: list[str] = Field(default_factory=list, description="e.g. ops, creative, reporting")
    installer_recipes: list[dict[str, Any]] = Field(default_factory=list, description="Steps to install pack locally")
    dependencies: list[str] = Field(default_factory=list, description="Pack or repo dependencies")
    supported_os_hardware: list[str] = Field(default_factory=list, description="e.g. macos, linux, cpu, gpu")


def validate_pack_manifest(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate dict against PackManifest. Return (valid, list of error messages).
    """
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
