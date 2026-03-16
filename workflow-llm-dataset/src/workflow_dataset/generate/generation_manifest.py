"""
Build generation manifest from request, style pack, prompt packs, asset plans, variant plans.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

from workflow_dataset.generate.generate_models import (
    GenerationRequest,
    GenerationManifest,
    GenerationStatus,
    StylePack,
    PromptPack,
    AssetPlan,
    VariantPlan,
)


def build_generation_manifest(
    request: GenerationRequest,
    workspace_path: str | Path,
    style_packs: list[StylePack],
    prompt_packs: list[PromptPack],
    asset_plans: list[AssetPlan],
    variant_plans: list[VariantPlan] | None = None,
    backend_requested: str = "",
    backend_executed: str = "",
) -> GenerationManifest:
    """Build a GenerationManifest from request and produced packs/plans."""
    ts = utc_now_iso()
    manifest_id = stable_id("genmanifest", request.generation_id, ts, prefix="gm")
    variant_plans = variant_plans or []

    status = GenerationStatus.PROMPT_PACK_ONLY
    if backend_executed:
        status = GenerationStatus.BACKEND_EXECUTED
    elif backend_requested:
        status = GenerationStatus.BACKEND_READY

    return GenerationManifest(
        manifest_id=manifest_id,
        generation_id=request.generation_id,
        workspace_path=str(Path(workspace_path).resolve()),
        style_pack_refs=[s.style_pack_id for s in style_packs],
        prompt_pack_refs=[p.prompt_pack_id for p in prompt_packs],
        asset_plan_refs=[a.asset_plan_id for a in asset_plans],
        variant_plan_refs=[v.variant_plan_id for v in variant_plans],
        backend_requested=backend_requested,
        backend_executed=backend_executed,
        status=status,
        created_utc=ts,
        prompt_packs=prompt_packs,
        asset_plans=asset_plans,
        style_packs=style_packs,
    )
