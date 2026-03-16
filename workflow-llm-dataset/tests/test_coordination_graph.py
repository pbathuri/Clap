"""M23F-F1: Cross-app coordination graph. Advisory only."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.task_demos import TaskDefinition, TaskStep, save_task, get_task
from workflow_dataset.coordination_graph import (
    task_definition_to_graph,
    format_graph_summary,
    graph_to_dict,
    CoordinationGraph,
    NODE_TYPE_FILE,
    NODE_TYPE_BROWSER,
)


def test_task_definition_to_graph_simple(tmp_path):
    task = TaskDefinition(
        task_id="g1",
        steps=[
            TaskStep("file_ops", "inspect_path", {"path": "/tmp"}),
            TaskStep("browser_open", "open_url", {"url": "https://example.com"}),
        ],
    )
    graph = task_definition_to_graph(task)
    assert graph.task_id == "g1"
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.nodes[0].type == NODE_TYPE_FILE
    assert graph.nodes[0].adapter_id == "file_ops"
    assert graph.nodes[1].type == NODE_TYPE_BROWSER
    assert graph.edges[0].source_id == "step_0"
    assert graph.edges[0].target_id == "step_1"


def test_task_definition_to_graph_with_artifacts():
    task = TaskDefinition("g2", [TaskStep("notes_document", "read_text", {"path": "x.txt"}), TaskStep("file_ops", "list_directory", {"path": "."})])
    graph = task_definition_to_graph(task, include_artifact_nodes=True)
    assert len(graph.nodes) >= 3
    assert len(graph.edges) >= 2
    artifact_labels = [n.label for n in graph.nodes if n.type == "artifact"]
    assert "(artifact)" in artifact_labels


def test_format_graph_summary():
    from workflow_dataset.coordination_graph.models import GraphNode, GraphEdge
    graph = CoordinationGraph(
        nodes=[GraphNode("s0", "file", "file_ops:inspect_path", "file_ops", "inspect_path", 0)],
        edges=[],
        task_id="t1",
    )
    report = format_graph_summary(graph)
    assert "t1" in report
    assert "file" in report
    assert "file_ops" in report


def test_graph_to_dict():
    from workflow_dataset.coordination_graph.models import GraphNode, GraphEdge
    graph = CoordinationGraph(
        nodes=[GraphNode("a", "file", "label")],
        edges=[GraphEdge("a", "b")],
        task_id="x",
    )
    d = graph_to_dict(graph)
    assert d["task_id"] == "x"
    assert len(d["nodes"]) == 1
    assert d["nodes"][0]["type"] == "file"
    assert len(d["edges"]) == 1
    assert d["edges"][0]["source_id"] == "a"


def test_graph_from_stored_task(tmp_path):
    task = TaskDefinition("stored", [TaskStep("app_launch", "launch_app", {"app_name_or_path": "Notes"})])
    save_task(task, tmp_path)
    loaded = get_task("stored", tmp_path)
    assert loaded is not None
    graph = task_definition_to_graph(loaded)
    assert graph.task_id == "stored"
    assert len(graph.nodes) == 1
    assert graph.nodes[0].type == "app"
