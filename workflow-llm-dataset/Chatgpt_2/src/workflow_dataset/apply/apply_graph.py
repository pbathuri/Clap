"""
Persist apply request, plan, result, and rollback record nodes into the personal graph.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.personal.graph_store import init_store, add_node, add_edge, get_node
from workflow_dataset.personal.work_graph import NodeType, PersonalWorkGraphNode
from workflow_dataset.utils.dates import utc_now_iso


def _ensure_conn(conn_or_path: sqlite3.Connection | Path | str) -> sqlite3.Connection:
    if isinstance(conn_or_path, sqlite3.Connection):
        return conn_or_path
    path = Path(conn_or_path)
    init_store(path)
    return sqlite3.connect(str(path))


def persist_apply_request(
    conn_or_path: sqlite3.Connection | Path | str,
    request: Any,
    workspace_node_id: str = "",
    project_node_id: str = "",
) -> None:
    """Write apply_request node and edges to workspace / project."""
    from workflow_dataset.utils.hashes import stable_id
    conn = _ensure_conn(conn_or_path)
    aid = getattr(request, "apply_id", "") or stable_id("apply", utc_now_iso(), prefix="apply")
    ts = getattr(request, "created_utc", utc_now_iso()) or utc_now_iso()
    node = PersonalWorkGraphNode(
        node_id=aid,
        node_type=NodeType.APPLY_REQUEST,
        label=f"Apply {aid[:14]}",
        attributes={
            "workspace_path": getattr(request, "workspace_path", ""),
            "target_root": getattr(request, "target_root", ""),
            "user_confirmed": getattr(request, "user_confirmed", False),
        },
        source="apply",
        created_utc=ts,
        updated_utc=utc_now_iso(),
        confidence=1.0,
    )
    add_node(conn, node)
    if workspace_node_id and get_node(conn, workspace_node_id):
        add_edge(conn, workspace_node_id, aid, "apply_request_for_workspace")
    if project_node_id and get_node(conn, project_node_id):
        add_edge(conn, project_node_id, aid, "apply_request_for_project")
    if not isinstance(conn_or_path, sqlite3.Connection):
        conn.commit()
        conn.close()


def persist_apply_plan_node(
    conn_or_path: sqlite3.Connection | Path | str,
    plan: Any,
    apply_request_id: str,
) -> None:
    """Write apply_plan node and edge to apply_request."""
    from workflow_dataset.utils.hashes import stable_id
    conn = _ensure_conn(conn_or_path)
    pid = getattr(plan, "plan_id", "") or stable_id("plan", apply_request_id, utc_now_iso(), prefix="plan")
    node = PersonalWorkGraphNode(
        node_id=pid,
        node_type=NodeType.APPLY_PLAN,
        label=f"Plan {pid[:12]}",
        attributes={
            "apply_id": getattr(plan, "apply_id", ""),
            "estimated_file_count": getattr(plan, "estimated_file_count", 0),
            "conflicts_count": len(getattr(plan, "conflicts", [])),
        },
        source="apply",
        created_utc=getattr(plan, "created_utc", utc_now_iso()),
        updated_utc=utc_now_iso(),
        confidence=1.0,
    )
    add_node(conn, node)
    add_edge(conn, apply_request_id, pid, "apply_plan_generated_for_request")
    if not isinstance(conn_or_path, sqlite3.Connection):
        conn.commit()
        conn.close()


def persist_apply_result_node(
    conn_or_path: sqlite3.Connection | Path | str,
    result: Any,
    apply_request_id: str,
) -> None:
    """Write applied_artifact-style tracking and rollback record ref."""
    from workflow_dataset.utils.hashes import stable_id
    conn = _ensure_conn(conn_or_path)
    rid = getattr(result, "result_id", "") or stable_id("result", apply_request_id, utc_now_iso(), prefix="result")
    node = PersonalWorkGraphNode(
        node_id=rid,
        node_type=NodeType.APPLIED_ARTIFACT,
        label=f"Apply result {rid[:12]}",
        attributes={
            "apply_id": getattr(result, "apply_id", ""),
            "applied_count": len(getattr(result, "applied_paths", [])),
            "rollback_token": getattr(result, "rollback_token", ""),
        },
        source="apply",
        created_utc=getattr(result, "created_utc", utc_now_iso()),
        updated_utc=utc_now_iso(),
        confidence=1.0,
    )
    add_node(conn, node)
    add_edge(conn, apply_request_id, rid, "artifact_applied_to_target")
    if getattr(result, "rollback_token", ""):
        rb_id = f"rollback_{result.rollback_token}"
        rb_node = PersonalWorkGraphNode(
            node_id=rb_id,
            node_type=NodeType.ROLLBACK_RECORD,
            label=result.rollback_token[:16],
            attributes={"rollback_token": result.rollback_token},
            source="apply",
            created_utc=utc_now_iso(),
            updated_utc=utc_now_iso(),
            confidence=1.0,
        )
        add_node(conn, rb_node)
        add_edge(conn, rid, rb_id, "apply_has_rollback_record")
    if not isinstance(conn_or_path, sqlite3.Connection):
        conn.commit()
        conn.close()
