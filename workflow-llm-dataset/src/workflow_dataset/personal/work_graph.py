"""
Personal work graph: entities and relationships.

Stored on-device only; see docs/schemas/PERSONAL_WORK_GRAPH.md.
"""

from __future__ import annotations

import sqlite3
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

# Optional local graph_store for persistence (avoids circular import at module level)
try:
    from workflow_dataset.personal import graph_store as _graph_store
except ImportError:
    _graph_store = None


class NodeType(str, Enum):
    USER_PROFILE = "user_profile"
    PROJECT = "project"
    FOLDER = "folder"
    RECURRING_TASK = "recurring_task"
    FILE_REF = "file_ref"
    TOOL_APP = "tool_app"
    COLLABORATOR = "collaborator"
    ROUTINE = "routine"
    WORKFLOW_CHAIN = "workflow_chain"
    PREFERENCE = "preference"
    PAIN_POINT = "pain_point"
    GOAL = "goal"
    APPROVAL_BOUNDARY = "approval_boundary"


class PersonalWorkGraphNode(BaseModel):
    """Single node in the personal work graph."""

    node_id: str = Field(..., description="Stable device-local ID")
    node_type: NodeType
    label: str = Field(default="", description="Human-readable label")
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="observation", description="observation | teaching | import")
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


def add_node(
    graph_store: Any,
    node: PersonalWorkGraphNode,
) -> None:
    """Add or update a node in the graph store. graph_store is a sqlite3.Connection or path."""
    if _graph_store is None:
        return
    conn = graph_store if isinstance(graph_store, sqlite3.Connection) else None
    if conn is None and hasattr(graph_store, "path"):
        from workflow_dataset.personal.graph_store import init_store
        init_store(Path(graph_store.path))
        conn = sqlite3.connect(str(graph_store.path))
    if conn is not None:
        _graph_store.add_node(conn, node)
        if not isinstance(graph_store, sqlite3.Connection):
            conn.commit()
            conn.close()


def get_node(graph_store: Any, node_id: str) -> PersonalWorkGraphNode | None:
    """Retrieve a node by ID."""
    if _graph_store is None:
        return None
    conn = graph_store if isinstance(graph_store, sqlite3.Connection) else None
    if conn is None and hasattr(graph_store, "path"):
        conn = sqlite3.connect(str(graph_store.path))
    if conn is None:
        return None
    try:
        return _graph_store.get_node(conn, node_id)
    finally:
        if not isinstance(graph_store, sqlite3.Connection):
            conn.close()


def ingest_file_events(
    store_path: Path | str,
    events: list[Any],
    root_paths: list[Path] | None = None,
    timestamp_utc: str | None = None,
) -> tuple[int, int]:
    """
    Ingest file observation events into the graph. Creates file_ref, folder, project nodes
    and file_in_folder, file_in_project edges. Returns (nodes_created_or_updated, edges_created).
    """
    from workflow_dataset.personal import graph_store as _gs
    from workflow_dataset.personal.graph_store import (
        init_store,
        add_node as _add_node,
        add_edge,
    )

    store_path = Path(store_path)
    init_store(store_path)
    conn = sqlite3.connect(str(store_path))
    ts = timestamp_utc or utc_now_iso()
    roots = [Path(r).resolve() for r in (root_paths or [])]
    nodes_added = 0
    edges_added = 0

    try:
        for evt in events:
            if getattr(evt, "source", None) is None:
                try:
                    src = evt.get("source")
                except (TypeError, AttributeError):
                    continue
            else:
                src = getattr(evt.source, "value", str(evt.source))
            if src != "file":
                continue
            payload = getattr(evt, "payload", evt) if hasattr(evt, "payload") else evt
            if isinstance(payload, dict):
                path_str = payload.get("path")
            else:
                continue
            if not path_str:
                continue
            path_obj = Path(path_str).resolve()
            is_dir = payload.get("is_dir", False)
            filename = payload.get("filename") or path_obj.name

            # Infer project: first path component under any root
            project_label = ""
            for r in roots:
                try:
                    rel = path_obj.relative_to(r)
                    parts = rel.parts
                    if parts:
                        project_label = parts[0]
                    break
                except ValueError:
                    continue
            if not project_label and path_obj.parts:
                project_label = path_obj.parts[-2] if len(path_obj.parts) >= 2 else path_obj.parts[0]

            node_type = NodeType.FOLDER if is_dir else NodeType.FILE_REF
            node_id = stable_id("node", path_str, prefix="node")
            attrs = {k: v for k, v in payload.items() if k not in ("path", "filename", "event_kind")}
            node = PersonalWorkGraphNode(
                node_id=node_id,
                node_type=node_type,
                label=filename,
                attributes=attrs,
                source="observation",
                created_utc=ts,
                updated_utc=ts,
                confidence=0.9,
            )
            _add_node(conn, node)
            nodes_added += 1

            # file_in_folder: link to parent folder
            parent = path_obj.parent
            if str(parent) != str(path_obj) and parent != path_obj:
                parent_id = stable_id("node", str(parent), prefix="node")
                parent_node = _gs.get_node(conn, parent_id)
                if parent_node is None:
                    parent_node = PersonalWorkGraphNode(
                        node_id=parent_id,
                        node_type=NodeType.FOLDER,
                        label=parent.name,
                        attributes={"path": str(parent)},
                        source="observation",
                        created_utc=ts,
                        updated_utc=ts,
                        confidence=0.9,
                    )
                    _add_node(conn, parent_node)
                    nodes_added += 1
                add_edge(conn, node_id, parent_id, "file_in_folder")
                edges_added += 1

            # file_in_project: link to observed_project (top-level folder)
            if project_label:
                project_id = stable_id("project", project_label, prefix="project")
                proj = _gs.get_node(conn, project_id)
                if proj is None:
                    proj = PersonalWorkGraphNode(
                        node_id=project_id,
                        node_type=NodeType.PROJECT,
                        label=project_label,
                        attributes={"inferred_from": "top_level_folder"},
                        source="observation",
                        created_utc=ts,
                        updated_utc=ts,
                        confidence=0.8,
                    )
                    _add_node(conn, proj)
                    nodes_added += 1
                add_edge(conn, node_id, project_id, "file_in_project")
                edges_added += 1

        conn.commit()
    finally:
        conn.close()

    return nodes_added, edges_added


def persist_routines(
    store_path: Path | str,
    routines: list[dict[str, Any]],
    timestamp_utc: str | None = None,
) -> int:
    """
    Persist inferred routines into the graph as ROUTINE nodes.
    Links to project nodes via routine_in_project when routine has a project.
    Returns number of routine nodes written.
    """
    from workflow_dataset.personal import graph_store as _gs
    from workflow_dataset.personal.graph_store import (
        init_store,
        add_node as _add_node,
        add_edge,
    )

    store_path = Path(store_path)
    init_store(store_path)
    conn = sqlite3.connect(str(store_path))
    ts = timestamp_utc or utc_now_iso()
    n = 0
    try:
        for r in routines:
            routine_id = r.get("routine_id") or stable_id("routine", r.get("routine_type", ""), r.get("label", ""), ts, prefix="routine")
            node = PersonalWorkGraphNode(
                node_id=routine_id,
                node_type=NodeType.ROUTINE,
                label=r.get("label", ""),
                attributes={
                    "routine_type": r.get("routine_type", ""),
                    "touch_count": r.get("touch_count", 0),
                    "path": r.get("path", ""),
                    "project": r.get("project", ""),
                    "extensions": r.get("extensions", []),
                    "hours": r.get("hours", []),
                    "supporting_signals": r.get("supporting_signals", []),
                },
                source="observation",
                created_utc=ts,
                updated_utc=ts,
                confidence=r.get("confidence"),
            )
            _add_node(conn, node)
            n += 1
            project = r.get("project", "").strip()
            if project:
                project_id = stable_id("project", project, prefix="project")
                add_edge(conn, routine_id, project_id, "routine_in_project")
        conn.commit()
    finally:
        conn.close()
    return n
