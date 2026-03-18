"""
M40D.1: Experimental quarantine rules — when quarantined surfaces are available; operator-facing explanations.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.production_cut.models import ProductionCut, ExperimentalQuarantineRule
from workflow_dataset.production_cut.store import get_active_cut
from workflow_dataset.vertical_selection.surface_policies import get_advanced_reveal_rule


def _surface_label(surface_id: str) -> str:
    try:
        from workflow_dataset.default_experience.surfaces import get_surface_by_id
        s = get_surface_by_id(surface_id)
        return s.label if s else surface_id
    except Exception:
        return surface_id


def _operator_explanation(surface_id: str, reveal_rule: str) -> str:
    """Clear operator-facing explanation for when this experimental surface is available."""
    if reveal_rule == "never":
        return "Not available in production; excluded from this cut."
    if reveal_rule == "after_first_milestone":
        return "Available only after first-value milestone is reached; best-effort, known limitations."
    if reveal_rule == "on_demand":
        return "Available on demand only; experimental, not part of production-default experience."
    return "Experimental; not production-safe. Use only when explicitly needed."


def _condition_summary(reveal_rule: str) -> str:
    if reveal_rule == "never":
        return "Never shown"
    if reveal_rule == "after_first_milestone":
        return "After first-value milestone"
    if reveal_rule == "on_demand":
        return "On demand only"
    return "On demand"


def list_quarantine_rules(
    cut: ProductionCut | None = None,
    vertical_id: str | None = None,
    repo_root: Any = None,
) -> list[ExperimentalQuarantineRule]:
    """
    List quarantine rules for quarantined (experimental) surfaces in the cut or for vertical_id.
    """
    if cut is None and vertical_id:
        from workflow_dataset.production_cut.freeze import build_production_freeze
        freeze = build_production_freeze(vertical_id, repo_root)
        if not freeze:
            return []
        qids = freeze.get("quarantined_surface_ids", [])
        vid = vertical_id
    elif cut:
        qids = cut.quarantined_surface_ids
        vid = cut.vertical_id
    else:
        cut = get_active_cut(repo_root)
        if not cut:
            return []
        qids = cut.quarantined_surface_ids
        vid = cut.vertical_id
    rules = []
    for sid in qids:
        reveal = get_advanced_reveal_rule(vid, sid) if vid else "on_demand"
        rules.append(ExperimentalQuarantineRule(
            surface_id=sid,
            label=_surface_label(sid),
            reveal_rule=reveal,
            condition_summary=_condition_summary(reveal),
            operator_explanation=_operator_explanation(sid, reveal),
            production_safe=False,
        ))
    return rules


def build_quarantine_rules_report(
    cut: ProductionCut | None = None,
    repo_root: Any = None,
) -> dict[str, Any]:
    """
    Full quarantine rules report: rules list, summary counts, operator-facing summary.
    """
    if cut is None:
        cut = get_active_cut(repo_root)
    if not cut:
        return {
            "vertical_id": "",
            "quarantine_rules": [],
            "count": 0,
            "operator_summary": "No active production cut.",
        }
    rules = list_quarantine_rules(cut=cut)
    summary = f"{len(rules)} experimental surface(s) in quarantine; not production-safe. Available only per reveal rule (on_demand or after_first_milestone)."
    return {
        "vertical_id": cut.vertical_id,
        "label": cut.label,
        "quarantine_rules": [r.to_dict() for r in rules],
        "count": len(rules),
        "operator_summary": summary,
    }
