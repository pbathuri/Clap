"""
M43C: Bridge to SimpleMem-like shapes. Product uses its own models and storage; these adapters
allow optional translation to/from SimpleMem MemoryEntry/CrossMemoryEntry format for local
cursor_mem reference or future optional integration. No cloud; no import of cursor_mem at module load.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.memory_substrate.models import CompressedMemoryUnit


def unit_to_simplemem_entry_dict(unit: CompressedMemoryUnit) -> dict[str, Any]:
    """
    Convert our CompressedMemoryUnit to a dict shaped like SimpleMem MemoryEntry
    (lossless_restatement, keywords, timestamp, location, persons, entities, topic).
    Used for documentation or optional write to cursor_mem when run locally.
    """
    return {
        "entry_id": unit.unit_id,
        "lossless_restatement": unit.lossless_restatement,
        "keywords": list(unit.keywords),
        "timestamp": unit.timestamp or None,
        "location": unit.location,
        "persons": list(unit.persons),
        "entities": list(unit.entities),
        "topic": unit.topic,
    }


def simplemem_entry_dict_to_unit(
    d: dict[str, Any],
    session_id: str = "",
    source: str = "simplemem_bridge",
    source_ref: str = "",
    created_at_utc: str = "",
) -> CompressedMemoryUnit:
    """
    Convert a SimpleMem MemoryEntry-like dict into our CompressedMemoryUnit.
    """
    return CompressedMemoryUnit(
        unit_id=str(d.get("entry_id", d.get("unit_id", ""))),
        lossless_restatement=str(d.get("lossless_restatement", "")),
        keywords=list(d.get("keywords", [])),
        timestamp=str(d.get("timestamp", "")),
        location=d.get("location"),
        persons=list(d.get("persons", [])),
        entities=list(d.get("entities", [])),
        topic=d.get("topic"),
        session_id=session_id,
        source=source,
        source_ref=source_ref,
        created_at_utc=created_at_utc,
    )
