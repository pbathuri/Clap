"""
M43E–M43H: Memory-aware live context — retrieve memories for current project/session for fusion or explain.
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


def get_memory_context_for_live_context(
    project_id: str = "",
    session_id: str = "",
    limit: int = 5,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Retrieve memory snippets relevant to the current project/session for use in live context.
    Returns summary list and optional snippets; empty when no substrate or no links.
    """
    root = _repo_root(repo_root)
    substrate = get_memory_substrate(root)
    memory_ids_project = get_memory_ids_for_entity("project", project_id, root) if project_id else []
    memory_ids_session = get_memory_ids_for_entity("session", session_id, root) if session_id else []
    all_ids = list(dict.fromkeys(memory_ids_project + memory_ids_session))[:limit * 2]
    if not all_ids:
        return {
            "project_id": project_id,
            "session_id": session_id,
            "snippets": [],
            "summary": "",
            "source": "memory_fusion",
        }
    # Substrate may not support retrieve by memory_id; use project_id/session_id as filter
    results = substrate.retrieve(
        project_id=project_id,
        session_id=session_id,
        limit=limit,
    )
    snippets = []
    for r in results:
        mid = r.get("memory_id", r.get("id", ""))
        text = r.get("text", r.get("content", r.get("summary", "")))
        if isinstance(text, str) and text.strip():
            snippets.append({"memory_id": mid, "text": text[:300]})
    summary = f"{len(snippets)} memory snippet(s) for project={project_id or '—'} session={session_id or '—'}." if snippets else ""
    return {
        "project_id": project_id,
        "session_id": session_id,
        "snippets": snippets,
        "summary": summary,
        "source": "memory_fusion",
    }


def explain_live_context_memory(
    project_id: str = "",
    session_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Operator-facing: why memory context is (or isn't) present for this project/session."""
    root = _repo_root(repo_root)
    ctx = get_memory_context_for_live_context(project_id, session_id, repo_root=root)
    project_links = len(get_memory_ids_for_entity("project", project_id, root)) if project_id else 0
    session_links = len(get_memory_ids_for_entity("session", session_id, root)) if session_id else 0
    return {
        "project_id": project_id or "—",
        "session_id": session_id or "—",
        "memory_links_to_project": project_links,
        "memory_links_to_session": session_links,
        "snippets_returned": len(ctx.get("snippets", [])),
        "explanation": ctx.get("summary", "No memory substrate or no links for this context."),
    }
