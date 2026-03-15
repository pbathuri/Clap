"""
M24: Detect conflicts between installed packs. Classify and report; no silent overwrites.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from workflow_dataset.packs.pack_models import PackManifest


class ConflictClass(str, Enum):
    HARMLESS_OVERLAP = "harmless_overlap"
    MERGEABLE = "mergeable"
    PRECEDENCE_REQUIRED = "precedence_required"
    INCOMPATIBLE = "incompatible"
    BLOCKED = "blocked"


@dataclass
class PackConflict:
    """One detected conflict between packs."""

    conflict_class: ConflictClass
    capability: str  # e.g. templates, output_adapters, retrieval_profile
    pack_ids: list[str]
    description: str
    resolution: str = ""  # how it was or will be resolved


def _tags_match(manifest: PackManifest, role: str | None, workflow: str | None, task: str | None) -> bool:
    if role and not any(role.lower() in (t or "").lower() for t in manifest.role_tags):
        return False
    if workflow and not any(workflow.lower() in (t or "").lower() for t in manifest.workflow_tags):
        return False
    if task and not any(task.lower() in (t or "").lower() for t in manifest.task_tags):
        return False
    return True


def detect_conflicts(
    manifests: list[PackManifest],
    role: str | None = None,
    workflow: str | None = None,
    task: str | None = None,
) -> list[PackConflict]:
    """
    Detect conflicts among manifests. Optionally filter by role/workflow/task so only
    packs that would be active together are compared.
    """
    conflicts: list[PackConflict] = []
    if len(manifests) < 2:
        return conflicts

    # Filter to those matching scope if scope given
    if role or workflow or task:
        manifests = [m for m in manifests if _tags_match(m, role, workflow, task)]
    if len(manifests) < 2:
        return conflicts

    pack_ids = [m.pack_id for m in manifests]

    # Templates overlap: same template in multiple packs -> harmless_overlap
    all_templates: dict[str, list[str]] = {}
    for m in manifests:
        for t in m.templates or m.workflow_templates or []:
            all_templates.setdefault(t, []).append(m.pack_id)
    for t, ids in all_templates.items():
        if len(ids) > 1:
            conflicts.append(PackConflict(
                conflict_class=ConflictClass.HARMLESS_OVERLAP,
                capability="templates",
                pack_ids=ids,
                description=f"Template '{t}' declared by multiple packs.",
                resolution="Merged; included once. Primary pack's order wins.",
            ))

    # Output adapters: different default order -> precedence_required
    adapters_by_pack = {m.pack_id: (m.output_adapters or []) for m in manifests}
    first_adapters = {}
    for pid, adaps in adapters_by_pack.items():
        if adaps:
            first_adapters[pid] = adaps[0]
    if len(set(first_adapters.values())) > 1:
        conflicts.append(PackConflict(
            conflict_class=ConflictClass.PRECEDENCE_REQUIRED,
            capability="output_adapters",
            pack_ids=pack_ids,
            description="Different default output adapter (first in list) across packs.",
            resolution="Primary pack's default adapter wins for role scope.",
        ))

    # Retrieval profile: different top_k -> mergeable
    top_ks = [m.retrieval_profile.get("top_k") for m in manifests if m.retrieval_profile and m.retrieval_profile.get("top_k") is not None]
    if len(set(top_ks)) > 1:
        conflicts.append(PackConflict(
            conflict_class=ConflictClass.MERGEABLE,
            capability="retrieval_profile",
            pack_ids=pack_ids,
            description="Different retrieval top_k across packs.",
            resolution="Primary pack's retrieval_profile wins.",
        ))

    # Optional wrappers: one has network/proxy, another strict local -> blocked when strict is primary
    has_wrapper = [m.pack_id for m in manifests if m.optional_wrappers]
    strict_local = [m.pack_id for m in manifests if (m.safety_policies or {}).get("no_network_default") is True]
    if has_wrapper and strict_local:
        conflicts.append(PackConflict(
            conflict_class=ConflictClass.BLOCKED,
            capability="optional_wrappers",
            pack_ids=has_wrapper + strict_local,
            description="Some packs use optional_wrappers (e.g. proxy) while others are strict local-only.",
            resolution="Strict local-only wins; wrapper pack is excluded when strict pack is primary.",
        ))

    # Safety: one weakens (already rejected at install; but if we had two installs from different sources)
    for m in manifests:
        sp = m.safety_policies or {}
        if sp.get("sandbox_only") is False or sp.get("require_apply_confirm") is False:
            conflicts.append(PackConflict(
                conflict_class=ConflictClass.INCOMPATIBLE,
                capability="safety_policies",
                pack_ids=[m.pack_id],
                description=f"Pack {m.pack_id} weakens safety (would be rejected at install).",
                resolution="Stricter safety wins; pack should not be installed.",
            ))

    return conflicts
