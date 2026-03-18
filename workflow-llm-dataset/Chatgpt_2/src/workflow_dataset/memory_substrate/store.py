"""
M43B: Memory substrate store — ingest, store, retrieve, status, backends. Single default backend (SQLite).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_substrate.models import (
    CompressedMemoryUnit,
    MemoryItem,
    MemorySessionLink,
    MemoryStorageBackend,
    RetrievalIntent,
)
from workflow_dataset.memory_substrate.backends import SQLiteBackend, InMemoryBackend
from workflow_dataset.memory_substrate.compression import compress_item, synthesize_units
from workflow_dataset.memory_substrate.retrieval import retrieve

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_backend(repo_root: Path | str | None) -> MemoryStorageBackend:
    return SQLiteBackend(repo_root)


def ingest(
    items: list[MemoryItem],
    repo_root: Path | str | None = None,
    backend: MemoryStorageBackend | None = None,
    synthesize: bool = False,
) -> list[CompressedMemoryUnit]:
    """
    Ingest raw memory items: compress each to a unit, optionally synthesize, store, return stored units.
    """
    be = backend or _default_backend(repo_root)
    units = [compress_item(item) for item in items]
    if synthesize and len(units) > 1:
        units = synthesize_units(units)
    for u in units:
        link = MemorySessionLink(
            link_id=stable_id("link", u.unit_id, u.session_id, prefix="ml_"),
            unit_id=u.unit_id,
            session_id=u.session_id or "",
            created_at_utc=u.created_at_utc or utc_now_iso(),
        )
        be.store(u, link if u.session_id else None)
    return units


def store_unit(
    unit: CompressedMemoryUnit,
    repo_root: Path | str | None = None,
    backend: MemoryStorageBackend | None = None,
) -> None:
    """Store a single compressed unit and its session link."""
    be = backend or _default_backend(repo_root)
    link = MemorySessionLink(
        link_id=stable_id("link", unit.unit_id, unit.session_id, prefix="ml_"),
        unit_id=unit.unit_id,
        session_id=unit.session_id or "",
        created_at_utc=unit.created_at_utc or utc_now_iso(),
    )
    be.store(unit, link if unit.session_id else None)


def retrieve_units(
    intent: RetrievalIntent,
    repo_root: Path | str | None = None,
    backend: MemoryStorageBackend | None = None,
) -> list[CompressedMemoryUnit]:
    """Retrieve units by intent (keyword + structured)."""
    be = backend or _default_backend(repo_root)
    return retrieve(be, intent)


def list_sessions(
    limit: int = 50,
    repo_root: Path | str | None = None,
    backend: MemoryStorageBackend | None = None,
) -> list[str]:
    """List session IDs that have memory units."""
    be = backend or _default_backend(repo_root)
    return be.list_sessions(limit)


def get_status(
    repo_root: Path | str | None = None,
    backend: MemoryStorageBackend | None = None,
) -> dict[str, Any]:
    """Status: backend id, counts, path if SQLite."""
    be = backend or _default_backend(repo_root)
    return be.get_stats()


def get_backends(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Available backends: sqlite (default), in_memory (for reference)."""
    root = repo_root
    return [
        SQLiteBackend(root).get_stats(),
        {"backend_id": "in_memory", "note": "ephemeral; use for tests"},
    ]
