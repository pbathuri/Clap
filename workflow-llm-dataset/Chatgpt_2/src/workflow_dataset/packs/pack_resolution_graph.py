"""
M24: Resolution with priority — primary, pinned, secondary; merge/precedence rules; explanation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_dataset.packs.pack_models import PackManifest
from workflow_dataset.packs.pack_registry import list_installed_packs, get_installed_manifest
from workflow_dataset.packs.pack_activation import (
    load_activation_state,
    get_primary_pack_id,
    get_pinned,
    get_suspended_pack_ids,
    get_current_context,
)
from workflow_dataset.packs.pack_state import get_active_role
from workflow_dataset.packs.pack_conflicts import detect_conflicts, PackConflict, ConflictClass
from workflow_dataset.packs.pack_resolver import ActiveCapabilities


@dataclass
class ResolutionExplanation:
    """Why this set of packs and capabilities was chosen."""

    primary_pack_id: str = ""
    pinned_packs: list[str] = field(default_factory=list)
    secondary_pack_ids: list[str] = field(default_factory=list)
    excluded_pack_ids: list[str] = field(default_factory=list)
    conflicts: list[PackConflict] = field(default_factory=list)
    summary: str = ""


def _tag_matches(manifest: PackManifest, role: str | None, workflow: str | None, task: str | None) -> bool:
    if role and not any((role or "").lower() in (t or "").lower() for t in manifest.role_tags):
        return False
    if workflow and not any((workflow or "").lower() in (t or "").lower() for t in manifest.workflow_tags):
        return False
    if task and not any((task or "").lower() in (t or "").lower() for t in manifest.task_tags):
        return False
    return True


def resolve_with_priority(
    role: str | None = None,
    industry: str | None = None,
    workflow_type: str | None = None,
    task_type: str | None = None,
    packs_dir: str | None = None,
    scope_pinned: str | None = None,
) -> tuple[ActiveCapabilities, ResolutionExplanation]:
    """
    Resolve active capabilities using activation state (primary, pinned, suspended) and merge rules.
    If no primary/pinned state, falls back to tag-based resolution (all matching packs).
    """
    packs_dir = packs_dir or "data/local/packs"
    ctx = get_current_context(packs_dir)
    active_role = role or ctx.get("current_role") or get_active_role(packs_dir)
    active_workflow = workflow_type or ctx.get("current_workflow")
    active_task = task_type or ctx.get("current_task")

    installed = list_installed_packs(packs_dir)
    suspended = set(get_suspended_pack_ids(packs_dir))
    primary_id = get_primary_pack_id(packs_dir)
    pinned = get_pinned(packs_dir)
    # Scope for pin: e.g. session, task; if scope_pinned given, use that key
    pin_scope = scope_pinned or "session"
    pinned_for_scope = pinned.get(pin_scope) or pinned.get("task") or pinned.get("project") or ""

    explanation = ResolutionExplanation()

    # Build candidate manifests
    candidates: list[PackManifest] = []
    for rec in installed:
        pid = rec.get("pack_id", "")
        if pid in suspended:
            explanation.excluded_pack_ids.append(pid)
            continue
        m = get_installed_manifest(pid, packs_dir)
        if not m:
            continue
        candidates.append(m)

    # Determine active set: pinned for scope overrides; then primary if role matches; then matching secondaries
    active: list[PackManifest] = []
    if pinned_for_scope:
        pin_manifest = get_installed_manifest(pinned_for_scope, packs_dir)
        if pin_manifest and pin_manifest not in active:
            active.append(pin_manifest)
            explanation.pinned_packs.append(pinned_for_scope)

    if primary_id and primary_id not in suspended:
        primary_manifest = get_installed_manifest(primary_id, packs_dir)
        if primary_manifest and primary_manifest not in active:
            # Include primary if role matches or no role filter
            if not active_role or _tag_matches(primary_manifest, active_role, active_workflow, active_task):
                active.insert(0, primary_manifest)  # primary first
                explanation.primary_pack_id = primary_id

    for m in candidates:
        if m in active:
            continue
        if active_role or active_workflow or active_task:
            if not _tag_matches(m, active_role, active_workflow, active_task):
                continue
        active.append(m)
        explanation.secondary_pack_ids.append(m.pack_id)

    # If no activation state, use original behavior: all matching by role/workflow/task
    if not active and (active_role or active_workflow or active_task):
        for m in candidates:
            if _tag_matches(m, active_role, active_workflow, active_task):
                active.append(m)
                if not explanation.primary_pack_id:
                    explanation.primary_pack_id = m.pack_id
    elif not active:
        active = list(candidates)

    # Detect conflicts among active packs
    explanation.conflicts = detect_conflicts(active, role=active_role, workflow=active_workflow, task=active_task)
    blocked_ids = {pid for c in explanation.conflicts for pid in c.pack_ids if c.conflict_class == ConflictClass.BLOCKED}
    # Exclude blocked packs that are not primary/pinned (strict local wins)
    if blocked_ids and explanation.primary_pack_id and explanation.primary_pack_id not in blocked_ids:
        for pid in blocked_ids:
            if pid in explanation.pinned_packs or pid == explanation.primary_pack_id:
                continue
            active = [m for m in active if m.pack_id != pid]
            explanation.excluded_pack_ids.append(pid)

    # Merge capabilities: primary wins single-value; lists dedupe with primary first
    prompts: list[dict[str, Any]] = []
    templates: list[str] = []
    output_adapters: list[str] = []
    parser_profiles: list[str] = []
    recommended_models: list[str] = []
    retrieval_profile: dict[str, Any] = {}
    safety_restrictions: list[str] = []

    for m in active:
        prompts.extend(m.prompts)
        for t in m.templates or m.workflow_templates or []:
            if t not in templates:
                templates.append(t)
        for a in m.output_adapters or []:
            if a not in output_adapters:
                output_adapters.append(a)
        for p in m.parser_profiles or []:
            if p not in parser_profiles:
                parser_profiles.append(p)
        for r in m.recommended_models or []:
            if r not in recommended_models:
                recommended_models.append(r)
        if m.retrieval_profile and not retrieval_profile:
            retrieval_profile = dict(m.retrieval_profile)
        elif m.retrieval_profile and not retrieval_profile.get("top_k"):
            retrieval_profile.setdefault("top_k", m.retrieval_profile.get("top_k", 5))
        safety_restrictions.extend(m.safety_constraints or [])

    safety_restrictions = list(dict.fromkeys(safety_restrictions))

    cap = ActiveCapabilities(
        active_packs=active,
        prompts=prompts,
        templates=templates,
        output_adapters=output_adapters,
        parser_profiles=parser_profiles,
        recommended_models=recommended_models,
        retrieval_profile=retrieval_profile,
        safety_restrictions=safety_restrictions,
    )

    # Summary
    parts = []
    if explanation.primary_pack_id:
        parts.append(f"primary={explanation.primary_pack_id}")
    if explanation.pinned_packs:
        parts.append(f"pinned={explanation.pinned_packs}")
    if explanation.secondary_pack_ids:
        parts.append(f"secondary={explanation.secondary_pack_ids}")
    if explanation.excluded_pack_ids:
        parts.append(f"excluded={explanation.excluded_pack_ids}")
    if explanation.conflicts:
        parts.append(f"conflicts={len(explanation.conflicts)}")
    explanation.summary = "; ".join(parts) or "no packs"

    return cap, explanation
