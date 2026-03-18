"""
M23F-F1: Export coordination graph to dict/JSON. Advisory only.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.coordination_graph.models import CoordinationGraph, GraphNode, GraphEdge


def graph_to_dict(graph: CoordinationGraph) -> dict[str, Any]:
    """Serialize coordination graph to a JSON-serializable dict."""
    return {
        "task_id": graph.task_id,
        "source_task_id": graph.source_task_id,
        "nodes": [
            {
                "id": n.id,
                "type": n.type,
                "label": n.label,
                "adapter_id": n.adapter_id,
                "action_id": n.action_id,
                "step_index": n.step_index,
            }
            for n in graph.nodes
        ],
        "edges": [
            {"source_id": e.source_id, "target_id": e.target_id, "edge_type": e.edge_type}
            for e in graph.edges
        ],
    }
