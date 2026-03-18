"""
M44I–M44L Phase B: Memory-backed operator flow hint for delegated responsibility context.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.memory_intelligence.models import (
    MemoryBackedOperatorFlowHint,
    RetrievedPriorCase,
    WeakMemoryCaution,
)
from workflow_dataset.memory_intelligence.retrieval import retrieve_for_context, CONFIDENCE_THRESHOLD_WEAK


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_memory_backed_operator_context(
    project_id: str = "",
    responsibility_id: str = "",
    repo_root: Path | str | None = None,
    limit: int = 5,
) -> MemoryBackedOperatorFlowHint:
    """Retrieve memory relevant to this responsibility and return a flow hint."""
    root = _repo_root(repo_root)
    prior_cases = retrieve_for_context(
        project_id=project_id,
        session_id=None,
        query=f"operator responsibility {responsibility_id}" if responsibility_id else "operator delegated",
        limit=limit,
        repo_root=root,
    )
    used: list[RetrievedPriorCase] = []
    weak: list[WeakMemoryCaution] = []
    for pc in prior_cases:
        if pc.confidence >= CONFIDENCE_THRESHOLD_WEAK:
            used.append(pc)
        else:
            weak.append(WeakMemoryCaution(
                unit_id=pc.unit_id,
                reason_ignored="confidence_below_threshold",
                confidence_score=pc.confidence,
            ))
    summary = used[0].relevance_summary[:200] if used else "No high-confidence memory for this responsibility."
    return MemoryBackedOperatorFlowHint(
        responsibility_id=responsibility_id,
        hint_summary=summary,
        prior_cases=used[:limit],
        weak_cautions=weak[:3],
    )
