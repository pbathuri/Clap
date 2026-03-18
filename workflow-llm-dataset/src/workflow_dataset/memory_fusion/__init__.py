"""
M43E–M43H: Product memory fusion — connect memory substrate to personal graph, sessions, live context, continuity.
"""

from __future__ import annotations

from workflow_dataset.memory_fusion.substrate import get_memory_substrate, StubMemorySubstrate
from workflow_dataset.memory_fusion.links import (
    add_link,
    get_links_for_entity,
    get_memory_ids_for_entity,
    list_memory_links,
)
from workflow_dataset.memory_fusion.live_context_integration import (
    get_memory_context_for_live_context,
    explain_live_context_memory,
)
from workflow_dataset.memory_fusion.continuity_integration import get_memory_context_for_continuity
from workflow_dataset.memory_fusion.review import list_weak_memories

__all__ = [
    "get_memory_substrate",
    "StubMemorySubstrate",
    "add_link",
    "get_links_for_entity",
    "get_memory_ids_for_entity",
    "list_memory_links",
    "get_memory_context_for_live_context",
    "explain_live_context_memory",
    "get_memory_context_for_continuity",
    "list_weak_memories",
]
