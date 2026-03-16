"""
M23F-F1: Map task definition to coordination graph. Advisory only.
"""

from __future__ import annotations

from workflow_dataset.task_demos.models import TaskDefinition, TaskStep
from workflow_dataset.coordination_graph.models import (
    CoordinationGraph,
    GraphNode,
    GraphEdge,
    EDGE_TYPE_SEQUENCE,
    NODE_TYPE_FILE,
    NODE_TYPE_NOTES,
    NODE_TYPE_BROWSER,
    NODE_TYPE_APP,
    NODE_TYPE_ARTIFACT,
)


def _adapter_to_node_type(adapter_id: str) -> str:
    if adapter_id == "file_ops":
        return NODE_TYPE_FILE
    if adapter_id == "notes_document":
        return NODE_TYPE_NOTES
    if adapter_id == "browser_open":
        return NODE_TYPE_BROWSER
    if adapter_id == "app_launch":
        return NODE_TYPE_APP
    return "app"


def task_definition_to_graph(
    task: TaskDefinition,
    include_artifact_nodes: bool = False,
) -> CoordinationGraph:
    """
    Build coordination graph from task definition. One node per step; edges step_i -> step_i+1.
    Optional: insert advisory artifact nodes between steps (include_artifact_nodes=True).
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for i, step in enumerate(task.steps):
        node_id = f"step_{i}"
        node_type = _adapter_to_node_type(step.adapter_id)
        label = f"{step.adapter_id}:{step.action_id}"
        nodes.append(GraphNode(
            id=node_id,
            type=node_type,
            label=label,
            adapter_id=step.adapter_id,
            action_id=step.action_id,
            step_index=i,
        ))
        if include_artifact_nodes and i > 0:
            art_id = f"artifact_{i-1}"
            nodes.append(GraphNode(id=art_id, type=NODE_TYPE_ARTIFACT, label="(artifact)"))
            edges.append(GraphEdge(f"step_{i-1}", art_id, EDGE_TYPE_SEQUENCE))
            edges.append(GraphEdge(art_id, node_id, EDGE_TYPE_SEQUENCE))
        elif i > 0:
            edges.append(GraphEdge(f"step_{i-1}", node_id, EDGE_TYPE_SEQUENCE))
    return CoordinationGraph(
        nodes=nodes,
        edges=edges,
        task_id=task.task_id,
        source_task_id=task.task_id,
    )
