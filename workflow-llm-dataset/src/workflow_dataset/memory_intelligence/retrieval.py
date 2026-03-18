"""
M44I–M44L: Retrieve memory for a given context (project/session) using substrate + fusion links.
Returns units/snippets with confidence for use in recommendations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_intelligence.models import RetrievedPriorCase

CONFIDENCE_THRESHOLD_WEAK = 0.4  # Below this, treat as weak (caution)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def retrieve_for_context(
    project_id: str = "",
    session_id: str | None = None,
    query: str = "",
    limit: int = 10,
    repo_root: Path | str | None = None,
) -> list[RetrievedPriorCase]:
    """
    Retrieve memory units for the given context. Uses memory_substrate.retrieve_units
    and optionally memory_fusion links to scope by project/session.
    Returns list of prior-case-like records with snippet and confidence.
    """
    root = _repo_root(repo_root)
    out: list[RetrievedPriorCase] = []

    try:
        from workflow_dataset.memory_substrate import retrieve_units
        from workflow_dataset.memory_substrate.models import RetrievalIntent, CompressedMemoryUnit
    except ImportError:
        return out

    # Resolve session: prefer passed session_id; else sessions linked to project
    resolved_session = session_id
    if not resolved_session and project_id:
        try:
            from workflow_dataset.memory_fusion.links import get_links_for_entity
            links = get_links_for_entity("project", project_id, repo_root=root)
            session_ids = list({l.get("entity_id") for l in links if l.get("entity_type") == "session" and l.get("entity_id")})
            if session_ids:
                resolved_session = session_ids[0]
        except Exception:
            pass

    search_query = query or (f"project {project_id}" if project_id else "workflow")
    intent = RetrievalIntent(
        query=search_query,
        top_k=limit,
        session_id=resolved_session,
        source=None,
        semantic=False,
    )
    try:
        units: list[CompressedMemoryUnit] = retrieve_units(intent, repo_root=root)
    except Exception:
        units = []

    for i, u in enumerate(units):
        snippet = (u.lossless_restatement or "")[:500]
        # Simple confidence: decay by rank; could later use link confidence or score from backend
        confidence = max(0.0, 1.0 - (i * 0.08))
        out.append(RetrievedPriorCase(
            unit_id=getattr(u, "unit_id", "") or "",
            snippet=snippet,
            source=getattr(u, "source", "") or "",
            session_id=getattr(u, "session_id", "") or "",
            relevance_summary=snippet[:200] if snippet else "No snippet",
            confidence=confidence,
        ))

    return out
