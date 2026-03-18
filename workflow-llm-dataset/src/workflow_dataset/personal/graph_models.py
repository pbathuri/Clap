"""
M31E–M31H: Explicit graph models for personal work graph builder — provenance, confidence, edge semantics.
Uses existing NodeType and PersonalWorkGraphNode from work_graph; adds edge/provenance conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Provenance/evidence keys used in node.attributes and in pattern output
ATTR_SOURCE_EVENT_IDS = "source_event_ids"
ATTR_EVIDENCE_COUNT = "evidence_count"
ATTR_LAST_SEEN_UTC = "last_seen_utc"
ATTR_SUPPORTING_SIGNALS = "supporting_signals"

# Relation types (edges)
REL_FILE_IN_FOLDER = "file_in_folder"
REL_FILE_IN_PROJECT = "file_in_project"
REL_ROUTINE_IN_PROJECT = "routine_in_project"
REL_USES_TOOL = "uses_tool"
REL_PRECEDES = "precedes"
REL_PRODUCES_ARTIFACT = "produces_artifact"
REL_PATTERN_IN_PROJECT = "pattern_in_project"
REL_ASSOCIATED_SESSION = "associated_session"


@dataclass
class EdgeRecord:
    """In-memory edge for reports and explain."""
    from_id: str
    to_id: str
    relation_type: str

    def to_dict(self) -> dict[str, Any]:
        return {"from_id": self.from_id, "to_id": self.to_id, "relation_type": self.relation_type}


@dataclass
class ProvenanceMarker:
    """Provenance for a node or edge: event ids and optional confidence."""
    source_event_ids: list[str] = field(default_factory=list)
    confidence: float | None = None
    source: str = "observation"  # observation | teaching | import

    def to_attributes_fragment(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.source_event_ids:
            out[ATTR_SOURCE_EVENT_IDS] = self.source_event_ids[:100]  # cap for storage
        if self.confidence is not None:
            out["confidence_value"] = self.confidence
        out["provenance_source"] = self.source
        return out


def merge_provenance_into_attributes(attributes: dict[str, Any], marker: ProvenanceMarker) -> dict[str, Any]:
    """Merge provenance into a copy of attributes (e.g. for node.attributes)."""
    attrs = dict(attributes)
    existing_ids = list(attrs.get(ATTR_SOURCE_EVENT_IDS) or [])
    for eid in marker.source_event_ids:
        if eid not in existing_ids:
            existing_ids.append(eid)
    attrs[ATTR_SOURCE_EVENT_IDS] = existing_ids[:100]
    if marker.confidence is not None:
        attrs["confidence_value"] = marker.confidence
    attrs["provenance_source"] = marker.source
    return attrs
