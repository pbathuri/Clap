"""
M31E–M31H: Personal work graph builder + routine mining — ingestion, patterns, provenance, explain.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.personal.graph_store import (
    init_store,
    add_node,
    add_edge,
    get_node,
    list_nodes,
    list_edges,
    count_nodes,
    count_edges,
)
from workflow_dataset.personal.work_graph import NodeType, PersonalWorkGraphNode
from workflow_dataset.personal.graph_models import (
    ATTR_SOURCE_EVENT_IDS,
    merge_provenance_into_attributes,
    ProvenanceMarker,
)
from workflow_dataset.personal.graph_builder import ingest_events, _event_source, _event_id, _payload
from workflow_dataset.personal.pattern_mining import (
    task_sequence_patterns,
    file_flow_patterns,
    session_shape_patterns,
    repeated_block_patterns_personal,
    repeated_success_patterns_personal,
    all_routines_from_events,
    all_patterns,
)
from workflow_dataset.personal.graph_reports import (
    graph_status,
    list_recent_routines,
    explain_node,
)


def test_list_edges_empty(tmp_path: Path) -> None:
    init_store(tmp_path / "g.sqlite")
    import sqlite3
    conn = sqlite3.connect(str(tmp_path / "g.sqlite"))
    try:
        edges = list_edges(conn, limit=10)
        assert edges == []
    finally:
        conn.close()


def test_list_edges_after_add(tmp_path: Path) -> None:
    init_store(tmp_path / "g.sqlite")
    import sqlite3
    conn = sqlite3.connect(str(tmp_path / "g.sqlite"))
    try:
        add_node(conn, PersonalWorkGraphNode(node_id="a", node_type=NodeType.PROJECT, label="A", created_utc="", updated_utc=""))
        add_node(conn, PersonalWorkGraphNode(node_id="b", node_type=NodeType.ROUTINE, label="B", created_utc="", updated_utc=""))
        add_edge(conn, "b", "a", "routine_in_project")
        edges = list_edges(conn, from_id="b")
        assert len(edges) == 1
        assert edges[0]["to_id"] == "a"
        assert edges[0]["relation_type"] == "routine_in_project"
    finally:
        conn.close()


def test_provenance_merge() -> None:
    attrs = {"path": "/x"}
    marker = ProvenanceMarker(source_event_ids=["evt_1"], confidence=0.8)
    out = merge_provenance_into_attributes(attrs, marker)
    assert out[ATTR_SOURCE_EVENT_IDS] == ["evt_1"]
    assert out.get("confidence_value") == 0.8


def test_ingest_events_file_only(tmp_path: Path) -> None:
    events = [
        {"source": "file", "event_id": "e1", "payload": {"path": str(tmp_path / "a" / "f.txt"), "filename": "f.txt", "is_dir": False}},
    ]
    root_paths = [tmp_path]
    result = ingest_events(tmp_path / "graph.sqlite", events, root_paths=root_paths)
    assert result["nodes_created_or_updated"] >= 1
    assert result["edges_created"] >= 1
    assert result["by_source"]["file"]["nodes"] >= 1


def test_ingest_events_app(tmp_path: Path) -> None:
    events = [
        {"source": "app", "event_id": "e2", "payload": {"app_id": "com.test.app", "app_name": "TestApp"}},
    ]
    result = ingest_events(tmp_path / "graph2.sqlite", events)
    assert result["nodes_created_or_updated"] >= 1
    assert result["by_source"]["app"]["nodes"] >= 1


def test_event_helpers() -> None:
    class Evt:
        source = type("Src", (), {"value": "file"})()
        event_id = "evt_1"
        payload = {"path": "/x"}
    evt = Evt()
    assert _event_source(evt) == "file"
    assert _event_id(evt) == "evt_1"
    assert _payload(evt) == {"path": "/x"}


def test_task_sequence_patterns_empty(tmp_path: Path) -> None:
    out = task_sequence_patterns(repo_root=tmp_path, min_occurrences=2)
    assert isinstance(out, list)


def test_file_flow_patterns_empty() -> None:
    out = file_flow_patterns([], min_occurrences=2)
    assert out == []


def test_file_flow_patterns_with_events(tmp_path: Path) -> None:
    events = [
        {"path": "/a/f.py", "path_obj": Path("/a/f.py"), "project": "a", "extension": "py", "timestamp_utc": "2025-01-01T10:00:00Z"},
        {"path": "/a/g.md", "path_obj": Path("/a/g.md"), "project": "a", "extension": "md", "timestamp_utc": "2025-01-01T10:01:00Z"},
        {"path": "/a/h.json", "path_obj": Path("/a/h.json"), "project": "a", "extension": "json", "timestamp_utc": "2025-01-01T10:02:00Z"},
        {"path": "/a/f2.py", "path_obj": Path("/a/f2.py"), "project": "a", "extension": "py", "timestamp_utc": "2025-01-01T11:00:00Z"},
        {"path": "/a/g2.md", "path_obj": Path("/a/g2.md"), "project": "a", "extension": "md", "timestamp_utc": "2025-01-01T11:01:00Z"},
        {"path": "/a/h2.json", "path_obj": Path("/a/h2.json"), "project": "a", "extension": "json", "timestamp_utc": "2025-01-01T11:02:00Z"},
    ]
    out = file_flow_patterns(events, min_occurrences=2, sequence_length=3)
    assert isinstance(out, list)


def test_session_shape_patterns_empty(tmp_path: Path) -> None:
    out = session_shape_patterns(repo_root=tmp_path)
    assert isinstance(out, list)


def test_repeated_block_patterns_personal(tmp_path: Path) -> None:
    out = repeated_block_patterns_personal(repo_root=tmp_path, min_occurrences=2)
    assert isinstance(out, list)


def test_repeated_success_patterns_personal(tmp_path: Path) -> None:
    out = repeated_success_patterns_personal(repo_root=tmp_path, min_occurrences=2)
    assert isinstance(out, list)


def test_all_routines_from_events_empty() -> None:
    out = all_routines_from_events([])
    assert out == []


def test_all_patterns_no_events(tmp_path: Path) -> None:
    out = all_patterns(repo_root=tmp_path, events=None)
    assert isinstance(out, list)


def test_graph_status_no_graph(tmp_path: Path) -> None:
    st = graph_status(repo_root=tmp_path, graph_path=tmp_path / "nonexistent.sqlite")
    assert st["exists"] is False
    assert st["nodes_total"] == 0


def test_graph_status_with_graph(tmp_path: Path) -> None:
    init_store(tmp_path / "g.sqlite")
    import sqlite3
    conn = sqlite3.connect(str(tmp_path / "g.sqlite"))
    try:
        add_node(conn, PersonalWorkGraphNode(node_id="r1", node_type=NodeType.ROUTINE, label="Routine 1", created_utc="", updated_utc=""))
        conn.commit()
    finally:
        conn.close()
    st = graph_status(repo_root=tmp_path, graph_path=tmp_path / "g.sqlite")
    assert st["exists"] is True
    assert st["nodes_total"] >= 1
    assert st["routines_count"] >= 1


def test_list_recent_routines_empty(tmp_path: Path) -> None:
    out = list_recent_routines(repo_root=tmp_path, graph_path=tmp_path / "nonexistent.sqlite")
    assert out == []


def test_explain_node_not_found(tmp_path: Path) -> None:
    init_store(tmp_path / "g.sqlite")
    ex = explain_node("nonexistent_id", repo_root=tmp_path, graph_path=tmp_path / "g.sqlite")
    assert ex.get("error") == "node_not_found"


def test_explain_node_found(tmp_path: Path) -> None:
    init_store(tmp_path / "g.sqlite")
    import sqlite3
    conn = sqlite3.connect(str(tmp_path / "g.sqlite"))
    try:
        add_node(conn, PersonalWorkGraphNode(
            node_id="r1",
            node_type=NodeType.ROUTINE,
            label="Test routine",
            attributes={ATTR_SOURCE_EVENT_IDS: ["evt_1"]},
            created_utc="",
            updated_utc="",
        ))
        add_edge(conn, "r1", "project_1", "routine_in_project")
        conn.commit()
    finally:
        conn.close()
    ex = explain_node("r1", repo_root=tmp_path, graph_path=tmp_path / "g.sqlite")
    assert ex.get("error") is None
    assert ex.get("node_id") == "r1"
    assert ex.get("node_type") == "routine"
    assert ex.get("source_event_count") == 1
    assert any(e["relation_type"] == "routine_in_project" for e in ex.get("out_edges", []))
