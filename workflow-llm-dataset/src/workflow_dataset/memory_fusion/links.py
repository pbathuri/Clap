"""
M43E–M43H: Memory–entity links — memory to project, session, episode, routine.
Stored under data/local/memory_fusion/links.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DIR_NAME = "data/local/memory_fusion"
LINKS_FILE = "links.json"
WEAK_MEMORIES_FILE = "weak_review.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _load_links(root: Path) -> list[dict[str, Any]]:
    path = root / DIR_NAME / LINKS_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("links", []))
    except Exception:
        return []


def _save_links(root: Path, links: list[dict[str, Any]]) -> Path:
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    path = d / LINKS_FILE
    path.write_text(json.dumps({"links": links}, indent=2), encoding="utf-8")
    return path


def add_link(
    memory_id: str,
    entity_type: str,
    entity_id: str,
    confidence: float = 1.0,
    needs_review: bool = False,
    repo_root: Path | str | None = None,
) -> None:
    """Record a link from memory_id to entity (project, session, episode, routine)."""
    root = _repo_root(repo_root)
    links = _load_links(root)
    key = (memory_id, entity_type, entity_id)
    existing = [i for i in links if (i.get("memory_id"), i.get("entity_type"), i.get("entity_id")) == key]
    if existing:
        existing[0]["confidence"] = confidence
        existing[0]["needs_review"] = needs_review
    else:
        links.append({
            "memory_id": memory_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "confidence": confidence,
            "needs_review": needs_review,
        })
    if len(links) > 2000:
        links = links[-2000:]
    _save_links(root, links)


def get_links_for_entity(
    entity_type: str,
    entity_id: str,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return all memory links for the given entity."""
    root = _repo_root(repo_root)
    links = _load_links(root)
    return [l for l in links if l.get("entity_type") == entity_type and l.get("entity_id") == entity_id]


def get_memory_ids_for_entity(
    entity_type: str,
    entity_id: str,
    repo_root: Path | str | None = None,
) -> list[str]:
    """Return memory_ids linked to this entity (deduplicated)."""
    links = get_links_for_entity(entity_type, entity_id, repo_root)
    seen: set[str] = set()
    out: list[str] = []
    for l in links:
        mid = l.get("memory_id", "")
        if mid and mid not in seen:
            seen.add(mid)
            out.append(mid)
    return out


def list_memory_links(
    limit: int = 100,
    entity_type: str | None = None,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List recent links, optionally filtered by entity_type."""
    root = _repo_root(repo_root)
    links = _load_links(root)
    if entity_type:
        links = [l for l in links if l.get("entity_type") == entity_type]
    return list(reversed(links[-limit:]))
