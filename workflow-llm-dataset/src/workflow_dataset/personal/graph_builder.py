"""
M31E–M31H: Event-to-graph ingestion — consume normalized events, create/update nodes and edges, record provenance.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.personal.work_graph import NodeType, PersonalWorkGraphNode
from workflow_dataset.personal.graph_store import (
    init_store,
    add_node as _add_node,
    add_edge,
    get_node as _get_node,
)
from workflow_dataset.personal.graph_models import ATTR_SOURCE_EVENT_IDS, merge_provenance_into_attributes
from workflow_dataset.personal import graph_store as _gs
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _event_source(evt: Any) -> str:
    if getattr(evt, "source", None) is not None:
        return getattr(evt.source, "value", str(evt.source))
    try:
        return evt.get("source", "") if isinstance(evt, dict) else ""
    except (TypeError, AttributeError):
        return ""


def _event_id(evt: Any) -> str:
    if hasattr(evt, "event_id"):
        return getattr(evt, "event_id", "")
    try:
        return evt.get("event_id", "") if isinstance(evt, dict) else ""
    except (TypeError, AttributeError):
        return ""


def _payload(evt: Any) -> dict[str, Any]:
    if hasattr(evt, "payload"):
        p = getattr(evt, "payload", {})
        return p if isinstance(p, dict) else {}
    try:
        return evt.get("payload", {}) if isinstance(evt, dict) else {}
    except (TypeError, AttributeError):
        return {}


def _append_event_id_to_node(conn: sqlite3.Connection, node_id: str, event_id: str, ts: str) -> bool:
    """Load node, append event_id to source_event_ids, save. Returns True if updated."""
    node = _gs.get_node(conn, node_id)
    if not node:
        return False
    ids = list(node.attributes.get(ATTR_SOURCE_EVENT_IDS) or [])
    if event_id and event_id not in ids:
        ids.append(event_id)
    node.attributes[ATTR_SOURCE_EVENT_IDS] = ids[:100]
    node.updated_utc = ts
    _add_node(conn, node)
    return True


def ingest_events(
    store_path: Path | str,
    events: list[Any],
    root_paths: list[Path] | None = None,
    timestamp_utc: str | None = None,
) -> dict[str, Any]:
    """
    Ingest normalized observation events into the graph. Creates/updates file_ref, folder, project, tool_app
    nodes and file_in_folder, file_in_project, uses_tool edges. Records source_event_ids in node attributes.
    Returns {nodes_created_or_updated, edges_created, by_source: {file: {nodes, edges}, app: {nodes, edges}}}.
    """
    store_path = Path(store_path)
    init_store(store_path)
    conn = sqlite3.connect(str(store_path))
    ts = timestamp_utc or utc_now_iso()
    roots = [Path(r).resolve() for r in (root_paths or [])]
    nodes_delta = 0
    edges_delta = 0
    by_source: dict[str, dict[str, int]] = {"file": {"nodes": 0, "edges": 0}, "app": {"nodes": 0, "edges": 0}}

    try:
        for evt in events:
            src = _event_source(evt)
            eid = _event_id(evt) or stable_id("evt", ts, str(hash(evt))[:8], prefix="evt")
            payload = _payload(evt)

            if src == "file":
                path_str = payload.get("path")
                if not path_str:
                    continue
                path_obj = Path(path_str).resolve()
                is_dir = payload.get("is_dir", False)
                filename = payload.get("filename") or path_obj.name
                project_label = ""
                for r in roots:
                    try:
                        rel = path_obj.relative_to(r)
                        if rel.parts:
                            project_label = rel.parts[0]
                        break
                    except ValueError:
                        continue
                if not project_label and path_obj.parts:
                    project_label = path_obj.parts[-2] if len(path_obj.parts) >= 2 else path_obj.parts[0]

                node_type = NodeType.FOLDER if is_dir else NodeType.FILE_REF
                node_id = stable_id("node", path_str, prefix="node")
                attrs = {k: v for k, v in payload.items() if k not in ("path", "filename", "event_kind")}
                attrs[ATTR_SOURCE_EVENT_IDS] = attrs.get(ATTR_SOURCE_EVENT_IDS) or []
                if eid not in attrs[ATTR_SOURCE_EVENT_IDS]:
                    attrs[ATTR_SOURCE_EVENT_IDS].append(eid)
                attrs[ATTR_SOURCE_EVENT_IDS] = attrs[ATTR_SOURCE_EVENT_IDS][:100]

                existing = _gs.get_node(conn, node_id)
                if existing and existing.attributes.get(ATTR_SOURCE_EVENT_IDS):
                    for x in existing.attributes[ATTR_SOURCE_EVENT_IDS]:
                        if x not in attrs[ATTR_SOURCE_EVENT_IDS]:
                            attrs[ATTR_SOURCE_EVENT_IDS].append(x)
                    attrs[ATTR_SOURCE_EVENT_IDS] = attrs[ATTR_SOURCE_EVENT_IDS][:100]

                node = PersonalWorkGraphNode(
                    node_id=node_id,
                    node_type=node_type,
                    label=filename,
                    attributes=attrs,
                    source="observation",
                    created_utc=existing.created_utc if existing else ts,
                    updated_utc=ts,
                    confidence=0.9,
                )
                _add_node(conn, node)
                nodes_delta += 1
                by_source["file"]["nodes"] += 1

                parent = path_obj.parent
                if str(parent) != str(path_obj) and parent != path_obj:
                    parent_id = stable_id("node", str(parent), prefix="node")
                    parent_node = _gs.get_node(conn, parent_id)
                    if parent_node is None:
                        parent_node = PersonalWorkGraphNode(
                            node_id=parent_id,
                            node_type=NodeType.FOLDER,
                            label=parent.name,
                            attributes={"path": str(parent), ATTR_SOURCE_EVENT_IDS: [eid]},
                            source="observation",
                            created_utc=ts,
                            updated_utc=ts,
                            confidence=0.9,
                        )
                        _add_node(conn, parent_node)
                        nodes_delta += 1
                        by_source["file"]["nodes"] += 1
                    add_edge(conn, node_id, parent_id, "file_in_folder")
                    edges_delta += 1
                    by_source["file"]["edges"] += 1

                if project_label:
                    project_id = stable_id("project", project_label, prefix="project")
                    proj = _gs.get_node(conn, project_id)
                    if proj is None:
                        proj = PersonalWorkGraphNode(
                            node_id=project_id,
                            node_type=NodeType.PROJECT,
                            label=project_label,
                            attributes={"inferred_from": "top_level_folder", ATTR_SOURCE_EVENT_IDS: [eid]},
                            source="observation",
                            created_utc=ts,
                            updated_utc=ts,
                            confidence=0.8,
                        )
                        _add_node(conn, proj)
                        nodes_delta += 1
                        by_source["file"]["nodes"] += 1
                    add_edge(conn, node_id, project_id, "file_in_project")
                    edges_delta += 1
                    by_source["file"]["edges"] += 1

            elif src == "app":
                app_id = payload.get("app_id") or payload.get("bundle_id") or ""
                app_name = payload.get("app_name") or app_id or "unknown"
                if not app_id and not app_name:
                    continue
                tool_node_id = stable_id("tool_app", app_id or app_name, prefix="tool")
                existing = _gs.get_node(conn, tool_node_id)
                attrs = {"app_id": app_id, "app_name": app_name, ATTR_SOURCE_EVENT_IDS: [eid]}
                if existing and existing.attributes.get(ATTR_SOURCE_EVENT_IDS):
                    attrs[ATTR_SOURCE_EVENT_IDS] = list(existing.attributes[ATTR_SOURCE_EVENT_IDS])
                    if eid not in attrs[ATTR_SOURCE_EVENT_IDS]:
                        attrs[ATTR_SOURCE_EVENT_IDS].append(eid)
                    attrs[ATTR_SOURCE_EVENT_IDS] = attrs[ATTR_SOURCE_EVENT_IDS][:100]
                node = PersonalWorkGraphNode(
                    node_id=tool_node_id,
                    node_type=NodeType.TOOL_APP,
                    label=app_name,
                    attributes=attrs,
                    source="observation",
                    created_utc=existing.created_utc if existing else ts,
                    updated_utc=ts,
                    confidence=0.8,
                )
                _add_node(conn, node)
                nodes_delta += 1
                by_source["app"]["nodes"] += 1

        conn.commit()
    finally:
        conn.close()

    return {
        "nodes_created_or_updated": nodes_delta,
        "edges_created": edges_delta,
        "by_source": by_source,
    }


def build_graph_from_recent_events(
    store_path: Path | str,
    log_dir: Path | str,
    root_paths: list[Path] | None = None,
    max_events: int = 5000,
    source_filter: str | None = None,
) -> dict[str, Any]:
    """
    Load recent events from log_dir and ingest into graph. source_filter: None (all) or 'file' or 'app'.
    """
    from workflow_dataset.observe.local_events import load_all_events
    log_dir = Path(log_dir)
    events = load_all_events(log_dir, source_filter=source_filter, max_events=max_events)
    return ingest_events(store_path, events, root_paths=root_paths)
