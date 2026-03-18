"""
M43E–M43H: Memory-assisted continuity — attach memory context to resume and next-session recommendation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_fusion.substrate import get_memory_substrate
from workflow_dataset.memory_fusion.links import get_memory_ids_for_entity


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_memory_context_for_continuity(
    project_id: str = "",
    session_id: str = "",
    limit: int = 5,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Retrieve memory context for use in continuity (resume, next-session recommendation).
    Returns snippets and a short rationale line for "memory-assisted" resume.
    """
    root = _repo_root(repo_root)
    substrate = get_memory_substrate(root)
    memory_ids = []
    if project_id:
        memory_ids.extend(get_memory_ids_for_entity("project", project_id, root))
    if session_id:
        memory_ids.extend(get_memory_ids_for_entity("session", session_id, root))
    memory_ids = list(dict.fromkeys(memory_ids))[:limit]
    if not memory_ids:
        return {
            "project_id": project_id,
            "session_id": session_id,
            "memory_snippets": [],
            "rationale_line": "",
            "has_memory_context": False,
        }
    results = substrate.retrieve(
        project_id=project_id,
        session_id=session_id,
        limit=limit,
    )
    snippets = []
    for r in results:
        text = r.get("text", r.get("content", r.get("summary", "")))
        if isinstance(text, str) and text.strip():
            snippets.append(text[:200])
    rationale = ""
    if snippets:
        rationale = f"Recalled {len(snippets)} memory snippet(s) for this project/session."
    return {
        "project_id": project_id,
        "session_id": session_id,
        "memory_snippets": snippets,
        "rationale_line": rationale,
        "has_memory_context": len(snippets) > 0,
    }
