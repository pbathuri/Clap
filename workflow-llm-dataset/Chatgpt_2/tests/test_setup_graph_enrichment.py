"""Tests for setup graph enrichment: new node types and edges."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from workflow_dataset.personal.graph_store import init_store, count_nodes, count_edges
from workflow_dataset.setup.graph_enrichment import (
    add_artifact_node,
    add_domain_node,
    add_style_pattern_node,
    add_workflow_hint_node,
    link_project_to_domain,
    link_style_pattern_to_project,
    get_or_create_project,
    get_or_create_family_node,
)
from workflow_dataset.personal.work_graph import NodeType


@pytest.fixture
def graph_conn(tmp_path: Path) -> sqlite3.Connection:
    db = tmp_path / "graph.sqlite"
    init_store(db)
    return sqlite3.connect(str(db))


def test_add_domain_node(graph_conn: sqlite3.Connection) -> None:
    nid = add_domain_node(graph_conn, "creative", "Creative / media")
    graph_conn.commit()
    assert count_nodes(graph_conn, NodeType.DOMAIN.value) == 1


def test_add_artifact_node_with_project(graph_conn: sqlite3.Connection) -> None:
    from workflow_dataset.personal.graph_store import add_node
    from workflow_dataset.personal.work_graph import PersonalWorkGraphNode
    proj_id = "project_test1"
    add_node(
        graph_conn,
        PersonalWorkGraphNode(node_id=proj_id, node_type=NodeType.PROJECT, label="Test Project"),
    )
    art_id = add_artifact_node(
        graph_conn,
        "/path/to/doc.txt",
        "text_document",
        project_id=proj_id,
    )
    graph_conn.commit()
    assert count_edges(graph_conn, "artifact_in_project") >= 1


def test_add_style_pattern_node(graph_conn: sqlite3.Connection) -> None:
    nid = add_style_pattern_node(graph_conn, "revision_naming", "v1", description="Version suffix")
    graph_conn.commit()
    assert count_nodes(graph_conn, NodeType.STYLE_PATTERN.value) == 1


def test_artifact_node_with_family(graph_conn: sqlite3.Connection) -> None:
    """Artifact can be linked to a family node via artifact_has_family."""
    from workflow_dataset.personal.graph_store import add_node
    from workflow_dataset.personal.work_graph import PersonalWorkGraphNode
    proj_id = get_or_create_project(graph_conn, "proj_a", scan_root="/tmp")
    family_id = get_or_create_family_node(graph_conn, "text_document")
    art_id = add_artifact_node(
        graph_conn,
        "/tmp/proj_a/readme.txt",
        "text_document",
        project_id=proj_id,
        family_node_id=family_id,
    )
    graph_conn.commit()
    assert count_edges(graph_conn, "artifact_in_project") >= 1
    assert count_edges(graph_conn, "artifact_has_family") >= 1


def test_link_style_pattern_to_project(graph_conn: sqlite3.Connection) -> None:
    """Style pattern can be linked to project (style_signature_seen_in_project)."""
    proj_id = get_or_create_project(graph_conn, "proj_b", scan_root="/tmp")
    style_id = add_style_pattern_node(graph_conn, "naming_convention", "snake_case", description="Snake case")
    link_style_pattern_to_project(graph_conn, style_id, proj_id)
    graph_conn.commit()
    assert count_edges(graph_conn, "style_pattern_seen_in_project") >= 1
