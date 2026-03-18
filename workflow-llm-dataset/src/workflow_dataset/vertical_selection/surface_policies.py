"""
M39D.1: Vertical-specific core vs advanced surface policies — recommended / allowed / discouraged / blocked;
experimental labels; advanced surface reveal rules.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.vertical_selection.models import (
    SurfacePolicyEntry,
    SURFACE_POLICY_RECOMMENDED,
    SURFACE_POLICY_ALLOWED,
    SURFACE_POLICY_DISCOURAGED,
    SURFACE_POLICY_BLOCKED,
    REVEAL_ALWAYS,
    REVEAL_ON_DEMAND,
    REVEAL_AFTER_FIRST_MILESTONE,
    REVEAL_NEVER,
)
from workflow_dataset.vertical_packs.registry import get_curated_pack
from workflow_dataset.cohort.surface_matrix import get_all_surface_ids

# Surfaces we label as experimental (best-effort, known limitations)
EXPERIMENTAL_SURFACE_IDS: set[str] = {
    "automation_run",
    "background_run",
    "copilot_plan",
    "agent_loop",
    "timeline",
    "automation_inbox",
}


def _surface_label(surface_id: str) -> str:
    try:
        from workflow_dataset.default_experience.surfaces import get_surface_by_id
        s = get_surface_by_id(surface_id)
        return s.label if s else surface_id
    except Exception:
        return surface_id


def get_surface_policy_level(vertical_id: str, surface_id: str) -> str:
    """M39D.1: recommended | allowed | discouraged | blocked for this vertical and surface."""
    pack = get_curated_pack(vertical_id)
    if not pack:
        return SURFACE_POLICY_DISCOURAGED
    req = pack.required_surfaces
    if surface_id in req.required_surface_ids:
        return SURFACE_POLICY_RECOMMENDED
    if surface_id in req.optional_surface_ids:
        return SURFACE_POLICY_ALLOWED
    if surface_id in req.hidden_for_vertical:
        return SURFACE_POLICY_BLOCKED
    return SURFACE_POLICY_DISCOURAGED


def is_surface_experimental(surface_id: str) -> bool:
    """M39D.1: True if surface is explicitly experimental (best-effort, known limitations)."""
    return surface_id in EXPERIMENTAL_SURFACE_IDS


def get_advanced_reveal_rule(vertical_id: str, surface_id: str) -> str:
    """M39D.1: When to reveal this surface for this vertical: always | on_demand | after_first_milestone | never."""
    level = get_surface_policy_level(vertical_id, surface_id)
    if level == SURFACE_POLICY_BLOCKED:
        return REVEAL_NEVER
    if level == SURFACE_POLICY_RECOMMENDED:
        return REVEAL_ALWAYS
    if level == SURFACE_POLICY_ALLOWED:
        return REVEAL_ON_DEMAND
    return REVEAL_ON_DEMAND


def get_surface_policy_entry(vertical_id: str, surface_id: str) -> SurfacePolicyEntry:
    """M39D.1: Full policy entry for this vertical and surface."""
    level = get_surface_policy_level(vertical_id, surface_id)
    reveal = get_advanced_reveal_rule(vertical_id, surface_id)
    experimental = is_surface_experimental(surface_id)
    return SurfacePolicyEntry(
        surface_id=surface_id,
        policy_level=level,
        is_experimental=experimental,
        reveal_rule=reveal,
        label=_surface_label(surface_id),
    )


def get_surface_policy_report(vertical_id: str) -> dict[str, Any]:
    """
    M39D.1: Full surface policy report for vertical: recommended, allowed, discouraged, blocked lists;
    experimental_labels; reveal_rules summary.
    """
    all_ids = get_all_surface_ids()
    recommended: list[str] = []
    allowed: list[str] = []
    discouraged: list[str] = []
    blocked: list[str] = []
    experimental_labels: dict[str, bool] = {}
    entries: list[dict[str, Any]] = []

    for sid in all_ids:
        level = get_surface_policy_level(vertical_id, sid)
        if level == SURFACE_POLICY_RECOMMENDED:
            recommended.append(sid)
        elif level == SURFACE_POLICY_ALLOWED:
            allowed.append(sid)
        elif level == SURFACE_POLICY_BLOCKED:
            blocked.append(sid)
        else:
            discouraged.append(sid)
        if is_surface_experimental(sid):
            experimental_labels[sid] = True
        entries.append(get_surface_policy_entry(vertical_id, sid).to_dict())

    return {
        "vertical_id": vertical_id,
        "recommended_surfaces": recommended,
        "allowed_surfaces": allowed,
        "discouraged_surfaces": discouraged,
        "blocked_surfaces": blocked,
        "recommended_count": len(recommended),
        "allowed_count": len(allowed),
        "discouraged_count": len(discouraged),
        "blocked_count": len(blocked),
        "experimental_labels": experimental_labels,
        "reveal_rules_summary": {
            "always": len([e for e in entries if e.get("reveal_rule") == REVEAL_ALWAYS]),
            "on_demand": len([e for e in entries if e.get("reveal_rule") == REVEAL_ON_DEMAND]),
            "after_first_milestone": len([e for e in entries if e.get("reveal_rule") == REVEAL_AFTER_FIRST_MILESTONE]),
            "never": len([e for e in entries if e.get("reveal_rule") == REVEAL_NEVER]),
        },
        "entries": entries,
    }
