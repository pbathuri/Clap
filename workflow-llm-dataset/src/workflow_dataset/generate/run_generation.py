"""
Orchestrate a full generation plan: context -> style pack -> prompt packs -> asset plan -> manifest.

Used by CLI and operator console. Sandbox-only; no uncontrolled execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

from workflow_dataset.generate.generate_models import (
    GenerationRequest,
    GenerationStatus,
    StylePack,
    PromptPack,
    AssetPlan,
    VariantPlan,
    GenerationManifest,
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
)
from workflow_dataset.generate.generate_graph import persist_generation_to_graph


def run_generation_plan(
    graph_path: Path | str,
    style_signals_dir: Path | str,
    parsed_artifacts_dir: Path | str,
    style_profiles_dir: Path | str,
    suggestions_dir: Path | str,
    draft_structures_dir: Path | str,
    generation_workspace_root: Path | str,
    setup_session_id: str = "",
    project_id: str = "",
    domain: str = "",
    source_ref: str = "",
    source_type: str = "project",
    generation_type: str = "image_pack",
    use_llm: bool = False,
    allow_style_packs: bool = True,
    allow_prompt_packs: bool = True,
    allow_asset_plans: bool = True,
    persist_to_graph: bool = True,
) -> tuple[GenerationRequest, GenerationManifest, str]:
    """
    Build generation context, style pack, prompt packs, asset plan, variant plan, manifest.
    Persist all under generation_workspace_root and optionally to graph.
    Returns (request, manifest, workspace_path). workspace_path is the created workspace dir.
    """
    ts = utc_now_iso()
    generation_id = stable_id("gen", setup_session_id or "session", project_id or "proj", source_ref or generation_type, ts, prefix="gen")

    context = build_generation_context(
        graph_path=graph_path,
        style_signals_dir=style_signals_dir,
        parsed_artifacts_dir=parsed_artifacts_dir,
        style_profiles_dir=style_profiles_dir,
        suggestions_dir=suggestions_dir,
        draft_structures_dir=draft_structures_dir,
        setup_session_id=setup_session_id,
        project_id=project_id,
        domain_filter=domain,
    )

    request = GenerationRequest(
        generation_id=generation_id,
        session_id=setup_session_id,
        project_id=project_id,
        domain=domain,
        generation_type=generation_type,
        source_ref=source_ref,
        source_type=source_type,
        use_style_profile=allow_style_packs,
        use_imitation_candidate=allow_style_packs,
        use_llm=use_llm,
        status=GenerationStatus.PROMPT_PACK_ONLY,
        created_utc=ts,
    )

    root = Path(generation_workspace_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    workspace_path = root / generation_id
    workspace_path.mkdir(parents=True, exist_ok=True)

    style_packs: list[StylePack] = []
    if allow_style_packs:
        sp = build_style_pack_from_context(context, project_id=project_id, domain=domain)
        style_packs.append(sp)
        save_style_pack(sp, root)
    save_generation_request(request, root)

    prompt_packs: list[PromptPack] = []
    if allow_prompt_packs:
        for family in _prompt_families_for_type(generation_type, context):
            pp = build_prompt_pack(
                generation_id=generation_id,
                prompt_family=family,
                context=context,
                style_pack=style_packs[0] if style_packs else None,
                draft_ref=source_ref if source_type == "draft" else "",
                suggestion_ref=source_ref if source_type == "suggestion" else "",
            )
            prompt_packs.append(pp)
            save_prompt_pack(pp, root)

    asset_plans: list[AssetPlan] = []
    if allow_asset_plans:
        ap = build_asset_plan(
            generation_id=generation_id,
            context=context,
            style_pack=style_packs[0] if style_packs else None,
            generation_type=generation_type,
        )
        asset_plans.append(ap)
        save_asset_plan(ap, root)

    variant_plans: list[VariantPlan] = []
    vt = _variant_type_for_generation(generation_type, context)
    if vt:
        vp = build_variant_plan(generation_id=generation_id, context=context, variant_type=vt, style_pack=style_packs[0] if style_packs else None)
        variant_plans.append(vp)
        save_variant_plan(vp, root)

    manifest = build_generation_manifest(
        request=request,
        workspace_path=workspace_path,
        style_packs=style_packs,
        prompt_packs=prompt_packs,
        asset_plans=asset_plans,
        variant_plans=variant_plans,
        backend_requested="",
        backend_executed="",
    )
    save_generation_manifest(manifest, root)

    if persist_to_graph:
        persist_generation_to_graph(
            graph_path,
            request=request,
            style_packs=style_packs,
            prompt_packs=prompt_packs,
            asset_plans=asset_plans,
            manifest=manifest,
            project_id=project_id,
        )

    return request, manifest, str(workspace_path)


def _prompt_families_for_type(generation_type: str, context: dict[str, Any]) -> list[str]:
    """Return prompt families to build for this generation type."""
    if generation_type in ("image_pack", "creative", "design"):
        return ["image", "keyframe", "storyboard"]
    if generation_type in ("report_variant", "finance", "ops"):
        return ["report_narrative", "presentation"]
    if generation_type == "shot_plan":
        return ["storyboard", "keyframe"]
    return ["image", "report_narrative"]


def _variant_type_for_generation(generation_type: str, context: dict[str, Any]) -> str:
    """Return variant type for variant plan, or empty if none."""
    if generation_type in ("report_variant", "finance", "ops"):
        return "report"
    if generation_type == "dashboard":
        return "dashboard"
    if generation_type == "workbook":
        return "workbook"
    if generation_type in ("presentation", "design"):
        return "presentation"
    return ""
