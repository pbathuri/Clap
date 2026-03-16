"""
Project and domain context for the assistive loop.

Loads from graph + setup outputs (parsed artifacts, style signals) to provide
project_id, domain, and style context. No execution; read-only.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.personal.graph_store import init_store, list_nodes
from workflow_dataset.setup.style_persistence import load_style_signals


def load_projects_from_graph(graph_path: Path | str) -> list[dict[str, Any]]:
    """List PROJECT nodes from the graph."""
    path = Path(graph_path)
    if not path.exists():
        return []
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        nodes = list_nodes(conn, node_type="project", limit=500)
        return [{"node_id": n["node_id"], "label": n["label"], "attributes": n.get("attributes", {})} for n in nodes]
    finally:
        conn.close()


def load_domains_from_graph(graph_path: Path | str) -> list[dict[str, Any]]:
    """List DOMAIN nodes from the graph."""
    path = Path(graph_path)
    if not path.exists():
        return []
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        return list_nodes(conn, node_type="domain", limit=100)
    finally:
        conn.close()


def load_parsed_artifacts_summary(parsed_dir: Path | str, session_id: str) -> list[dict[str, Any]]:
    """Load parsed artifact summaries (path, family, title, summary) for a session."""
    from workflow_dataset.parse.document_models import ParsedDocument
    base = Path(parsed_dir) / session_id
    if not base.exists():
        return []
    out = []
    for p in sorted(base.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                doc = ParsedDocument.model_validate_json(f.read())
            if doc.error:
                continue
            out.append({
                "source_path": doc.source_path,
                "artifact_family": doc.artifact_family,
                "title": doc.title,
                "summary": doc.summary[:300] if doc.summary else "",
            })
        except Exception:
            continue
    return out


def infer_project_from_path(path: str, scan_roots: list[str] | None = None) -> str:
    """Infer project label from path (first segment under a scan root, or last parent name)."""
    path_obj = Path(path).resolve()
    if scan_roots:
        for r in scan_roots:
            try:
                rel = path_obj.relative_to(Path(r).resolve())
                if rel.parts:
                    return rel.parts[0]
            except ValueError:
                continue
    parts = path_obj.parts
    if len(parts) >= 2:
        return parts[-2]
    return parts[0] if parts else "unknown"


def get_assistive_context(
    graph_path: Path | str,
    style_signals_dir: Path | str,
    parsed_artifacts_dir: Path | str,
    session_id: str = "",
) -> dict[str, Any]:
    """
    Gather context for the assistive engines: projects, domains, style signals, parsed summary.
    """
    projects = load_projects_from_graph(graph_path)
    domains = load_domains_from_graph(graph_path)
    style_records = load_style_signals(session_id, style_signals_dir) if session_id else []
    parsed = load_parsed_artifacts_summary(parsed_artifacts_dir, session_id) if session_id else []
    return {
        "projects": projects,
        "domains": [{"node_id": d["node_id"], "label": d["label"]} for d in domains],
        "style_signals": [{"pattern_type": r.pattern_type, "value": r.value, "description": r.description} for r in style_records],
        "parsed_artifacts": parsed,
        "session_id": session_id,
    }
