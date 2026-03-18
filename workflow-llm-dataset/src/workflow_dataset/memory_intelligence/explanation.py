"""
M44I–M44L Phase C: Explain recommendation, prior-case influence, weak-memory cautions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_intelligence.store import load_recommendation
from workflow_dataset.memory_fusion.review import list_weak_memories


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def explain_recommendation(
    recommendation_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Return structured explanation for a recommendation: which memory influenced it,
    prior cases, rationale, weak cautions, and action linkages.
    """
    root = _repo_root(repo_root)
    rec = load_recommendation(recommendation_id, repo_root=root)
    if not rec:
        return {
            "recommendation_id": recommendation_id,
            "found": False,
            "message": "Recommendation not found.",
        }
    return {
        "recommendation_id": rec.get("recommendation_id", ""),
        "found": True,
        "kind": rec.get("kind", ""),
        "title": rec.get("title", ""),
        "description": rec.get("description", ""),
        "memory_influence": {
            "prior_cases": rec.get("prior_cases", []),
            "rationale_recall": rec.get("rationale_recall", []),
            "weak_cautions": rec.get("weak_cautions", []),
        },
        "action_linkages": rec.get("action_linkages", []),
    }


def explain_prior_case_influence(
    recommendation_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Return which prior cases influenced this recommendation and how."""
    root = _repo_root(repo_root)
    rec = load_recommendation(recommendation_id, repo_root=root)
    if not rec:
        return {
            "recommendation_id": recommendation_id,
            "found": False,
            "prior_cases": [],
            "influence_summary": "Recommendation not found.",
        }
    prior = rec.get("prior_cases", [])
    rationale = rec.get("rationale_recall", [])
    return {
        "recommendation_id": rec.get("recommendation_id", ""),
        "found": True,
        "prior_cases": prior,
        "rationale_recall": rationale,
        "influence_summary": f"{len(prior)} prior case(s) and {len(rationale)} rationale(s) influenced this recommendation.",
    }


def list_weak_memory_cautions(
    limit: int = 20,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    List weak memories (low confidence or needing review) from memory_fusion
    and from recent recommendations' weak_cautions.
    """
    root = _repo_root(repo_root)
    from workflow_dataset.memory_intelligence.store import list_recent_recommendations
    weak_from_fusion: list[dict[str, Any]] = []
    try:
        weak_from_fusion = list_weak_memories(limit=limit, repo_root=root)
    except Exception:
        pass
    weak_from_recs: list[dict[str, Any]] = []
    for rec in list_recent_recommendations(limit=limit * 2, repo_root=root):
        for w in rec.get("weak_cautions", []):
            weak_from_recs.append({
                "recommendation_id": rec.get("recommendation_id"),
                **w,
            })
    return {
        "weak_memories_from_fusion": weak_from_fusion,
        "weak_cautions_from_recommendations": weak_from_recs[:limit],
    }
