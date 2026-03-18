"""
M39C: Scope lock — core / advanced_available / non_core surfaces per vertical; scope report.
"""

from __future__ import annotations

from workflow_dataset.vertical_selection.models import SURFACE_CLASS_CORE, SURFACE_CLASS_ADVANCED_AVAILABLE, SURFACE_CLASS_NON_CORE
from workflow_dataset.vertical_packs.registry import get_curated_pack
from workflow_dataset.cohort.surface_matrix import get_all_surface_ids


def get_core_surfaces(vertical_id: str) -> list[str]:
    """Surface ids that are core (required) for this vertical."""
    pack = get_curated_pack(vertical_id)
    if not pack:
        return []
    return list(pack.required_surfaces.required_surface_ids)


def get_optional_surfaces(vertical_id: str) -> list[str]:
    """Surface ids that are optional (advanced-but-available) for this vertical."""
    pack = get_curated_pack(vertical_id)
    if not pack:
        return []
    return list(pack.required_surfaces.optional_surface_ids)


def get_excluded_surfaces(vertical_id: str) -> list[str]:
    """Surface ids explicitly excluded/hidden for this vertical."""
    pack = get_curated_pack(vertical_id)
    if not pack:
        return []
    return list(pack.required_surfaces.hidden_for_vertical)


def get_surface_class_for_vertical(surface_id: str, vertical_id: str) -> str:
    """Return core | advanced_available | non_core for this surface in this vertical."""
    core = get_core_surfaces(vertical_id)
    optional = get_optional_surfaces(vertical_id)
    excluded = get_excluded_surfaces(vertical_id)
    if surface_id in core:
        return SURFACE_CLASS_CORE
    if surface_id in optional:
        return SURFACE_CLASS_ADVANCED_AVAILABLE
    if surface_id in excluded:
        return SURFACE_CLASS_NON_CORE
    # Not in required/optional -> non_core for this vertical
    return SURFACE_CLASS_NON_CORE


def get_surfaces_hidden_by_scope(vertical_id: str) -> list[str]:
    """Surfaces that are non-core or excluded for this vertical (down-ranked / hidden by scope)."""
    all_ids = get_all_surface_ids()
    core = set(get_core_surfaces(vertical_id))
    optional = set(get_optional_surfaces(vertical_id))
    excluded = set(get_excluded_surfaces(vertical_id))
    hidden = []
    for sid in all_ids:
        if sid in excluded:
            hidden.append(sid)
        elif sid not in core and sid not in optional:
            hidden.append(sid)
    return hidden


def get_scope_report(vertical_id: str, repo_root: str | None = None) -> dict[str, list[str] | int]:
    """Report: core, optional, hidden/non-core surface lists and counts. repo_root ignored (for API compatibility)."""
    core = get_core_surfaces(vertical_id)
    optional = get_optional_surfaces(vertical_id)
    hidden = get_surfaces_hidden_by_scope(vertical_id)
    return {
        "vertical_id": vertical_id,
        "core_surfaces": core,
        "optional_surfaces": optional,
        "hidden_or_non_core_surfaces": hidden,
        "core_count": len(core),
        "optional_count": len(optional),
        "hidden_count": len(hidden),
    }
