"""
M40C: Production surface freeze — default-visible, hidden experimental, blocked; queue/day/workspace defaults; trust.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.vertical_selection.scope_lock import (
    get_core_surfaces,
    get_optional_surfaces,
    get_excluded_surfaces,
    get_scope_report,
)
from workflow_dataset.vertical_selection.surface_policies import (
    get_surface_policy_report,
    is_surface_experimental,
)
from workflow_dataset.cohort.surface_matrix import get_all_surface_ids


def build_production_freeze(
    vertical_id: str,
    repo_root: str | None = None,
) -> dict[str, Any] | None:
    """
    Build production freeze for vertical: included (default-visible), excluded (blocked/non-core), quarantined (experimental).
    Returns dict with included_surface_ids, excluded_surface_ids, quarantined_surface_ids; None if vertical has no pack.
    """
    from workflow_dataset.vertical_packs.registry import get_curated_pack
    pack = get_curated_pack(vertical_id)
    if not pack:
        return None

    core = get_core_surfaces(vertical_id)
    optional = get_optional_surfaces(vertical_id)
    excluded_pack = get_excluded_surfaces(vertical_id)
    policy = get_surface_policy_report(vertical_id)
    blocked = set(policy.get("blocked_surfaces", []))
    discouraged = set(policy.get("discouraged_surfaces", []))
    all_ids = get_all_surface_ids()

    # Included: core + optional that are not experimental (default-visible supported)
    experimental = {sid for sid in all_ids if is_surface_experimental(sid)}
    included = list(core)
    for sid in optional:
        if sid not in experimental:
            included.append(sid)
    included = list(dict.fromkeys(included))

    # Quarantined: experimental surfaces that are in core or optional (visible under policy only)
    quarantined = [sid for sid in all_ids if is_surface_experimental(sid) and (sid in core or sid in optional)]
    quarantined = list(dict.fromkeys(quarantined))

    # Excluded: blocked, discouraged, pack hidden, and any other not in core/optional
    excluded_set = set(blocked) | set(discouraged) | set(excluded_pack)
    for sid in all_ids:
        if sid not in core and sid not in optional:
            excluded_set.add(sid)
    excluded_set -= set(included) | set(quarantined)
    excluded = list(excluded_set)

    return {
        "vertical_id": vertical_id,
        "included_surface_ids": included,
        "excluded_surface_ids": excluded,
        "quarantined_surface_ids": quarantined,
        "core_count": len(core),
        "optional_count": len(optional),
        "included_count": len(included),
        "excluded_count": len(excluded),
        "quarantined_count": len(quarantined),
    }


def get_default_visible_surfaces(vertical_id: str) -> list[str]:
    """Surfaces that are default-visible for this vertical (included, not quarantined)."""
    freeze = build_production_freeze(vertical_id)
    if not freeze:
        return []
    return list(freeze["included_surface_ids"])


def get_hidden_experimental_surfaces(vertical_id: str) -> list[str]:
    """Surfaces that are experimental and hidden-by-default (quarantined)."""
    freeze = build_production_freeze(vertical_id)
    if not freeze:
        return []
    return list(freeze["quarantined_surface_ids"])


def get_blocked_unsupported_surfaces(vertical_id: str) -> list[str]:
    """Surfaces that are blocked or unsupported for this vertical."""
    freeze = build_production_freeze(vertical_id)
    if not freeze:
        return []
    return list(freeze["excluded_surface_ids"])
