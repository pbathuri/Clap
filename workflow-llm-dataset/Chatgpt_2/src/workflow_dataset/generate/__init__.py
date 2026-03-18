"""
Sandboxed multimodal generation scaffolding (M10).

Style-conditioned generation packs, prompt packs, asset plans, and manifests.
Local-only; scaffold-first; no uncontrolled backend execution.
"""

from __future__ import annotations

from workflow_dataset.generate.generate_models import (
    GenerationRequest,
    StylePack,
    PromptPack,
    AssetPlan,
    VariantPlan,
    GenerationManifest,
    GenerationStatus,
)
from workflow_dataset.generate.generation_context import build_generation_context
from workflow_dataset.generate.style_pack_builder import build_style_pack_from_context
from workflow_dataset.generate.prompt_pack_builder import build_prompt_pack
from workflow_dataset.generate.asset_plan_builder import build_asset_plan
from workflow_dataset.generate.variant_plan_builder import build_variant_plan
from workflow_dataset.generate.generation_manifest import build_generation_manifest
from workflow_dataset.generate.sandbox_generation_store import (
    save_generation_request,
    save_style_pack,
    save_prompt_pack,
    save_asset_plan,
    save_variant_plan,
    save_generation_manifest,
    list_generation_requests,
    load_generation_manifest,
    load_prompt_pack,
    load_asset_plan,
    load_style_pack,
    load_packs_for_manifest,
)
from workflow_dataset.generate.backend_registry import (
    get_backend,
    register_backend,
    execute_generation,
    list_backends,
    BackendCapability,
    BackendMeta,
    ExecutionMode,
)
from workflow_dataset.generate import backends  # noqa: F401  # register document + image_demo

__all__ = [
    "GenerationRequest",
    "StylePack",
    "PromptPack",
    "AssetPlan",
    "VariantPlan",
    "GenerationManifest",
    "GenerationStatus",
    "build_generation_context",
    "build_style_pack_from_context",
    "build_prompt_pack",
    "build_asset_plan",
    "build_variant_plan",
    "build_generation_manifest",
    "save_generation_request",
    "save_style_pack",
    "save_prompt_pack",
    "save_asset_plan",
    "save_variant_plan",
    "save_generation_manifest",
    "list_generation_requests",
    "load_generation_manifest",
    "load_prompt_pack",
    "load_asset_plan",
    "load_style_pack",
    "load_packs_for_manifest",
    "get_backend",
    "register_backend",
    "execute_generation",
    "list_backends",
    "BackendCapability",
    "BackendMeta",
    "ExecutionMode",
]
