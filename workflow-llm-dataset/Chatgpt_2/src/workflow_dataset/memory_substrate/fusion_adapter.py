"""
M43 integration: Adapter so memory_fusion (Pane 2) can use memory_substrate (Pane 1).
Exposes retrieve(project_id, session_id, limit) -> list[dict], store(entry) -> memory_id, link() no-op.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_substrate.store import ingest, retrieve_units
from workflow_dataset.memory_substrate.models import MemoryItem, RetrievalIntent


def get_store(repo_root: Path | str | None = None) -> MemorySubstrateStoreAdapter:
    """Return an adapter that implements the protocol expected by memory_fusion.substrate."""
    return MemorySubstrateStoreAdapter(repo_root=repo_root)


class MemorySubstrateStoreAdapter:
    """
    Adapter: Pane 1 store/retrieve_units behind the interface Pane 2 expects.
    - retrieve(project_id, session_id, limit) -> list[dict] with memory_id, text
    - store(entry: dict) -> memory_id (entry may have text/content/summary, session_id, source)
    - link() no-op; links are managed by memory_fusion.links.add_link.
    """

    def __init__(self, repo_root: Path | str | None = None) -> None:
        self._repo_root = repo_root

    def retrieve(
        self,
        query: str = "",
        project_id: str = "",
        session_id: str = "",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return list of dicts with memory_id and text (lossless_restatement) for fusion."""
        intent = RetrievalIntent(
            query=query,
            top_k=limit,
            session_id=session_id or None,
        )
        units = retrieve_units(intent, repo_root=self._repo_root)
        out: list[dict[str, Any]] = []
        for u in units:
            out.append({
                "memory_id": u.unit_id,
                "id": u.unit_id,
                "text": u.lossless_restatement,
                "content": u.lossless_restatement,
                "summary": u.lossless_restatement[:200] if u.lossless_restatement else "",
            })
        return out

    def store(self, entry: dict[str, Any]) -> str:
        """Store entry (text/content/summary, session_id, source); return memory_id."""
        content = (
            entry.get("text")
            or entry.get("content")
            or entry.get("summary")
            or ""
        )
        if not content:
            return ""
        try:
            from workflow_dataset.utils.dates import utc_now_iso
        except Exception:
            from datetime import datetime, timezone
            def utc_now_iso() -> str:
                return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            from workflow_dataset.utils.hashes import stable_id
        except Exception:
            def stable_id(*parts: str, prefix: str = "") -> str:
                import hashlib
                return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]
        item = MemoryItem(
            item_id=stable_id("item", content[:100], utc_now_iso(), prefix="mi_"),
            content=content,
            source=entry.get("source", "memory_fusion"),
            source_ref=entry.get("source_ref", ""),
            timestamp_utc=entry.get("timestamp_utc", utc_now_iso()),
            session_id=entry.get("session_id", ""),
        )
        units = ingest([item], repo_root=self._repo_root)
        return units[0].unit_id if units else ""

    def link(self, memory_id: str, entity_type: str, entity_id: str) -> None:
        """No-op; links are recorded via memory_fusion.links.add_link to avoid circular dependency."""
        pass
