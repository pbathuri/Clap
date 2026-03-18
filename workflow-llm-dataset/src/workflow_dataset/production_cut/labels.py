"""
M40D.1: Production-safe vs non-production-safe labeling; operator-facing advanced/experimental explanations.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.production_cut.models import ProductionCut, ProductionSafeLabel
from workflow_dataset.production_cut.store import get_active_cut
from workflow_dataset.production_cut.freeze import build_production_freeze


def _surface_label(surface_id: str) -> str:
    try:
        from workflow_dataset.default_experience.surfaces import get_surface_by_id
        s = get_surface_by_id(surface_id)
        return s.label if s else surface_id
    except Exception:
        return surface_id


def build_production_safe_label_report(
    cut: ProductionCut | None = None,
    vertical_id: str | None = None,
    repo_root: Any = None,
) -> dict[str, Any]:
    """
    Per-surface production-safe vs non-production-safe labels.
    production_safe=True only for included (default-visible) surfaces.
    """
    if cut is None and vertical_id:
        freeze = build_production_freeze(vertical_id, repo_root)
        if not freeze:
            return {"vertical_id": vertical_id, "labels": [], "production_safe_count": 0, "non_production_safe_count": 0}
        included = set(freeze["included_surface_ids"])
        excluded = set(freeze["excluded_surface_ids"])
        quarantined = set(freeze["quarantined_surface_ids"])
        vid = vertical_id
    elif cut:
        included = set(cut.included_surface_ids)
        excluded = set(cut.excluded_surface_ids)
        quarantined = set(cut.quarantined_surface_ids)
        vid = cut.vertical_id
    else:
        cut = get_active_cut(repo_root)
        if not cut:
            return {"vertical_id": "", "labels": [], "production_safe_count": 0, "non_production_safe_count": 0}
        return build_production_safe_label_report(cut=cut, repo_root=repo_root)
    labels: list[dict[str, Any]] = []
    all_ids = included | excluded | quarantined
    for sid in sorted(all_ids):
        safe = sid in included
        if sid in quarantined:
            reason = "experimental"
        elif sid in excluded:
            reason = "excluded"
        else:
            reason = ""
        labels.append(ProductionSafeLabel(
            surface_id=sid,
            label=_surface_label(sid),
            production_safe=safe,
            reason_if_not_safe=reason,
        ).to_dict())
    return {
        "vertical_id": vid,
        "labels": labels,
        "production_safe_count": len(included),
        "non_production_safe_count": len(excluded) + len(quarantined),
    }


def build_operator_surface_explanations(
    cut: ProductionCut | None = None,
    repo_root: Any = None,
) -> dict[str, Any]:
    """
    Operator-facing explanations: what is advanced-only, what is experimental-only.
    """
    if cut is None:
        cut = get_active_cut(repo_root)
    if not cut:
        return {
            "advanced_only_summary": "",
            "experimental_only_summary": "",
            "production_safe_summary": "",
        }
    # Advanced-only: optional surfaces (allowed but not recommended) — show as "available in advanced mode"
    from workflow_dataset.vertical_selection.scope_lock import get_optional_surfaces
    optional = get_optional_surfaces(cut.vertical_id)
    from workflow_dataset.vertical_selection.surface_policies import is_surface_experimental
    optional_non_experimental = [s for s in optional if not is_surface_experimental(s)]
    advanced_only_summary = (
        f"{len(optional_non_experimental)} surface(s) are available in advanced mode only (on demand): "
        + ", ".join(optional_non_experimental[:6])
        + ("..." if len(optional_non_experimental) > 6 else "")
    ) if optional_non_experimental else "No additional surfaces in advanced mode; production default is the full supported set."
    # Experimental-only: quarantined
    q = cut.quarantined_surface_ids
    experimental_only_summary = (
        f"{len(q)} surface(s) are experimental only (not production-safe): "
        + ", ".join(q[:6])
        + ("..." if len(q) > 6 else "")
        + ". Use only when explicitly needed; best-effort, known limitations."
    ) if q else "No experimental surfaces in this cut."
    # Production-safe
    production_safe_summary = (
        f"{len(cut.included_surface_ids)} surface(s) are production-safe and default-visible for this cut."
    )
    return {
        "advanced_only_summary": advanced_only_summary,
        "experimental_only_summary": experimental_only_summary,
        "production_safe_summary": production_safe_summary,
        "included_count": len(cut.included_surface_ids),
        "quarantined_count": len(q),
        "optional_advanced_count": len(optional_non_experimental),
    }
