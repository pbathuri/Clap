"""
M44B: Task-aware retrieval surfaces — project, session, episode, continuity, operator, learning, cursor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_os.models import (
    RetrievalSurface,
    RetrievalIntentOS,
    RetrievalScope,
    RETRIEVAL_INTENTS,
    RETRIEVAL_INTENT_RECALL_CONTEXT,
    RETRIEVAL_INTENT_RECALL_BLOCKER,
    RETRIEVAL_INTENT_RECALL_PATTERN,
    RETRIEVAL_INTENT_RECALL_REVIEW_HISTORY,
)

SURFACE_PROJECT = "project"
SURFACE_SESSION = "session"
SURFACE_EPISODE = "episode"
SURFACE_CONTINUITY = "continuity"
SURFACE_OPERATOR = "operator"
SURFACE_LEARNING = "learning"
SURFACE_CURSOR = "cursor"

_SURFACES: list[RetrievalSurface] = [
    RetrievalSurface(
        surface_id=SURFACE_PROJECT,
        label="Project memory",
        description="Memory linked to a project (entity_type=project).",
        entity_types=["project"],
        supports_intents=RETRIEVAL_INTENTS,
    ),
    RetrievalSurface(
        surface_id=SURFACE_SESSION,
        label="Session memory",
        description="Memory linked to a session (entity_type=session).",
        entity_types=["session"],
        supports_intents=RETRIEVAL_INTENTS,
    ),
    RetrievalSurface(
        surface_id=SURFACE_EPISODE,
        label="Workflow episode memory",
        description="Memory linked to a workflow episode (entity_type=episode).",
        entity_types=["episode"],
        supports_intents=RETRIEVAL_INTENTS,
    ),
    RetrievalSurface(
        surface_id=SURFACE_CONTINUITY,
        label="Continuity / resume memory",
        description="Memory for resume and next-session context.",
        entity_types=["project", "session"],
        supports_intents=[RETRIEVAL_INTENT_RECALL_CONTEXT, RETRIEVAL_INTENT_RECALL_BLOCKER],
    ),
    RetrievalSurface(
        surface_id=SURFACE_OPERATOR,
        label="Operator / history memory",
        description="Memory for operator decisions and history.",
        entity_types=["project", "session"],
        supports_intents=RETRIEVAL_INTENTS,
    ),
    RetrievalSurface(
        surface_id=SURFACE_LEARNING,
        label="Learning / eval memory",
        description="Memory slices and learning-lab / benchmark context.",
        entity_types=[],
        supports_intents=[RETRIEVAL_INTENT_RECALL_CONTEXT, RETRIEVAL_INTENT_RECALL_PATTERN, RETRIEVAL_INTENT_RECALL_REVIEW_HISTORY],
    ),
    RetrievalSurface(
        surface_id=SURFACE_CURSOR,
        label="Cursor / coding memory",
        description="Memory for Cursor and coding context (local substrate).",
        entity_types=["project", "session"],
        supports_intents=RETRIEVAL_INTENTS,
    ),
]

def list_surfaces() -> list[RetrievalSurface]:
    """Return all registered retrieval surfaces."""
    return list(_SURFACES)


def get_surface(surface_id: str) -> RetrievalSurface | None:
    """Return surface by id."""
    for s in _SURFACES:
        if s.surface_id == surface_id:
            return s
    return None


def resolve_scope_entity(scope: RetrievalScope) -> tuple[str, str]:
    """Return (entity_type, entity_id) for fusion/substrate from scope. Prefer explicit entity_type/entity_id."""
    if scope.entity_type and scope.entity_id:
        return scope.entity_type, scope.entity_id
    if scope.project_id:
        return "project", scope.project_id
    if scope.session_id:
        return "session", scope.session_id
    if scope.episode_id:
        return "episode", scope.episode_id
    return "", ""


def retrieve_via_surface(
    surface_id: str,
    scope: RetrievalScope,
    intent_os: RetrievalIntentOS,
    repo_root: Path | str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Execute retrieval for the given surface, scope, and intent.
    Returns (list of item dicts with memory_id, text, confidence, tier), (list of weak_memory dicts).
    Delegates to memory_fusion + memory_substrate; learning surface uses slices when applicable.
    """
    root = Path(repo_root).resolve() if repo_root else None
    if not root:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()

    entity_type, entity_id = resolve_scope_entity(scope)
    items: list[dict[str, Any]] = []
    weak: list[dict[str, Any]] = []

    if surface_id == SURFACE_LEARNING:
        try:
            from workflow_dataset.memory_substrate.slices import list_memory_slices
            slices = list_memory_slices(repo_root=root, limit=intent_os.top_k)
            for s in slices:
                items.append({
                    "memory_id": s.memory_slice_id,
                    "text": s.description or s.source_ref,
                    "source": "slices",
                    "confidence": 0.9 if s.scope == "production_safe" else 0.7,
                    "tier": "trusted",
                })
        except Exception:
            pass
        return items, weak

    try:
        from workflow_dataset.memory_fusion.substrate import get_memory_substrate
        from workflow_dataset.memory_fusion.links import get_memory_ids_for_entity, get_links_for_entity
        from workflow_dataset.memory_fusion.review import list_weak_memories
    except ImportError:
        return items, weak

    if entity_type and entity_id:
        memory_ids = get_memory_ids_for_entity(entity_type, entity_id, repo_root=root)
        links = get_links_for_entity(entity_type, entity_id, repo_root=root)
        link_confidence: dict[str, float] = {l["memory_id"]: l.get("confidence", 1.0) for l in links if l.get("memory_id")}
        link_review: dict[str, bool] = {l["memory_id"]: l.get("needs_review", False) for l in links if l.get("memory_id")}
    else:
        memory_ids = []
        link_confidence = {}
        link_review = {}

    if memory_ids or scope.session_id or scope.project_id:
        substrate = get_memory_substrate(root)
        raw = substrate.retrieve(
            query=intent_os.query,
            project_id=scope.project_id or "",
            session_id=scope.session_id or "",
            limit=intent_os.top_k,
        )
        for r in raw:
            mid = r.get("memory_id", r.get("id", ""))
            text = r.get("text", r.get("content", r.get("summary", "")))
            conf = link_confidence.get(mid, 0.8)
            needs_review = link_review.get(mid, False)
            tier = "weak" if conf < 0.6 or needs_review else "trusted"
            items.append({
                "memory_id": mid,
                "text": text[:500] if isinstance(text, str) else str(text),
                "source": "substrate",
                "confidence": conf,
                "tier": tier,
            })
            if tier == "weak":
                weak.append({"memory_id": mid, "confidence": conf, "needs_review": needs_review})

    weak_list = list_weak_memories(confidence_below=0.6, limit=20, repo_root=root)
    for w in weak_list:
        if w.get("memory_id") and not any(x.get("memory_id") == w["memory_id"] for x in weak):
            weak.append(w)

    return items[: intent_os.top_k], weak
