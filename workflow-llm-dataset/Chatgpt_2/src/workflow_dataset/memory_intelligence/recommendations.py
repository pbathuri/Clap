"""
M44I–M44L: Build memory-backed recommendations from retrieval; persist for explain.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.memory_intelligence.models import (
    RetrievalGroundedRecommendation,
    RetrievedPriorCase,
    DecisionRationaleRecall,
    WeakMemoryCaution,
)
from workflow_dataset.memory_intelligence.retrieval import retrieve_for_context, CONFIDENCE_THRESHOLD_WEAK
from workflow_dataset.memory_intelligence.store import save_recommendation
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_memory_backed_recommendations(
    project_id: str = "",
    session_id: str | None = None,
    repo_root: Path | str | None = None,
    limit: int = 5,
    persist: bool = True,
) -> list[RetrievalGroundedRecommendation]:
    """
    Retrieve memory for context, turn into explicit recommendations with prior cases and rationale.
    Optionally persist so explain_recommendation(rec_id) can be used later.
    """
    root = _repo_root(repo_root)
    prior_cases = retrieve_for_context(
        project_id=project_id,
        session_id=session_id,
        query="",
        limit=limit * 2,
        repo_root=root,
    )
    out: list[RetrievalGroundedRecommendation] = []
    if not prior_cases:
        return out
    weak_cautions: list[WeakMemoryCaution] = []
    used: list[RetrievedPriorCase] = []

    for pc in prior_cases:
        if pc.confidence >= CONFIDENCE_THRESHOLD_WEAK:
            used.append(pc)
        else:
            weak_cautions.append(WeakMemoryCaution(
                unit_id=pc.unit_id,
                reason_ignored="confidence_below_threshold",
                confidence_score=pc.confidence,
            ))

    if not used and not weak_cautions:
        return out

    rec_id = stable_id("rec", project_id or "default", session_id or "", utc_now_iso()[:19], prefix="rec_")
    rationale = []
    if used:
        rationale.append(DecisionRationaleRecall(
            rationale_id=stable_id("rationale", rec_id, prefix="r_"),
            summary="Retrieved prior context used to ground this recommendation.",
            source_unit_ids=[p.unit_id for p in used],
            influence_strength="medium" if len(used) >= 2 else "low",
        ))

    rec = RetrievalGroundedRecommendation(
        recommendation_id=rec_id,
        kind="next_step",
        title="Memory-backed suggestion",
        description=used[0].relevance_summary[:300] if used else "No high-confidence memory; review weak memories if needed.",
        project_id=project_id,
        session_id=session_id or "",
        prior_cases=used[:limit],
        rationale_recall=rationale,
        weak_cautions=weak_cautions[:5],
        action_linkages=[],
        created_at_utc=utc_now_iso(),
    )
    out.append(rec)
    if persist:
        save_recommendation(rec, repo_root=root)
    return out
