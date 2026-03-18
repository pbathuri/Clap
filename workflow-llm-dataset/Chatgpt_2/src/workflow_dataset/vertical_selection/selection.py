"""
M39B: Rank vertical candidates; recommend primary and secondary; explain.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_selection.models import VerticalCandidate
from workflow_dataset.vertical_selection.candidates import build_candidates


def rank_candidates(repo_root: Path | str | None = None) -> list[VerticalCandidate]:
    """
    Rank candidates by (evidence_score + readiness_score - support_burden_score - trust_risk_score).
    Higher composite = stronger. Returns list sorted descending.
    """
    candidates = build_candidates(repo_root)
    def composite(c: VerticalCandidate) -> float:
        return c.evidence_score + c.readiness_score - c.support_burden_score - 0.2 * c.trust_risk_score
    return sorted(candidates, key=composite, reverse=True)


def recommend_primary_secondary(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Recommend primary and optional secondary vertical from ranked candidates.
    Returns { primary, secondary (or None), primary_reason, secondary_reason, ranked_ids, no_evidence }.
    """
    ranked = rank_candidates(repo_root)
    no_evidence = not ranked or all(c.evidence_score <= 0.3 for c in ranked)
    primary = ranked[0] if ranked else None
    secondary = ranked[1] if len(ranked) > 1 else None
    return {
        "primary": primary.to_dict() if primary else None,
        "secondary": secondary.to_dict() if secondary else None,
        "primary_reason": primary.strength_reason if primary else "No candidates.",
        "secondary_reason": secondary.strength_reason if secondary else None,
        "ranked_ids": [c.vertical_id for c in ranked],
        "no_evidence": no_evidence,
    }


def explain_vertical(vertical_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Explain why this vertical is strong or weak (scores, reasons)."""
    c = next((x for x in build_candidates(repo_root) if x.vertical_id == vertical_id), None)
    if not c:
        return {"vertical_id": vertical_id, "error": "unknown vertical"}
    ranked = rank_candidates(repo_root)
    rank = next((i + 1 for i, x in enumerate(ranked) if x.vertical_id == vertical_id), 0)
    return {
        "vertical_id": c.vertical_id,
        "label": c.label,
        "evidence_score": c.evidence_score,
        "readiness_score": c.readiness_score,
        "support_burden_score": c.support_burden_score,
        "strength_reason": c.strength_reason,
        "weakness_reason": c.weakness_reason,
        "rank": rank,
        "core_workflow_ids": c.core_workflow_ids,
        "required_surface_ids": c.required_surface_ids[:15],
    }
