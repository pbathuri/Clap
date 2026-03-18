"""
M40C: Frozen-scope report and included/excluded/quarantined surface output.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.production_cut.models import ProductionCut
from workflow_dataset.production_cut.freeze import build_production_freeze


def _surface_label(surface_id: str) -> str:
    try:
        from workflow_dataset.default_experience.surfaces import get_surface_by_id
        s = get_surface_by_id(surface_id)
        return s.label if s else surface_id
    except Exception:
        return surface_id


def build_frozen_scope_report(
    cut: ProductionCut | None = None,
    vertical_id: str | None = None,
    repo_root: str | None = None,
) -> dict[str, Any]:
    """
    Build frozen-scope report from active cut or from vertical_id.
    Returns included, excluded, quarantined lists with counts and optional risk line.
    """
    if cut:
        vid = cut.vertical_id
        included_ids = cut.included_surface_ids
        excluded_ids = cut.excluded_surface_ids
        quarantined_ids = cut.quarantined_surface_ids
    elif vertical_id:
        freeze = build_production_freeze(vertical_id, repo_root)
        if not freeze:
            return {
                "vertical_id": vertical_id,
                "error": "no pack or scope for vertical",
                "included": [], "excluded": [], "quarantined": [],
                "included_count": 0, "excluded_count": 0, "quarantined_count": 0,
            }
        vid = vertical_id
        included_ids = freeze["included_surface_ids"]
        excluded_ids = freeze["excluded_surface_ids"]
        quarantined_ids = freeze["quarantined_surface_ids"]
    else:
        return {
            "vertical_id": "",
            "error": "no cut or vertical_id",
            "included": [], "excluded": [], "quarantined": [],
            "included_count": 0, "excluded_count": 0, "quarantined_count": 0,
        }

    included = [{"surface_id": sid, "label": _surface_label(sid)} for sid in included_ids]
    excluded = [{"surface_id": sid, "label": _surface_label(sid)} for sid in excluded_ids]
    quarantined = [{"surface_id": sid, "label": _surface_label(sid)} for sid in quarantined_ids]

    top_risk = ""
    if excluded_ids:
        top_risk = f"{len(excluded_ids)} surfaces excluded from production scope"

    return {
        "vertical_id": vid,
        "included": included,
        "excluded": excluded,
        "quarantined": quarantined,
        "included_count": len(included),
        "excluded_count": len(excluded),
        "quarantined_count": len(quarantined),
        "top_scope_risk": top_risk,
    }


def build_surfaces_classification(
    cut: ProductionCut | None = None,
    vertical_id: str | None = None,
    repo_root: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Return included, excluded, quarantined as typed entries (IncludedSurface, ExcludedSurface, QuarantinedExperimentalSurface).
    For CLI 'surfaces' output.
    """
    from workflow_dataset.vertical_selection.surface_policies import (
        get_surface_policy_level,
        get_advanced_reveal_rule,
    )

    report = build_frozen_scope_report(cut=cut, vertical_id=vertical_id, repo_root=repo_root)
    if report.get("error"):
        return {"included": [], "excluded": [], "quarantined": []}

    vid = report["vertical_id"]
    included: list[dict[str, Any]] = []
    for e in report.get("included", []):
        sid = e.get("surface_id", "")
        level = get_surface_policy_level(vid, sid) if vid else "recommended"
        included.append({
            "surface_id": sid,
            "label": e.get("label", sid),
            "policy_level": level,
            "is_default_visible": True,
        })
    excluded = [
        {"surface_id": e.get("surface_id", ""), "label": e.get("label", ""), "reason": "excluded"}
        for e in report.get("excluded", [])
    ]
    quarantined = []
    for e in report.get("quarantined", []):
        sid = e.get("surface_id", "")
        reveal = get_advanced_reveal_rule(vid, sid) if vid else "on_demand"
        quarantined.append({
            "surface_id": sid,
            "label": e.get("label", sid),
            "reveal_rule": reveal,
        })
    return {"included": included, "excluded": excluded, "quarantined": quarantined}
