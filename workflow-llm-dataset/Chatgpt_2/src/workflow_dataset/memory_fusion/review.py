"""
M43E–M43H: Weak/uncertain memory review — list memories needing operator review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_fusion.links import _load_links, _repo_root


def list_weak_memories(
    confidence_below: float = 0.6,
    needs_review_only: bool = False,
    limit: int = 50,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    List memory links that are weak (low confidence) or marked needs_review.
    Operator can then review or correct links.
    """
    root = _repo_root(repo_root)
    links = _load_links(root)
    out: list[dict[str, Any]] = []
    for l in links:
        if needs_review_only and not l.get("needs_review"):
            continue
        conf = l.get("confidence", 1.0)
        if isinstance(conf, (int, float)) and conf < confidence_below:
            out.append({
                "memory_id": l.get("memory_id"),
                "entity_type": l.get("entity_type"),
                "entity_id": l.get("entity_id"),
                "confidence": conf,
                "needs_review": l.get("needs_review", False),
            })
        elif l.get("needs_review"):
            out.append({
                "memory_id": l.get("memory_id"),
                "entity_type": l.get("entity_type"),
                "entity_id": l.get("entity_id"),
                "confidence": l.get("confidence", 0),
                "needs_review": True,
            })
    return out[:limit]
