"""
M43E–M43H: Memory substrate adapter — interface for Pane 1 memory substrate; stub when absent.
Consume memory layer; do not implement the substrate itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

# Optional: try to import real substrate from Pane 1 when present
_SUBSTRATE = None


def _try_import_substrate(repo_root: Path | str | None = None) -> Any:
    """Return real memory substrate if available (e.g. from memory_substrate package)."""
    try:
        from workflow_dataset.memory_substrate.fusion_adapter import get_store
        return get_store(repo_root=repo_root)
    except ImportError:
        pass
    try:
        from workflow_dataset import memory_substrate  # noqa: F401
        get_store_fn = getattr(memory_substrate, "get_store", None)
        if get_store_fn is not None:
            return get_store_fn(repo_root=repo_root)
    except ImportError:
        pass
    return None


class MemorySubstrateProtocol(Protocol):
    """Protocol for memory substrate: retrieve and optional store/link."""

    def retrieve(
        self,
        query: str = "",
        project_id: str = "",
        session_id: str = "",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        ...

    def store(self, entry: dict[str, Any]) -> str:
        ...

    def link(self, memory_id: str, entity_type: str, entity_id: str) -> None:
        ...


class StubMemorySubstrate:
    """Stub when no memory substrate is present: retrieve returns empty; store/link no-op."""

    def retrieve(
        self,
        query: str = "",
        project_id: str = "",
        session_id: str = "",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return []

    def store(self, entry: dict[str, Any]) -> str:
        return ""

    def link(self, memory_id: str, entity_type: str, entity_id: str) -> None:
        pass


def get_memory_substrate(repo_root: Path | str | None = None) -> MemorySubstrateProtocol:
    """Return memory substrate implementation (real if available, else stub)."""
    global _SUBSTRATE
    if repo_root is None and _SUBSTRATE is not None:
        return _SUBSTRATE
    real = _try_import_substrate(repo_root)
    if real is not None and hasattr(real, "retrieve"):
        if repo_root is None:
            _SUBSTRATE = real
        return real
    if repo_root is None:
        _SUBSTRATE = StubMemorySubstrate()
        return _SUBSTRATE
    return StubMemorySubstrate()
