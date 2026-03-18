"""
M25E–M25H: Load pack prompt assets and task-level defaults from manifest behavior config.
Manifest-declared; inspectable; safe to disable (omit or empty behavior).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_models import PackManifest
from workflow_dataset.packs.behavior_models import (
    PackPromptAsset,
    PackTaskDefaults,
    PackRetrievalProfilePreset,
    PackOutputProfilePreset,
    ParserOutputHint,
    PROMPT_ASSET_KINDS,
    RETRIEVAL_PROFILE_ALLOWED_KEYS,
    OUTPUT_PROFILE_ALLOWED_KEYS,
    PARSER_OUTPUT_HINT_ALLOWED_KEYS,
)


def _parse_prompt_asset(pack_id: str, raw: dict[str, Any]) -> PackPromptAsset:
    """Parse one prompt asset from manifest."""
    kind = (raw.get("kind") or "task_prompt").strip()
    if kind not in PROMPT_ASSET_KINDS:
        kind = "task_prompt"
    return PackPromptAsset(
        kind=kind,
        key=(raw.get("key") or raw.get("task_id") or raw.get("workflow_id") or "").strip(),
        content=(raw.get("content") or raw.get("text") or "").strip(),
        pack_id=pack_id,
        priority_hint=(raw.get("priority_hint") or "medium").strip(),
    )


def _parse_task_defaults(pack_id: str, raw: dict[str, Any]) -> PackTaskDefaults:
    """Parse one task default from manifest."""
    return PackTaskDefaults(
        task_id=(raw.get("task_id") or "").strip(),
        workflow_id=(raw.get("workflow_id") or "").strip(),
        pack_id=pack_id,
        preferred_adapter=(raw.get("preferred_adapter") or "").strip(),
        preferred_model_class=(raw.get("preferred_model_class") or "").strip(),
        preferred_retrieval_profile=dict(raw.get("preferred_retrieval_profile") or {}),
        preferred_output_mode=(raw.get("preferred_output_mode") or "").strip(),
        execution_mode_hint=(raw.get("execution_mode_hint") or "").strip(),
    )


def get_prompt_assets_from_manifest(manifest: PackManifest) -> list[PackPromptAsset]:
    """Extract prompt assets from manifest.behavior.prompt_assets. Returns empty if not present."""
    behavior = getattr(manifest, "behavior", None) or {}
    if not isinstance(behavior, dict):
        return []
    raw_list = behavior.get("prompt_assets") or behavior.get("prompts_behavior") or []
    out: list[PackPromptAsset] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        out.append(_parse_prompt_asset(manifest.pack_id, item))
    return out


def get_task_defaults_from_manifest(manifest: PackManifest) -> list[PackTaskDefaults]:
    """Extract task-level defaults from manifest.behavior.task_defaults. Returns empty if not present."""
    behavior = getattr(manifest, "behavior", None) or {}
    if not isinstance(behavior, dict):
        return []
    raw_list = behavior.get("task_defaults") or []
    out: list[PackTaskDefaults] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        out.append(_parse_task_defaults(manifest.pack_id, item))
    return out


def _filter_allowed(d: dict[str, Any], allowed: frozenset) -> dict[str, Any]:
    return {k: v for k, v in d.items() if k in allowed}


def _parse_retrieval_preset(pack_id: str, raw: dict[str, Any]) -> PackRetrievalProfilePreset:
    """Parse one retrieval profile preset; only allowed keys applied."""
    extra = _filter_allowed(dict(raw.get("extra") or raw), RETRIEVAL_PROFILE_ALLOWED_KEYS)
    return PackRetrievalProfilePreset(
        preset_id=(raw.get("preset_id") or "").strip(),
        task_id=(raw.get("task_id") or "").strip(),
        workflow_id=(raw.get("workflow_id") or "").strip(),
        pack_id=pack_id,
        top_k=int(raw.get("top_k") or 0),
        corpus_filter=(raw.get("corpus_filter") or "").strip(),
        max_tokens=int(raw.get("max_tokens") or 0),
        min_score=float(raw.get("min_score") or 0.0),
        rerank=bool(raw.get("rerank", False)),
        include_metadata=bool(raw.get("include_metadata", False)),
        extra=extra,
    )


def _parse_output_preset(pack_id: str, raw: dict[str, Any]) -> PackOutputProfilePreset:
    """Parse one output profile preset."""
    extra = _filter_allowed(dict(raw.get("extra") or raw), OUTPUT_PROFILE_ALLOWED_KEYS)
    return PackOutputProfilePreset(
        preset_id=(raw.get("preset_id") or "").strip(),
        task_id=(raw.get("task_id") or "").strip(),
        workflow_id=(raw.get("workflow_id") or "").strip(),
        pack_id=pack_id,
        adapter=(raw.get("adapter") or "").strip(),
        format_hint=(raw.get("format_hint") or "").strip(),
        max_length_hint=int(raw.get("max_length_hint") or 0),
        sections_hint=(raw.get("sections_hint") or "").strip(),
        extra=extra,
    )


def _parse_parser_hint(pack_id: str, raw: dict[str, Any]) -> ParserOutputHint:
    """Parse one parser/output hint. Only safe keys are read (key, preferred_format, max_length_hint, bullet_preference, stakeholder_safe); keys not in PARSER_OUTPUT_HINT_ALLOWED_KEYS are ignored."""
    return ParserOutputHint(
        key=(raw.get("key") or raw.get("task_id") or raw.get("workflow_id") or "").strip(),
        pack_id=pack_id,
        preferred_format=(raw.get("preferred_format") or "").strip(),
        max_length_hint=int(raw.get("max_length_hint") or 0),
        bullet_preference=(raw.get("bullet_preference") or "").strip(),
        stakeholder_safe=bool(raw.get("stakeholder_safe", False)),
    )


def get_retrieval_profile_presets_from_manifest(manifest: PackManifest) -> list[PackRetrievalProfilePreset]:
    """Extract retrieval profile presets from manifest.behavior.retrieval_profile_presets."""
    behavior = getattr(manifest, "behavior", None) or {}
    if not isinstance(behavior, dict):
        return []
    raw_list = behavior.get("retrieval_profile_presets") or behavior.get("retrieval_presets") or []
    out: list[PackRetrievalProfilePreset] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        out.append(_parse_retrieval_preset(manifest.pack_id, item))
    return out


def get_output_profile_presets_from_manifest(manifest: PackManifest) -> list[PackOutputProfilePreset]:
    """Extract output profile presets from manifest.behavior.output_profile_presets."""
    behavior = getattr(manifest, "behavior", None) or {}
    if not isinstance(behavior, dict):
        return []
    raw_list = behavior.get("output_profile_presets") or behavior.get("output_presets") or []
    out: list[PackOutputProfilePreset] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        out.append(_parse_output_preset(manifest.pack_id, item))
    return out


def get_parser_output_hints_from_manifest(manifest: PackManifest) -> list[ParserOutputHint]:
    """Extract parser/output hints from manifest.behavior.parser_output_hints. Safe keys only."""
    behavior = getattr(manifest, "behavior", None) or {}
    if not isinstance(behavior, dict):
        return []
    raw_list = behavior.get("parser_output_hints") or behavior.get("output_hints") or []
    out: list[ParserOutputHint] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        out.append(_parse_parser_hint(manifest.pack_id, item))
    return out


def get_all_behavior_assets(manifest: PackManifest) -> tuple[list[PackPromptAsset], list[PackTaskDefaults]]:
    """Return (prompt_assets, task_defaults) for a manifest."""
    return get_prompt_assets_from_manifest(manifest), get_task_defaults_from_manifest(manifest)
