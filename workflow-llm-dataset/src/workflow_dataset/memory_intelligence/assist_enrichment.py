"""
M44I–M44L Phase B: Memory-backed suggestions for assist context.
Returns list of MemoryBackedNextStepSuggestion that can be merged with assist queue or shown separately.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.memory_intelligence.models import (
    MemoryBackedNextStepSuggestion,
    RetrievedPriorCase,
    WeakMemoryCaution,
)
from workflow_dataset.memory_intelligence.retrieval import retrieve_for_context, CONFIDENCE_THRESHOLD_WEAK
from workflow_dataset.utils.hashes import stable_id


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def memory_backed_suggestions_for_context(
    project_id: str = "",
    session_id: str | None = None,
    repo_root: Path | str | None = None,
    max_suggestions: int = 3,
) -> list[MemoryBackedNextStepSuggestion]:
    """Build memory-backed next-step suggestions for the given project/session."""
    root = _repo_root(repo_root)
    prior_cases = retrieve_for_context(
        project_id=project_id,
        session_id=session_id,
        query="next step suggest",
        limit=max_suggestions * 2,
        repo_root=root,
    )
    out: list[MemoryBackedNextStepSuggestion] = []
    for i, pc in enumerate(prior_cases):
        if pc.confidence < CONFIDENCE_THRESHOLD_WEAK:
            continue
        if len(out) >= max_suggestions:
            break
        sug_id = stable_id("mem_sug", project_id or "default", pc.unit_id, str(i), prefix="sug_")
        out.append(MemoryBackedNextStepSuggestion(
            suggestion_id=sug_id,
            title="Memory suggests",
            description=pc.relevance_summary[:200] or "Continue based on prior context.",
            project_id=project_id,
            prior_case=pc,
            weak_caution=None,
        ))
    return out
