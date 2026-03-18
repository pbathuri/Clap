"""
M23F-F1: Cross-app coordination graph schema. Advisory only; no execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Node types: file | notes | browser | app | artifact
NODE_TYPE_FILE = "file"
NODE_TYPE_NOTES = "notes"
NODE_TYPE_BROWSER = "browser"
NODE_TYPE_APP = "app"
NODE_TYPE_ARTIFACT = "artifact"

EDGE_TYPE_SEQUENCE = "sequence"


@dataclass
class GraphNode:
    """One node in the coordination graph: step or advisory artifact."""
    id: str
    type: str  # file | notes | browser | app | artifact
    label: str
    adapter_id: str = ""
    action_id: str = ""
    step_index: int | None = None


@dataclass
class GraphEdge:
    """Directed edge: source -> target (e.g. sequence flow)."""
    source_id: str
    target_id: str
    edge_type: str = EDGE_TYPE_SEQUENCE


@dataclass
class CoordinationGraph:
    """Advisory graph: how a task flows across file/notes/browser/app/artifact."""
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    task_id: str = ""
    source_task_id: str = ""
