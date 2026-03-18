"""
Persist materialized artifact and workspace nodes into the personal graph.

Edges: materialized_from_draft, materialized_from_suggestion, materialized_for_project,
materialized_using_style_profile, materialized_in_workspace.
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


def persist_materialization_nodes(
    conn_or_path: sqlite3.Connection | Path | str,
    manifest: Any,
    workspace_path: str | Path,
    project_id_by_label: dict[str, str] | None = None,
) -> int:
    """
    Write workspace node, materialized artifact nodes, and edges.
    manifest: MaterializationManifest.
    workspace_path: path to the sandbox workspace.
    Returns count of artifact nodes added.
    """
    from workflow_dataset.utils.hashes import stable_id
    conn = _ensure_conn(conn_or_path)
    project_id_by_label = project_id_by_label or {}
    ts = utc_now_iso()
    n = 0
    try:
        workspace_id = stable_id("workspace", manifest.request_id, prefix="ws")
        ws_node = PersonalWorkGraphNode(
            node_id=workspace_id,
            node_type=NodeType.WORKSPACE,
            label=f"Workspace {manifest.request_id[:12]}",
            attributes={
                "request_id": manifest.request_id,
                "workspace_path": str(workspace_path),
                "generated_from": manifest.generated_from,
                "output_paths": manifest.output_paths[:50],
                "llm_used": manifest.llm_used,
                "retrieval_used": manifest.retrieval_used,
            },
            source="materialize",
            created_utc=manifest.created_utc or ts,
            updated_utc=ts,
            confidence=1.0,
        )
        add_node(conn, ws_node)
        project_id = ""
        for draft_ref in manifest.draft_refs:
            if get_node(conn, draft_ref):
                add_edge(conn, draft_ref, workspace_id, "materialized_from_draft")
        for sug_ref in manifest.suggestion_refs:
            if get_node(conn, sug_ref):
                add_edge(conn, sug_ref, workspace_id, "materialized_from_suggestion")
        for art in getattr(manifest, "artifacts", []):
            art_id = getattr(art, "artifact_id", None) or stable_id("art", art.title or "a", ts, prefix="art")
            proj = getattr(art, "project_id", "") or ""
            if proj and project_id_by_label.get(proj):
                project_id = project_id_by_label[proj]
            art_node = PersonalWorkGraphNode(
                node_id=art_id,
                node_type=NodeType.MATERIALIZED_ARTIFACT,
                label=getattr(art, "title", "artifact")[:200],
                attributes={
                    "artifact_type": getattr(art, "artifact_type", ""),
                    "sandbox_path": getattr(art, "sandbox_path", ""),
                    "request_id": getattr(art, "request_id", ""),
                    "project_id": proj,
                },
                source="materialize",
                created_utc=getattr(art, "created_utc", ts),
                updated_utc=ts,
                confidence=1.0,
            )
            add_node(conn, art_node)
            n += 1
            add_edge(conn, workspace_id, art_id, "materialized_in_workspace")
            if project_id and get_node(conn, project_id):
                add_edge(conn, project_id, art_id, "materialized_for_project")
            for ref in getattr(art, "provenance_refs", [])[:3]:
                if get_node(conn, ref):
                    add_edge(conn, ref, art_id, "materialized_from_draft")
        for profile_ref in getattr(manifest, "style_profile_refs", [])[:5]:
            if get_node(conn, profile_ref):
                add_edge(conn, profile_ref, workspace_id, "materialized_using_style_profile")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()
    return n
