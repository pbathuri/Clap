"""
M43I–M43L: Memory substrate models — memory slice summary, backed ref, production-safe vs experimental.
M43A–M43D: Memory item, compressed unit, source, session link, provenance, backend protocol, retrieval intent, retention state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# Scope for memory use (Cursor bridge and benchmarks)
MEMORY_SCOPE_PRODUCTION_SAFE = "production_safe"
MEMORY_SCOPE_EXPERIMENTAL = "experimental"


# ----- M43A: Core memory types -----


@dataclass
class MemoryItem:
    """Raw ingestible memory item (before compression)."""
    item_id: str = ""
    content: str = ""
    source: str = ""  # e.g. observe, session, learning_lab, manual
    source_ref: str = ""  # optional ref into source (e.g. event_id, session_id)
    timestamp_utc: str = ""
    session_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "content": self.content,
            "source": self.source,
            "source_ref": self.source_ref,
            "timestamp_utc": self.timestamp_utc,
            "session_id": self.session_id,
            "metadata": dict(self.metadata),
        }


@dataclass
class CompressedMemoryUnit:
    """Compressed memory unit (restatement + keywords + metadata) for storage and retrieval."""
    unit_id: str = ""
    lossless_restatement: str = ""
    keywords: list[str] = field(default_factory=list)
    timestamp: str = ""
    location: str | None = None
    persons: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    topic: str | None = None
    session_id: str = ""
    source: str = ""
    source_ref: str = ""
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "lossless_restatement": self.lossless_restatement,
            "keywords": list(self.keywords),
            "timestamp": self.timestamp,
            "location": self.location,
            "persons": list(self.persons),
            "entities": list(self.entities),
            "topic": self.topic,
            "session_id": self.session_id,
            "source": self.source,
            "source_ref": self.source_ref,
            "created_at_utc": self.created_at_utc,
        }


@dataclass
class MemorySource:
    """Identifies where a memory item/unit originated."""
    source_id: str = ""
    kind: str = ""  # observe | session | learning_lab | manual | correction
    ref: str = ""
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "kind": self.kind,
            "ref": self.ref,
            "label": self.label,
        }


@dataclass
class MemorySessionLink:
    """Links a memory unit to a session (existing Session model)."""
    link_id: str = ""
    unit_id: str = ""
    session_id: str = ""
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "link_id": self.link_id,
            "unit_id": self.unit_id,
            "session_id": self.session_id,
            "created_at_utc": self.created_at_utc,
        }


@dataclass
class Provenance:
    """Provenance/evidence for a memory unit (traceability)."""
    provenance_id: str = ""
    unit_id: str = ""
    source_kind: str = ""
    source_id: str = ""
    score: float = 0.0
    timestamp_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_id": self.provenance_id,
            "unit_id": self.unit_id,
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "score": self.score,
            "timestamp_utc": self.timestamp_utc,
        }


@runtime_checkable
class MemoryStorageBackend(Protocol):
    """Protocol for memory storage backends (SQLite, in-memory, optional vector)."""

    def store(self, unit: CompressedMemoryUnit, link: MemorySessionLink | None) -> None: ...
    def get(self, unit_id: str) -> CompressedMemoryUnit | None: ...
    def list_units(self, session_id: str | None, limit: int) -> list[CompressedMemoryUnit]: ...
    def search_keyword(self, query: str, top_k: int, session_id: str | None) -> list[CompressedMemoryUnit]: ...
    def search_structured(self, session_id: str | None, source: str | None, limit: int) -> list[CompressedMemoryUnit]: ...
    def list_sessions(self, limit: int) -> list[str]: ...
    def get_stats(self) -> dict[str, Any]: ...
    def backend_id(self) -> str: ...


@dataclass
class RetrievalIntent:
    """Intent for retrieval (keyword, structured filter, optional semantic)."""
    query: str = ""
    top_k: int = 20
    session_id: str | None = None
    source: str | None = None
    semantic: bool = False  # use vector search if backend supports

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "top_k": self.top_k,
            "session_id": self.session_id,
            "source": self.source,
            "semantic": self.semantic,
        }


@dataclass
class MemoryRetentionState:
    """Retention state for a unit or aggregate (e.g. for eviction/compaction)."""
    unit_id: str = ""
    last_accessed_utc: str = ""
    access_count: int = 0
    retention_tier: str = "default"  # default | pinned | candidate_evict

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "last_accessed_utc": self.last_accessed_utc,
            "access_count": self.access_count,
            "retention_tier": self.retention_tier,
        }


@dataclass
class MemorySliceSummary:
    """Summary of a logical memory slice (backed by evidence/corrections/outcomes)."""
    memory_slice_id: str = ""
    source_type: str = ""  # learning_lab_experiment | candidate_studio_slice | outcomes_aggregate | corrections_set
    source_ref: str = ""  # experiment_id, slice_id, or aggregate key
    description: str = ""
    evidence_count: int = 0
    correction_count: int = 0
    scope: str = MEMORY_SCOPE_EXPERIMENTAL  # production_safe | experimental
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_slice_id": self.memory_slice_id,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "description": self.description,
            "evidence_count": self.evidence_count,
            "correction_count": self.correction_count,
            "scope": self.scope,
            "created_at_utc": self.created_at_utc,
        }


@dataclass
class MemoryBackedRef:
    """Resolved refs for a memory slice (evidence_ids, correction_ids, etc.)."""
    memory_slice_id: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    correction_ids: list[str] = field(default_factory=list)
    issue_ids: list[str] = field(default_factory=list)
    session_ids: list[str] = field(default_factory=list)
    scope: str = MEMORY_SCOPE_EXPERIMENTAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_slice_id": self.memory_slice_id,
            "evidence_ids": list(self.evidence_ids),
            "correction_ids": list(self.correction_ids),
            "issue_ids": list(self.issue_ids),
            "session_ids": list(self.session_ids),
            "scope": self.scope,
        }
