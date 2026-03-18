"""
M25E–M25H: Behavior resolution engine — which pack behavior applies for a task, why, precedence, exclusions.
Explicit and explainable; does not bypass trust/approval/runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_resolution_graph import resolve_with_priority
from workflow_dataset.packs.pack_activation import get_current_context
from workflow_dataset.packs.pack_state import get_packs_dir, get_active_role
from workflow_dataset.packs.behavior_models import (
    PackPromptAsset,
    PackTaskDefaults,
    PackRetrievalProfilePreset,
    PackOutputProfilePreset,
    ParserOutputHint,
    ResolvedBehavior,
    BehaviorResolutionResult,
    RETRIEVAL_PROFILE_ALLOWED_KEYS,
    OUTPUT_PROFILE_ALLOWED_KEYS,
)
from workflow_dataset.packs.behavior_assets import (
    get_prompt_assets_from_manifest,
    get_task_defaults_from_manifest,
    get_retrieval_profile_presets_from_manifest,
    get_output_profile_presets_from_manifest,
    get_parser_output_hints_from_manifest,
)


def _packs_dir(packs_dir: Path | str | None) -> Path:
    if packs_dir is not None:
        return Path(packs_dir).resolve()
    return get_packs_dir()


def _task_matches(default: PackTaskDefaults, task_id: str | None, workflow_id: str | None) -> bool:
    if not task_id and not workflow_id:
        return True
    if task_id and default.task_id and (task_id.lower() == default.task_id.lower()):
        return True
    if task_id and not default.task_id and not default.workflow_id:
        return True
    if workflow_id and default.workflow_id and (workflow_id.lower() == default.workflow_id.lower()):
        return True
    if task_id and default.task_id:
        return task_id.lower() == default.task_id.lower()
    return False


def _key_matches(asset: PackPromptAsset, task_id: str | None, workflow_id: str | None) -> bool:
    if not asset.key:
        return True
    if task_id and task_id.lower() == asset.key.lower():
        return True
    if workflow_id and workflow_id.lower() == asset.key.lower():
        return True
    return False


def _retrieval_preset_matches(p: PackRetrievalProfilePreset, task_id: str | None, workflow_id: str | None) -> bool:
    if not task_id and not workflow_id:
        return True
    if task_id and p.task_id and task_id.lower() == p.task_id.lower():
        return True
    if workflow_id and p.workflow_id and workflow_id.lower() == p.workflow_id.lower():
        return True
    if not p.task_id and not p.workflow_id:
        return True
    return False


def _output_preset_matches(p: PackOutputProfilePreset, task_id: str | None, workflow_id: str | None) -> bool:
    if not task_id and not workflow_id:
        return True
    if task_id and p.task_id and task_id.lower() == p.task_id.lower():
        return True
    if workflow_id and p.workflow_id and workflow_id.lower() == p.workflow_id.lower():
        return True
    if not p.task_id and not p.workflow_id:
        return True
    return False


def _preset_to_retrieval_dict(p: PackRetrievalProfilePreset) -> dict[str, Any]:
    """Convert preset to dict with only allowed keys."""
    out: dict[str, Any] = {}
    if p.top_k > 0:
        out["top_k"] = p.top_k
    if p.corpus_filter:
        out["corpus_filter"] = p.corpus_filter
    if p.max_tokens > 0:
        out["max_tokens"] = p.max_tokens
    if p.min_score > 0:
        out["min_score"] = p.min_score
    if p.rerank:
        out["rerank"] = True
    if p.include_metadata:
        out["include_metadata"] = True
    for k, v in p.extra.items():
        if k in RETRIEVAL_PROFILE_ALLOWED_KEYS:
            out[k] = v
    return out


def _preset_to_output_dict(p: PackOutputProfilePreset) -> dict[str, Any]:
    """Convert preset to dict for output profile. Only allowed keys (M25H.1)."""
    out: dict[str, Any] = {}
    if p.adapter:
        out["adapter"] = p.adapter
    if p.format_hint:
        out["format_hint"] = p.format_hint
    if p.max_length_hint > 0:
        out["max_length_hint"] = p.max_length_hint
    if p.sections_hint:
        out["sections_hint"] = p.sections_hint
    for k, v in p.extra.items():
        if k in OUTPUT_PROFILE_ALLOWED_KEYS:
            out[k] = v
    return out


def resolve_behavior_for_task(
    task_id: str | None = None,
    workflow_id: str | None = None,
    role: str | None = None,
    packs_dir: Path | str | None = None,
) -> BehaviorResolutionResult:
    """
    Resolve which pack behavior applies for the given task/workflow/role.
    Returns resolved prompt assets, task defaults, winning pack, exclusions, and explanation.
    Precedence: pinned > primary > secondary (first wins for single-value; lists merged with precedence order).
    """
    root = _packs_dir(packs_dir)
    ctx = get_current_context(root)
    active_role = role or ctx.get("current_role") or get_active_role(root)
    active_workflow = workflow_id or ctx.get("current_workflow")
    active_task = task_id or ctx.get("current_task")

    cap, expl = resolve_with_priority(
        role=active_role,
        workflow_type=active_workflow,
        task_type=active_task,
        packs_dir=root,
    )

    # Order: pinned first, then primary, then secondary
    ordered_packs: list[tuple[str, str]] = []  # (pack_id, role) pinned=0, primary=1, secondary=2
    if expl.pinned_packs:
        for pid in expl.pinned_packs:
            ordered_packs.append((pid, "pinned"))
    if expl.primary_pack_id and expl.primary_pack_id not in [p[0] for p in ordered_packs]:
        ordered_packs.append((expl.primary_pack_id, "primary"))
    for pid in expl.secondary_pack_ids:
        if pid not in [p[0] for p in ordered_packs]:
            ordered_packs.append((pid, "secondary"))

    # Collect prompt assets, task defaults, retrieval/output presets, parser hints from active packs (in precedence order)
    all_assets: list[PackPromptAsset] = []
    all_defaults: list[PackTaskDefaults] = []
    all_retrieval_presets: list[PackRetrievalProfilePreset] = []
    all_output_presets: list[PackOutputProfilePreset] = []
    all_parser_hints: list[ParserOutputHint] = []
    for pack in cap.active_packs:
        assets = get_prompt_assets_from_manifest(pack)
        defaults = get_task_defaults_from_manifest(pack)
        for a in assets:
            a.pack_id = pack.pack_id
            all_assets.append(a)
        for d in defaults:
            d.pack_id = pack.pack_id
            all_defaults.append(d)
        for r in get_retrieval_profile_presets_from_manifest(pack):
            r.pack_id = pack.pack_id
            all_retrieval_presets.append(r)
        for o in get_output_profile_presets_from_manifest(pack):
            o.pack_id = pack.pack_id
            all_output_presets.append(o)
        for h in get_parser_output_hints_from_manifest(pack):
            h.pack_id = pack.pack_id
            all_parser_hints.append(h)

    # Filter by task/workflow
    task_id_f = active_task or task_id
    workflow_id_f = active_workflow or workflow_id
    assets_for_scope = [a for a in all_assets if _key_matches(a, task_id_f, workflow_id_f)]
    defaults_for_scope = [d for d in all_defaults if _task_matches(d, task_id_f, workflow_id_f)]

    # Single-value: winning pack is first in precedence order that has a value
    winning_pack_id = ""
    winning_defaults: PackTaskDefaults | None = None
    for pid, role in ordered_packs:
        for d in defaults_for_scope:
            if d.pack_id == pid and (d.preferred_adapter or d.preferred_model_class or d.preferred_output_mode):
                winning_pack_id = pid
                winning_defaults = d
                break
        if winning_defaults:
            break
    if not winning_defaults and defaults_for_scope:
        winning_defaults = defaults_for_scope[0]
        winning_pack_id = winning_defaults.pack_id

    # Merge prompt assets: all from contributing packs, ordered by precedence (pinned first, then primary, then secondary)
    contributing_ids = list(dict.fromkeys(a.pack_id for a in assets_for_scope))
    ordered_assets: list[PackPromptAsset] = []
    for pid, _ in ordered_packs:
        for a in assets_for_scope:
            if a.pack_id == pid:
                ordered_assets.append(a)
    for a in assets_for_scope:
        if a.pack_id not in [x.pack_id for x in ordered_assets]:
            ordered_assets.append(a)

    # M25H.1: Resolve retrieval profile preset (first in precedence order that matches scope)
    retrieval_for_scope = [r for r in all_retrieval_presets if _retrieval_preset_matches(r, task_id_f, workflow_id_f)]
    output_for_scope = [o for o in all_output_presets if _output_preset_matches(o, task_id_f, workflow_id_f)]
    retrieval_profile: dict[str, Any] = {}
    output_profile: dict[str, Any] = {}
    retrieval_source = ""
    output_source = ""
    retrieval_preset_id = ""
    output_preset_id = ""
    scope_str = f"task={task_id_f or '(any)'} workflow={workflow_id_f or '(any)'}"
    why_retrieval = ""
    why_output = ""
    for pid, role in ordered_packs:
        for r in retrieval_for_scope:
            if r.pack_id == pid and _preset_to_retrieval_dict(r):
                retrieval_profile = _preset_to_retrieval_dict(r)
                retrieval_source = pid
                retrieval_preset_id = r.preset_id or "(unnamed)"
                why_retrieval = f"Applied retrieval preset '{retrieval_preset_id}' from pack {pid} ({role}). Scope: {scope_str}."
                break
        if retrieval_profile:
            break
    if not why_retrieval and retrieval_for_scope:
        r0 = retrieval_for_scope[0]
        retrieval_profile = _preset_to_retrieval_dict(r0)
        retrieval_source = r0.pack_id
        retrieval_preset_id = r0.preset_id or "(unnamed)"
        why_retrieval = f"Applied retrieval preset '{retrieval_preset_id}' from pack {r0.pack_id} (first matching; no precedence override). Scope: {scope_str}."
    for pid, role in ordered_packs:
        for o in output_for_scope:
            if o.pack_id == pid and _preset_to_output_dict(o):
                output_profile = _preset_to_output_dict(o)
                output_source = pid
                output_preset_id = o.preset_id or "(unnamed)"
                why_output = f"Applied output preset '{output_preset_id}' from pack {pid} ({role}). Scope: {scope_str}."
                break
        if output_profile:
            break
    if not why_output and output_for_scope:
        o0 = output_for_scope[0]
        output_profile = _preset_to_output_dict(o0)
        output_source = o0.pack_id
        output_preset_id = o0.preset_id or "(unnamed)"
        why_output = f"Applied output preset '{output_preset_id}' from pack {o0.pack_id} (first matching; no precedence override). Scope: {scope_str}."
    # Parser/output hints: merge in precedence order (no overwrite of same key)
    parser_hints_for_scope: list[ParserOutputHint] = []
    seen_keys: set[tuple[str, str]] = set()
    for pid, _ in ordered_packs:
        for h in all_parser_hints:
            if h.pack_id != pid:
                continue
            if not h.key or (task_id_f and task_id_f.lower() == h.key.lower()) or (workflow_id_f and workflow_id_f.lower() == h.key.lower()):
                key = (h.key or "(any)", h.preferred_format or h.bullet_preference or "")
                if key not in seen_keys:
                    seen_keys.add(key)
                    parser_hints_for_scope.append(h)

    resolved = ResolvedBehavior(
        task_id=task_id_f or "",
        workflow_id=workflow_id_f or "",
        prompt_assets=ordered_assets,
        task_defaults=winning_defaults,
        retrieval_profile=retrieval_profile,
        output_profile=output_profile,
        parser_output_hints=parser_hints_for_scope,
        winning_pack_id=winning_pack_id,
        retrieval_profile_source_pack=retrieval_source,
        output_profile_source_pack=output_source,
        retrieval_profile_preset_id=retrieval_preset_id,
        output_profile_preset_id=output_preset_id,
        contributing_pack_ids=contributing_ids,
        excluded_pack_ids=list(expl.excluded_pack_ids),
        exclusion_reasons={},
        conflict_summary="; ".join(f"{c.conflict_class.value}: {c.capability}" for c in expl.conflicts) if expl.conflicts else "",
        why_retrieval_profile=why_retrieval,
        why_output_profile=why_output,
    )

    why_winning = ""
    if winning_pack_id:
        for pid, role in ordered_packs:
            if pid == winning_pack_id:
                why_winning = f"{role} pack {winning_pack_id} supplies task defaults for task={task_id_f or '(any)'} workflow={workflow_id_f or '(any)'}"
                break
    if not why_winning and ordered_packs:
        why_winning = f"Active packs {[p[0] for p in ordered_packs]}; no task_defaults matched. Merged prompt assets from contributing packs."

    why_excluded: list[str] = []
    for pid in expl.excluded_pack_ids:
        why_excluded.append(f"{pid}: excluded (suspended or conflict-blocked)")

    return BehaviorResolutionResult(
        resolved=resolved,
        active_pack_ids=[m.pack_id for m in cap.active_packs],
        primary_pack_id=expl.primary_pack_id or "",
        pinned_pack_id=expl.pinned_packs[0] if expl.pinned_packs else "",
        secondary_pack_ids=list(expl.secondary_pack_ids),
        why_winning=why_winning,
        why_excluded=why_excluded,
        conflicts=[f"{c.conflict_class.value}: {c.capability} ({c.pack_ids})" for c in expl.conflicts],
    )


def get_active_behavior_summary(packs_dir: Path | str | None = None) -> dict[str, Any]:
    """Return a summary of currently active behavior (for mission control): overrides, prompt source, excluded, why."""
    result = resolve_behavior_for_task(packs_dir=packs_dir)
    r = result.resolved
    return {
        "task_id": r.task_id,
        "workflow_id": r.workflow_id,
        "winning_pack_id": result.resolved.winning_pack_id,
        "active_pack_ids": result.active_pack_ids,
        "primary_pack_id": result.primary_pack_id,
        "pinned_pack_id": result.pinned_pack_id,
        "prompt_asset_count": len(r.prompt_assets),
        "prompt_asset_sources": list(dict.fromkeys(a.pack_id for a in r.prompt_assets)),
        "task_defaults": {
            "preferred_adapter": r.task_defaults.preferred_adapter if r.task_defaults else "",
            "preferred_model_class": r.task_defaults.preferred_model_class if r.task_defaults else "",
            "preferred_output_mode": r.task_defaults.preferred_output_mode if r.task_defaults else "",
            "source_pack": r.winning_pack_id,
        } if r.task_defaults else {},
        "retrieval_profile": r.retrieval_profile,
        "output_profile": r.output_profile,
        "retrieval_profile_source_pack": r.retrieval_profile_source_pack,
        "output_profile_source_pack": r.output_profile_source_pack,
        "retrieval_profile_preset_id": getattr(r, "retrieval_profile_preset_id", "") or "",
        "output_profile_preset_id": getattr(r, "output_profile_preset_id", "") or "",
        "why_retrieval_profile": r.why_retrieval_profile,
        "why_output_profile": r.why_output_profile,
        "parser_output_hints_count": len(r.parser_output_hints),
        "excluded_pack_ids": r.excluded_pack_ids,
        "exclusion_reasons": r.exclusion_reasons,
        "conflict_summary": r.conflict_summary,
        "why_current_behavior": result.why_winning,
        "conflicts": result.conflicts,
        "why_excluded": result.why_excluded,
    }
