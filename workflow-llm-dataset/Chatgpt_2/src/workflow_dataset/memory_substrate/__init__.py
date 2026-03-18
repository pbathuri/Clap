"""
M43I–M43L: Memory substrate facade — memory-backed slices for learning-lab, candidate-model studio, benchmarks; Cursor bridge.
M43A–M43D: Memory backbone — items, units, backends, compression, retrieval, store.
"""

from workflow_dataset.memory_substrate.models import (
    MemorySliceSummary,
    MemoryBackedRef,
    MemoryItem,
    CompressedMemoryUnit,
    MemorySource,
    MemorySessionLink,
    Provenance,
    MemoryStorageBackend,
    RetrievalIntent,
    MemoryRetentionState,
)
from workflow_dataset.memory_substrate.slices import list_memory_slices, get_memory_slice_refs
from workflow_dataset.memory_substrate.cursor_bridge import build_cursor_bridge_report
from workflow_dataset.memory_substrate.store import (
    ingest,
    store_unit,
    retrieve_units,
    list_sessions,
    get_status,
    get_backends,
)

__all__ = [
    "MemorySliceSummary",
    "MemoryBackedRef",
    "MemoryItem",
    "CompressedMemoryUnit",
    "MemorySource",
    "MemorySessionLink",
    "Provenance",
    "MemoryStorageBackend",
    "RetrievalIntent",
    "MemoryRetentionState",
    "list_memory_slices",
    "get_memory_slice_refs",
    "build_cursor_bridge_report",
    "ingest",
    "store_unit",
    "retrieve_units",
    "list_sessions",
    "get_status",
    "get_backends",
    "get_store",
]
