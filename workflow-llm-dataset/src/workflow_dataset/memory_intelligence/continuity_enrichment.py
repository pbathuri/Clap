"""
M44I–M44L Phase B: Enrich continuity resume and next-session recommendation with memory context.
Returns dicts that can be attached as memory_context on ResumeCard / NextSessionRecommendation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_intelligence.retrieval import retrieve_for_context


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_resume_memory_context(
    project_id: str = "",
    session_ref: str = "",
    repo_root: Path | str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Memory context for resume flow: prior cases and rationale summary for reconnecting."""
    root = _repo_root(repo_root)
    prior_cases = retrieve_for_context(
        project_id=project_id,
        session_id=session_ref or None,
        query="resume continue next step",
        limit=limit,
        repo_root=root,
    )
    return {
        "prior_cases": [p.to_dict() for p in prior_cases],
        "rationale_summary": "Prior session context used to suggest resume." if prior_cases else "No prior memory for this context.",
    }


def get_next_session_memory_context(
    project_id: str = "",
    repo_root: Path | str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Memory context for next-session recommendation (e.g. from shutdown)."""
    root = _repo_root(repo_root)
    prior_cases = retrieve_for_context(
        project_id=project_id,
        session_id=None,
        query="next session start tomorrow",
        limit=limit,
        repo_root=root,
    )
    return {
        "prior_cases": [p.to_dict() for p in prior_cases],
        "rationale_summary": "Prior patterns used for next-session suggestion." if prior_cases else "No prior memory.",
    }
