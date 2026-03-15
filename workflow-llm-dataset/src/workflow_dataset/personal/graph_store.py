"""
Minimal local graph store: SQLite-backed nodes and edges.

Used to persist personal work graph from observation (e.g. file events).
Device-local only. See docs/schemas/PERSONAL_WORK_GRAPH.md.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.personal.work_graph import NodeType, PersonalWorkGraphNode


def init_store(db_path: Path) -> None:
    """Create tables if they do not exist."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                label TEXT NOT NULL DEFAULT '',
                attributes TEXT NOT NULL DEFAULT '{}',
                source TEXT NOT NULL DEFAULT 'observation',
                created_utc TEXT NOT NULL DEFAULT '',
                updated_utc TEXT NOT NULL DEFAULT '',
                confidence REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                PRIMARY KEY (from_id, to_id, relation_type),
                FOREIGN KEY (from_id) REFERENCES nodes(node_id),
                FOREIGN KEY (to_id) REFERENCES nodes(node_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                suggestion_id TEXT PRIMARY KEY,
                suggestion_type TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                confidence_score REAL NOT NULL,
                supporting_signals TEXT NOT NULL DEFAULT '[]',
                created_utc TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending'
            )
        """)
        conn.commit()
    finally:
        conn.close()


def add_node(conn: sqlite3.Connection, node: PersonalWorkGraphNode) -> None:
    """Insert or replace a node."""
    attrs = json.dumps(node.attributes) if node.attributes else "{}"
    conn.execute(
        """
        INSERT OR REPLACE INTO nodes (node_id, node_type, label, attributes, source, created_utc, updated_utc, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            node.node_id,
            node.node_type.value,
            node.label,
            attrs,
            node.source,
            node.created_utc or "",
            node.updated_utc or "",
            node.confidence,
        ),
    )


def get_node(conn: sqlite3.Connection, node_id: str) -> PersonalWorkGraphNode | None:
    """Load one node by id."""
    row = conn.execute(
        "SELECT node_id, node_type, label, attributes, source, created_utc, updated_utc, confidence FROM nodes WHERE node_id = ?",
        (node_id,),
    ).fetchone()
    if not row:
        return None
    attrs = json.loads(row[3]) if row[3] else {}
    return PersonalWorkGraphNode(
        node_id=row[0],
        node_type=NodeType(row[1]),
        label=row[2] or "",
        attributes=attrs,
        source=row[4] or "observation",
        created_utc=row[5] or "",
        updated_utc=row[6] or "",
        confidence=row[7],
    )


def add_edge(conn: sqlite3.Connection, from_id: str, to_id: str, relation_type: str) -> None:
    """Insert an edge (ignore if exists)."""
    conn.execute(
        "INSERT OR IGNORE INTO edges (from_id, to_id, relation_type) VALUES (?, ?, ?)",
        (from_id, to_id, relation_type),
    )


def count_nodes(conn: sqlite3.Connection, node_type: str | None = None) -> int:
    """Count nodes, optionally filtered by type."""
    if node_type:
        return conn.execute("SELECT COUNT(*) FROM nodes WHERE node_type = ?", (node_type,)).fetchone()[0]
    return conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]


def count_edges(conn: sqlite3.Connection, relation_type: str | None = None) -> int:
    """Count edges, optionally filtered by relation_type."""
    if relation_type:
        return conn.execute("SELECT COUNT(*) FROM edges WHERE relation_type = ?", (relation_type,)).fetchone()[0]
    return conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]


def save_suggestion(
    conn: sqlite3.Connection,
    suggestion_id: str,
    suggestion_type: str,
    title: str,
    description: str,
    confidence_score: float,
    supporting_signals: list[str] | list[dict[str, Any]],
    created_utc: str,
    status: str = "pending",
) -> None:
    """Insert or replace a suggestion."""
    signals_json = json.dumps(supporting_signals) if supporting_signals else "[]"
    conn.execute(
        """
        INSERT OR REPLACE INTO suggestions
        (suggestion_id, suggestion_type, title, description, confidence_score, supporting_signals, created_utc, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (suggestion_id, suggestion_type, title, description, confidence_score, signals_json, created_utc, status),
    )


def list_suggestions(
    conn: sqlite3.Connection,
    status_filter: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List suggestions, optionally filtered by status."""
    if status_filter:
        rows = conn.execute(
            """SELECT suggestion_id, suggestion_type, title, description, confidence_score,
                      supporting_signals, created_utc, status FROM suggestions WHERE status = ? ORDER BY created_utc DESC LIMIT ?""",
            (status_filter, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT suggestion_id, suggestion_type, title, description, confidence_score,
                      supporting_signals, created_utc, status FROM suggestions ORDER BY created_utc DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    out = []
    for r in rows:
        signals = json.loads(r[5]) if r[5] else []
        out.append({
            "suggestion_id": r[0],
            "suggestion_type": r[1],
            "title": r[2],
            "description": r[3],
            "confidence_score": r[4],
            "supporting_signals": signals,
            "created_utc": r[6],
            "status": r[7],
        })
    return out
