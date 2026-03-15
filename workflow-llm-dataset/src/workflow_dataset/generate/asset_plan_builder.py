"""
Build asset plans: target outputs, required/optional assets, shot list, design variants, filenames.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

from workflow_dataset.generate.generate_models import AssetPlan, ShotItem, SceneItem, DesignVariant, StylePack


def build_asset_plan(
    generation_id: str,
    context: dict[str, Any],
    style_pack: StylePack | None = None,
    generation_type: str = "",
) -> AssetPlan:
    """
    Build an AssetPlan from context and optional style pack.
    Includes target outputs, assets, shot list, scenes, design variants, filenames, folder targets.
    """
    ts = utc_now_iso()
    plan_id = stable_id("assetplan", generation_id, generation_type or "default", ts, prefix="ap")

    summary = context.get("summary") or {}
    drafts = context.get("drafts") or []
    profiles = context.get("style_profiles") or []
    domain = context.get("domain_filter") or (style_pack.domain if style_pack else "")

    target_outputs: list[str] = []
    required_assets: list[str] = []
    optional_assets: list[str] = []
    shot_list: list[ShotItem] = []
    scene_list: list[SceneItem] = []
    design_variants: list[DesignVariant] = []
    filenames: list[str] = []
    folder_targets: list[str] = []

    # From drafts
    for i, d in enumerate(drafts[:10]):
        dtype = getattr(d, "draft_type", "") or "output"
        target_outputs.append(dtype)
        sections = getattr(d, "recommended_sections", None) or []
        for j, sec in enumerate(sections[:8]):
            shot_list.append(ShotItem(
                shot_id=stable_id("shot", plan_id, sec[:30], prefix="shot"),
                title=sec[:80],
                description="",
                sequence_order=len(shot_list) + 1,
                prompt_ref="",
            ))
        naming = getattr(d, "suggested_naming", None) or []
        filenames.extend(naming[:5])
        assets = getattr(d, "suggested_assets_or_tables", None) or []
        required_assets.extend(assets[:5])

    # From style pack
    if style_pack:
        folder_targets.extend(style_pack.layout_patterns[:10])
        if style_pack.deliverable_shapes:
            for ds in style_pack.deliverable_shapes[:5]:
                design_variants.append(DesignVariant(
                    variant_id=stable_id("var", plan_id, ds, prefix="var"),
                    name=ds,
                    description=f"Variant for {ds}",
                    output_family=ds,
                    constraints=[],
                ))
        if style_pack.naming_patterns and not filenames:
            filenames.extend(style_pack.naming_patterns[:5])

    # Domain-specific defaults
    if not target_outputs and domain:
        if domain in ("creative", "design"):
            target_outputs = ["concept", "keyframe", "storyboard", "deliverable_bundle"]
            optional_assets = ["source_assets", "exports", "review_copy"]
        elif domain in ("finance", "ops"):
            target_outputs = ["report", "workbook", "dashboard", "checklist"]
            optional_assets = ["summary_sheet", "detail_sheets", "appendix"]
        else:
            target_outputs = ["document", "output_bundle"]

    if not folder_targets and style_pack:
        folder_targets = [f"output_{i}" for i in range(3)]

    # Scenes from shot list or sections
    if shot_list:
        scene_list.append(SceneItem(
            scene_id=stable_id("scene", plan_id, "main", prefix="scene"),
            title="Main",
            items=[s.shot_id for s in shot_list[:10]],
        ))

    return AssetPlan(
        asset_plan_id=plan_id,
        generation_id=generation_id,
        target_outputs=dedupe(target_outputs, 15),
        required_assets=dedupe(required_assets, 20),
        optional_assets=dedupe(optional_assets, 15),
        shot_list=shot_list[:25],
        scene_list=scene_list[:10],
        design_variants=design_variants[:15],
        filenames=dedupe(filenames, 20),
        folder_targets=dedupe(folder_targets, 15),
        created_utc=ts,
    )


def dedupe(lst: list[str], cap: int = 50) -> list[str]:
    seen: set[str] = set()
    out = []
    for x in lst:
        if x and x not in seen and len(out) < cap:
            seen.add(x)
            out.append(x[:200])
    return out
