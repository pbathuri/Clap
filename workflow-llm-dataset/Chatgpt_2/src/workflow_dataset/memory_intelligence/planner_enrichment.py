"""
M44I–M44L Phase B: Enrich planner planning sources with memory context and prior cases.
Additive: adds memory_context and memory_prior_cases keys.
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


def enrich_planning_sources(
    sources_dict: dict[str, Any],
    project_id: str = "",
    session_id: str | None = None,
    repo_root: Path | str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Add memory_context and memory_prior_cases to the planning sources dict.
    Does not mutate in place; returns a new dict with extra keys.
    """
    root = _repo_root(repo_root)
    out = dict(sources_dict)
    prior_cases = retrieve_for_context(
        project_id=project_id,
        session_id=session_id,
        query="plan goal next step",
        limit=limit,
        repo_root=root,
    )
    snippets = [p.snippet for p in prior_cases if p.snippet]
    out["memory_context"] = {
        "summary": "Prior relevant context from memory." if snippets else "No relevant memory for this project.",
        "snippets": snippets[:3],
        "prior_case_count": len(prior_cases),
    }
    out["memory_prior_cases"] = [p.to_dict() for p in prior_cases[:limit]]
    return out
