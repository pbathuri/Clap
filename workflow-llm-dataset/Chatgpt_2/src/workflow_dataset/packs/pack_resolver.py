"""
M22/M24: Resolve active packs and derived capabilities. M24: uses priority (primary, pinned, secondary) when activation state present.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.packs.pack_models import PackManifest
from workflow_dataset.packs.pack_registry import list_installed_packs, get_installed_manifest
from workflow_dataset.packs.pack_activation import load_activation_state


class ActiveCapabilities:
    """Result of capability resolution: active packs and merged config."""

    def __init__(
        self,
        active_packs: list[PackManifest],
        prompts: list[dict[str, Any]],
        templates: list[str],
        output_adapters: list[str],
        parser_profiles: list[str],
        recommended_models: list[str],
        retrieval_profile: dict[str, Any],
        safety_restrictions: list[str],
    ):
        self.active_packs = active_packs
        self.prompts = prompts
        self.templates = templates
        self.output_adapters = output_adapters
        self.parser_profiles = parser_profiles
        self.recommended_models = recommended_models
        self.retrieval_profile = retrieval_profile
        self.safety_restrictions = safety_restrictions


def resolve_active_capabilities(
    role: str | None = None,
    industry: str | None = None,
    workflow_type: str | None = None,
    task_type: str | None = None,
    packs_dir: str | None = None,
) -> ActiveCapabilities:
    """
    Resolve active packs: uses M24 priority (primary, pinned, secondary) when activation state
    has primary or pinned; otherwise tag-based matching as before.
    """
    try:
        from workflow_dataset.packs.pack_resolution_graph import resolve_with_priority
        cap, _ = resolve_with_priority(
            role=role,
            workflow_type=workflow_type,
            task_type=task_type,
            packs_dir=packs_dir,
        )
        return cap
    except Exception:
        pass
    return _resolve_legacy(role, industry, workflow_type, task_type, packs_dir)


def _resolve_legacy(
    role: str | None,
    industry: str | None,
    workflow_type: str | None,
    task_type: str | None,
    packs_dir: str | None,
) -> ActiveCapabilities:
    """Original tag-based resolution (no activation state)."""
    installed = list_installed_packs(packs_dir)
    active: list[PackManifest] = []
    filters = []
    if role:
        filters.append(("role", role.lower()))
    if industry:
        filters.append(("industry", industry.lower()))
    if workflow_type:
        filters.append(("workflow", workflow_type.lower()))
    if task_type:
        filters.append(("task", task_type.lower()))

    for rec in installed:
        manifest = get_installed_manifest(rec["pack_id"], packs_dir)
        if not manifest:
            continue
        if not filters:
            active.append(manifest)
            continue
        match = False
        for kind, value in filters:
            if kind == "role" and any(value in (t or "").lower() for t in manifest.role_tags):
                match = True
                break
            if kind == "industry" and any(value in (t or "").lower() for t in manifest.industry_tags):
                match = True
                break
            if kind == "workflow" and any(value in (t or "").lower() for t in manifest.workflow_tags):
                match = True
                break
            if kind == "task" and any(value in (t or "").lower() for t in manifest.task_tags):
                match = True
                break
        if match:
            active.append(manifest)

    prompts: list[dict[str, Any]] = []
    templates: list[str] = []
    output_adapters: list[str] = []
    parser_profiles: list[str] = []
    recommended_models: list[str] = []
    retrieval_profile: dict[str, Any] = {}
    safety_restrictions: list[str] = []

    for m in active:
        prompts.extend(m.prompts)
        templates.extend(m.templates or m.workflow_templates)
        output_adapters.extend(m.output_adapters)
        parser_profiles.extend(m.parser_profiles)
        recommended_models.extend(m.recommended_models)
        if m.retrieval_profile and not retrieval_profile:
            retrieval_profile = dict(m.retrieval_profile)
        elif m.retrieval_profile:
            retrieval_profile.update(m.retrieval_profile)
        safety_restrictions.extend(m.safety_constraints or [])

    return ActiveCapabilities(
        active_packs=active,
        prompts=prompts,
        templates=list(dict.fromkeys(templates)),
        output_adapters=list(dict.fromkeys(output_adapters)),
        parser_profiles=list(dict.fromkeys(parser_profiles)),
        recommended_models=list(dict.fromkeys(recommended_models)),
        retrieval_profile=retrieval_profile,
        safety_restrictions=list(dict.fromkeys(safety_restrictions)),
    )
