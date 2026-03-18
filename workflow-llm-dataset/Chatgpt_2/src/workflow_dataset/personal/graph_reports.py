"""
M31E–M31H: Personal graph reports — status, recent routines, strong patterns, explain node.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.personal.work_graph import NodeType


def _store_path(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _default_graph_path(repo_root: Path | str | None) -> Path:
    try:
        from workflow_dataset.settings import load_settings
        s = load_settings("configs/settings.yaml")
        p = getattr(getattr(s, "paths", None), "graph_store_path", None)
        if p:
            return Path(p).resolve()
    except Exception:
        pass
    return _store_path(repo_root) / "data/local/work_graph.sqlite"


def graph_status(
    repo_root: Path | str | None = None,
    graph_path: Path | str | None = None,
) -> dict[str, Any]:
    """
    Return graph status: node counts by type, edge count, recent routine count, path.
    """
    from workflow_dataset.personal.graph_store import (
        init_store,
        count_nodes,
        count_edges,
        list_nodes,
    )
    root = _store_path(repo_root)
    path = Path(graph_path).resolve() if graph_path else _default_graph_path(root)
    if not path.exists():
        return {
            "graph_path": str(path),
            "exists": False,
            "nodes_total": 0,
            "edges_total": 0,
            "nodes_by_type": {},
            "routines_count": 0,
            "projects_count": 0,
            "tool_apps_count": 0,
        }
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        nodes_total = count_nodes(conn, node_type=None)
        edges_total = count_edges(conn, relation_type=None)
        nodes_by_type: dict[str, int] = {}
        for nt in [NodeType.ROUTINE.value, NodeType.PROJECT.value, NodeType.FILE_REF.value,
                   NodeType.FOLDER.value, NodeType.TOOL_APP.value, NodeType.ARTIFACT_PATTERN.value]:
            c = count_nodes(conn, node_type=nt)
            if c > 0:
                nodes_by_type[nt] = c
        routines_count = count_nodes(conn, node_type=NodeType.ROUTINE.value)
        projects_count = count_nodes(conn, node_type=NodeType.PROJECT.value)
        tool_apps_count = count_nodes(conn, node_type=NodeType.TOOL_APP.value)
        return {
            "graph_path": str(path),
            "exists": True,
            "nodes_total": nodes_total,
            "edges_total": edges_total,
            "nodes_by_type": nodes_by_type,
            "routines_count": routines_count,
            "projects_count": projects_count,
            "tool_apps_count": tool_apps_count,
        }
    finally:
        conn.close()


def list_recent_routines(
    repo_root: Path | str | None = None,
    graph_path: Path | str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List routine nodes from the graph (by updated_utc if available, else by list order)."""
    from workflow_dataset.personal.graph_store import init_store, list_nodes
    root = _store_path(repo_root)
    path = Path(graph_path).resolve() if graph_path else _default_graph_path(root)
    if not path.exists():
        return []
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        rows = list_nodes(conn, node_type=NodeType.ROUTINE.value, limit=limit)
        return [{"node_id": r["node_id"], "label": r["label"], "attributes": r["attributes"]} for r in rows]
    finally:
        conn.close()


def list_strong_patterns(
    repo_root: Path | str | None = None,
    min_confidence: float = 0.5,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Aggregate patterns from pattern_mining and return those with confidence >= min_confidence."""
    from workflow_dataset.personal.pattern_mining import all_patterns
    root = _store_path(repo_root)
    events: list[Any] = []
    try:
        from workflow_dataset.settings import load_settings
        s = load_settings("configs/settings.yaml")
        log_dir = getattr(getattr(s, "paths", None), "event_log_dir", None)
        if log_dir:
            from workflow_dataset.observe.local_events import load_all_events
            events = load_all_events(Path(log_dir), max_events=2000)
    except Exception:
        pass
    root_paths: list[Path] | None = None
    try:
        from workflow_dataset.settings import load_settings
        s = load_settings("configs/settings.yaml")
        fo = getattr(getattr(s, "agent", None), "file_observer", None)
        if fo and getattr(fo, "root_paths", None):
            root_paths = [Path(p).resolve() for p in fo.root_paths]
    except Exception:
        pass
    all_p = all_patterns(repo_root=root, events=events if events else None, root_paths=root_paths)
    out = [p for p in all_p if (p.get("confidence") or 0) >= min_confidence]
    return out[:limit]


def explain_node(
    node_id: str,
    repo_root: Path | str | None = None,
    graph_path: Path | str | None = None,
) -> dict[str, Any]:
    """
    Explain a graph node: node fields, outgoing/incoming edges, provenance (source_event_ids), confidence.
    """
    from workflow_dataset.personal.graph_store import init_store, get_node, list_edges
    from workflow_dataset.personal.graph_models import ATTR_SOURCE_EVENT_IDS
    root = _store_path(repo_root)
    path = Path(graph_path).resolve() if graph_path else _default_graph_path(root)
    if not path.exists():
        return {"node_id": node_id, "error": "graph_not_found", "graph_path": str(path)}
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        node = get_node(conn, node_id)
        if not node:
            return {"node_id": node_id, "error": "node_not_found"}
        out_edges = list_edges(conn, from_id=node_id, limit=100)
        in_edges = list_edges(conn, to_id=node_id, limit=100)
        attrs = node.attributes or {}
        event_ids = attrs.get(ATTR_SOURCE_EVENT_IDS) or []
        return {
            "node_id": node.node_id,
            "node_type": node.node_type.value,
            "label": node.label,
            "source": node.source,
            "confidence": node.confidence,
            "created_utc": node.created_utc,
            "updated_utc": node.updated_utc,
            "source_event_ids": event_ids[:50],
            "source_event_count": len(event_ids),
            "out_edges": [{"to_id": e["to_id"], "relation_type": e["relation_type"]} for e in out_edges],
            "in_edges": [{"from_id": e["from_id"], "relation_type": e["relation_type"]} for e in in_edges],
            "attributes_summary": {k: v for k, v in attrs.items() if k != ATTR_SOURCE_EVENT_IDS},
        }
    finally:
        conn.close()


def uncertain_patterns(
    repo_root: Path | str | None = None,
    max_confidence: float = 0.65,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Patterns with low/uncertain confidence for operator confirmation."""
    from workflow_dataset.personal.pattern_mining import all_patterns
    root = _store_path(repo_root)
    events: list[Any] = []
    try:
        from workflow_dataset.settings import load_settings
        s = load_settings("configs/settings.yaml")
        log_dir = getattr(getattr(s, "paths", None), "event_log_dir", None)
        if log_dir:
            from workflow_dataset.observe.local_events import load_all_events
            events = load_all_events(Path(log_dir), max_events=1000)
    except Exception:
        pass
    root_paths = None
    try:
        from workflow_dataset.settings import load_settings
        s = load_settings("configs/settings.yaml")
        fo = getattr(getattr(s, "agent", None), "file_observer", None)
        if fo and getattr(fo, "root_paths", None):
            root_paths = [Path(p).resolve() for p in fo.root_paths]
    except Exception:
        pass
    all_p = all_patterns(repo_root=root, events=events if events else None, root_paths=root_paths)
    out = [p for p in all_p if (p.get("confidence") or 0) <= max_confidence and (p.get("count") or 0) >= 1]
    return out[:limit]
