"""
Graph enrichment from setup: add artifact, project, domain, style, workflow hint nodes.

Relations: artifact_in_project, artifact_has_family, artifact_supports_domain,
artifact_exhibits_style_pattern (alias artifact_exhibits_style_signature),
project_has_workflow_hint, project_has_domain, style_pattern_seen_in_project.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.personal.work_graph import (
    NodeType,
    PersonalWorkGraphNode,
)
from workflow_dataset.personal import graph_store as _gs
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def get_or_create_project(
    conn: sqlite3.Connection,
    project_label: str,
    scan_root: str = "",
    source: str = "setup",
) -> str:
    """Get or create a PROJECT node; return node_id."""
    project_id = stable_id("project", project_label, prefix="project")
    existing = _gs.get_node(conn, project_id)
    if existing is not None:
        return project_id
    ts = utc_now_iso()
    node = PersonalWorkGraphNode(
        node_id=project_id,
        node_type=NodeType.PROJECT,
        label=project_label,
        attributes={"inferred_from": "setup_scan", "scan_root": scan_root},
        source=source,
        created_utc=ts,
        updated_utc=ts,
        confidence=0.8,
    )
    _gs.add_node(conn, node)
    return project_id


def get_or_create_family_node(
    conn: sqlite3.Connection,
    family_name: str,
    source: str = "setup",
) -> str:
    """Get or create a node representing an artifact family (e.g. text_document); return node_id."""
    family_id = stable_id("family", family_name, prefix="family")
    existing = _gs.get_node(conn, family_id)
    if existing is not None:
        return family_id
    ts = utc_now_iso()
    node = PersonalWorkGraphNode(
        node_id=family_id,
        node_type=NodeType.FOLDER,  # reuse FOLDER as generic container for family
        label=family_name,
        attributes={"artifact_family": family_name},
        source=source,
        created_utc=ts,
        updated_utc=ts,
        confidence=1.0,
    )
    _gs.add_node(conn, node)
    return family_id


def add_artifact_node(
    conn: sqlite3.Connection,
    path: str,
    artifact_family: str,
    project_id: str | None = None,
    family_node_id: str | None = None,
    domain_ids: list[str] | None = None,
    style_pattern_ids: list[str] | None = None,
    source: str = "setup",
) -> str:
    """Add or update artifact node; link to project, family, domains, style patterns. Returns node_id."""
    node_type = NodeType.FILE_REF
    if artifact_family == "document_artifact" or artifact_family == "text_document":
        node_type = NodeType.DOCUMENT_ARTIFACT
    elif artifact_family in ("tabular_artifact", "spreadsheet_table"):
        node_type = NodeType.TABULAR_ARTIFACT
    elif artifact_family in ("media_asset", "image_asset"):
        node_type = NodeType.MEDIA_ARTIFACT
    node_id = stable_id("artifact", path, prefix="art")
    ts = utc_now_iso()
    node = PersonalWorkGraphNode(
        node_id=node_id,
        node_type=node_type,
        label=Path(path).name,
        attributes={"path": path, "artifact_family": artifact_family},
        source=source,
        created_utc=ts,
        updated_utc=ts,
        confidence=0.85,
    )
    _gs.add_node(conn, node)
    if project_id:
        _gs.add_edge(conn, node_id, project_id, "artifact_in_project")
    if family_node_id:
        _gs.add_edge(conn, node_id, family_node_id, "artifact_has_family")
    for did in domain_ids or []:
        _gs.add_edge(conn, node_id, did, "artifact_supports_domain")
    for sid in style_pattern_ids or []:
        _gs.add_edge(conn, node_id, sid, "artifact_exhibits_style_pattern")
        _gs.add_edge(conn, node_id, sid, "artifact_exhibits_style_signature")  # alias for spec
    return node_id


def add_domain_node(conn: sqlite3.Connection, domain_id: str, label: str, source: str = "setup") -> str:
    nid = stable_id("domain", domain_id, prefix="domain")
    ts = utc_now_iso()
    node = PersonalWorkGraphNode(
        node_id=nid,
        node_type=NodeType.DOMAIN,
        label=label,
        attributes={"domain_id": domain_id},
        source=source,
        created_utc=ts,
        updated_utc=ts,
        confidence=0.8,
    )
    _gs.add_node(conn, node)
    return nid


def add_style_pattern_node(
    conn: sqlite3.Connection,
    pattern_type: str,
    value: str | list[str],
    description: str = "",
    source: str = "setup",
) -> str:
    nid = stable_id("style", pattern_type, str(value)[:100], prefix="style")
    ts = utc_now_iso()
    node = PersonalWorkGraphNode(
        node_id=nid,
        node_type=NodeType.STYLE_PATTERN,
        label=pattern_type,
        attributes={"pattern_type": pattern_type, "value": value, "description": description},
        source=source,
        created_utc=ts,
        updated_utc=ts,
        confidence=0.7,
    )
    _gs.add_node(conn, node)
    return nid


def add_workflow_hint_node(
    conn: sqlite3.Connection,
    hint: str,
    project_id: str,
    source: str = "setup",
) -> str:
    nid = stable_id("workflow_hint", hint, project_id, prefix="wf")
    ts = utc_now_iso()
    node = PersonalWorkGraphNode(
        node_id=nid,
        node_type=NodeType.WORKFLOW_HINT,
        label=hint[:200],
        attributes={"hint": hint},
        source=source,
        created_utc=ts,
        updated_utc=ts,
        confidence=0.6,
    )
    _gs.add_node(conn, node)
    _gs.add_edge(conn, project_id, nid, "project_has_workflow_hint")
    return nid


def link_project_to_domain(conn: sqlite3.Connection, project_id: str, domain_node_id: str) -> None:
    _gs.add_edge(conn, project_id, domain_node_id, "project_has_domain")


def link_style_pattern_to_project(conn: sqlite3.Connection, style_pattern_id: str, project_id: str) -> None:
    _gs.add_edge(conn, style_pattern_id, project_id, "style_pattern_seen_in_project")
    _gs.add_edge(conn, style_pattern_id, project_id, "style_signature_seen_in_project")  # alias
