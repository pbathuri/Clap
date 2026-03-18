"""
Persist assistive layer nodes and edges into the personal graph.

Nodes: style_profile, imitation_candidate, draft_structure, style_aware_suggestion.
Edges: project_has_style_profile, style_profile_supports_suggestion, suggestion_based_on_artifact,
suggestion_based_on_style_profile, draft_structure_for_project, imitation_candidate_for_project,
imitation_candidate_supported_by_style_profile.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.personal.graph_store import init_store, add_node, add_edge, get_node
from workflow_dataset.personal.work_graph import NodeType, PersonalWorkGraphNode
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _ensure_conn(conn_or_path: sqlite3.Connection | Path | str) -> sqlite3.Connection:
    if isinstance(conn_or_path, sqlite3.Connection):
        return conn_or_path
    path = Path(conn_or_path)
    init_store(path)
    return sqlite3.connect(str(path))


def persist_style_profile_nodes(
    conn_or_path: sqlite3.Connection | Path | str,
    profiles: list[Any],
    project_id_by_label: dict[str, str] | None = None,
) -> int:
    """Write style profile nodes and project_has_style_profile edges. Returns count written."""
    conn = _ensure_conn(conn_or_path)
    project_id_by_label = project_id_by_label or {}
    ts = utc_now_iso()
    n = 0
    try:
        for p in profiles:
            profile_id = getattr(p, "profile_id", None) or stable_id("profile", str(p)[:50], prefix="profile")
            node = PersonalWorkGraphNode(
                node_id=profile_id,
                node_type=NodeType.STYLE_PROFILE,
                label=getattr(p, "profile_type", "style_profile"),
                attributes={
                    "profile_type": getattr(p, "profile_type", ""),
                    "domain": getattr(p, "domain", ""),
                    "project_id": getattr(p, "project_id", ""),
                    "style_family": getattr(p, "style_family", ""),
                    "evidence_count": getattr(p, "evidence_count", 0),
                    "confidence": getattr(p, "confidence", 0),
                },
                source="assistive",
                created_utc=getattr(p, "created_utc", ts),
                updated_utc=getattr(p, "updated_utc", ts),
                confidence=getattr(p, "confidence", 0.5),
            )
            add_node(conn, node)
            n += 1
            proj_label = getattr(p, "project_id", "") or (p.project_paths[0].split("/")[0] if getattr(p, "project_paths", []) else "")
            proj_node_id = project_id_by_label.get(proj_label) if proj_label else None
            if not proj_node_id and proj_label:
                proj_node_id = stable_id("project", proj_label, prefix="project")
                if get_node(conn, proj_node_id):
                    pass  # use it
                else:
                    proj_node_id = None
            if proj_node_id:
                add_edge(conn, proj_node_id, profile_id, "project_has_style_profile")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()
    return n


def persist_imitation_candidate_nodes(
    conn_or_path: sqlite3.Connection | Path | str,
    candidates: list[Any],
    project_id_by_label: dict[str, str] | None = None,
) -> int:
    """Write imitation candidate nodes and imitation_candidate_for_project / supported_by_style_profile edges."""
    conn = _ensure_conn(conn_or_path)
    project_id_by_label = project_id_by_label or {}
    n = 0
    try:
        for c in candidates:
            cid = getattr(c, "candidate_id", None) or stable_id("cand", getattr(c, "candidate_type", ""), prefix="cand")
            proj_label = getattr(c, "project_id", "") or (getattr(c, "project_path", "") or "").replace("\\", "/").strip("/").split("/")[0]
            proj_id = project_id_by_label.get(proj_label) if proj_label else ""
            if not proj_id and proj_label and get_node(conn, stable_id("project", proj_label, prefix="project")):
                proj_id = stable_id("project", proj_label, prefix="project")
            node = PersonalWorkGraphNode(
                node_id=cid,
                node_type=NodeType.IMITATION_CANDIDATE,
                label=getattr(c, "candidate_type", "imitation_candidate"),
                attributes={
                    "candidate_type": getattr(c, "candidate_type", ""),
                    "domain": getattr(c, "domain", ""),
                    "project_id": proj_id,
                    "confidence_score": getattr(c, "confidence_score", getattr(c, "strength", 0)),
                    "source_patterns": getattr(c, "source_patterns", []),
                },
                source="assistive",
                created_utc=utc_now_iso(),
                updated_utc=utc_now_iso(),
                confidence=getattr(c, "confidence_score", getattr(c, "strength", 0.5)),
            )
            add_node(conn, node)
            n += 1
            if proj_id:
                add_edge(conn, proj_id, cid, "imitation_candidate_for_project")
            for pid in getattr(c, "source_patterns", [])[:5]:
                if get_node(conn, pid):
                    add_edge(conn, pid, cid, "imitation_candidate_supported_by_style_profile")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()
    return n


def persist_draft_structure_nodes(
    conn_or_path: sqlite3.Connection | Path | str,
    drafts: list[Any],
    project_id_by_label: dict[str, str] | None = None,
) -> int:
    """Write draft structure nodes and draft_structure_for_project edges."""
    conn = _ensure_conn(conn_or_path)
    project_id_by_label = project_id_by_label or {}
    ts = utc_now_iso()
    n = 0
    try:
        for d in drafts:
            did = getattr(d, "draft_id", None) or stable_id("draft", getattr(d, "draft_type", ""), ts, prefix="draft")
            proj_label = getattr(d, "project_id", "")
            proj_id = project_id_by_label.get(proj_label) if proj_label else ""
            if not proj_id and proj_label and get_node(conn, stable_id("project", proj_label, prefix="project")):
                proj_id = stable_id("project", proj_label, prefix="project")
            node = PersonalWorkGraphNode(
                node_id=did,
                node_type=NodeType.DRAFT_STRUCTURE,
                label=getattr(d, "title", getattr(d, "draft_type", "draft")),
                attributes={
                    "draft_type": getattr(d, "draft_type", ""),
                    "domain": getattr(d, "domain", ""),
                    "project_id": proj_id,
                    "confidence_score": getattr(d, "confidence_score", 0),
                    "style_profile_refs": getattr(d, "style_profile_refs", []),
                },
                source="assistive",
                created_utc=getattr(d, "created_utc", ts),
                updated_utc=ts,
                confidence=getattr(d, "confidence_score", 0.5),
            )
            add_node(conn, node)
            n += 1
            if proj_id:
                add_edge(conn, proj_id, did, "draft_structure_for_project")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()
    return n


def persist_style_aware_suggestion_nodes(
    conn_or_path: sqlite3.Connection | Path | str,
    suggestions: list[Any],
    project_id_by_label: dict[str, str] | None = None,
) -> int:
    """Write style-aware suggestion nodes and style_profile_supports_suggestion / suggestion_based_on_style_profile edges."""
    conn = _ensure_conn(conn_or_path)
    project_id_by_label = project_id_by_label or {}
    ts = utc_now_iso()
    n = 0
    try:
        for s in suggestions:
            sid = getattr(s, "suggestion_id", None) or stable_id("style_sug", getattr(s, "suggestion_type", ""), ts, prefix="sug")
            proj_label = getattr(s, "project_id", "")
            proj_id = project_id_by_label.get(proj_label) if proj_label else ""
            if not proj_id and proj_label and get_node(conn, stable_id("project", proj_label, prefix="project")):
                proj_id = stable_id("project", proj_label, prefix="project")
            node = PersonalWorkGraphNode(
                node_id=sid,
                node_type=NodeType.STYLE_AWARE_SUGGESTION,
                label=getattr(s, "title", "")[:200] or getattr(s, "suggestion_type", "suggestion"),
                attributes={
                    "suggestion_type": getattr(s, "suggestion_type", ""),
                    "domain": getattr(s, "domain", ""),
                    "project_id": proj_id,
                    "rationale": getattr(s, "rationale", "")[:500],
                    "confidence_score": getattr(s, "confidence_score", 0),
                    "status": getattr(s, "status", "pending"),
                },
                source="assistive",
                created_utc=getattr(s, "created_utc", ts),
                updated_utc=ts,
                confidence=getattr(s, "confidence_score", 0.5),
            )
            add_node(conn, node)
            n += 1
            for ref in getattr(s, "style_profile_refs", [])[:5]:
                if get_node(conn, ref):
                    add_edge(conn, ref, sid, "style_profile_supports_suggestion")
                    add_edge(conn, sid, ref, "suggestion_based_on_style_profile")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()
    return n
