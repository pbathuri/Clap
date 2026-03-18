"""
M31H.1: Routine confirmation + graph review inbox — suggested routines/patterns awaiting confirmation,
accept/reject/edit, integration with review_studio/trust surfaces.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

# Kinds for graph_review table
KIND_ROUTINE_CONFIRMATION = "routine_confirmation"
KIND_PATTERN_REVIEW = "pattern_review"

# Status
STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
STATUS_EDIT = "edited"


def _graph_path(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        root = Path(repo_root).resolve()
    else:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()
    try:
        from workflow_dataset.settings import load_settings
        s = load_settings("configs/settings.yaml")
        p = getattr(getattr(s, "paths", None), "graph_store_path", None)
        if p:
            return Path(p).resolve()
    except Exception:
        pass
    return root / "data/local/work_graph.sqlite"


def _conn(repo_root: Path | str | None):
    from workflow_dataset.personal.graph_store import init_store
    path = _graph_path(repo_root)
    if not path.exists():
        return None
    init_store(path)
    return sqlite3.connect(str(path))


def suggest_routines_for_review(
    repo_root: Path | str | None = None,
    max_confidence: float = 0.75,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """
    Add routine nodes (from graph) that are below max_confidence or not yet in graph_review
    as suggested routine items. Returns list of added item_ids.
    """
    from workflow_dataset.personal.graph_store import (
        init_store,
        list_nodes,
        get_graph_review_item,
        save_graph_review_item,
    )
    from workflow_dataset.personal.work_graph import NodeType
    path = _graph_path(repo_root)
    if not path.exists():
        return []
    init_store(path)
    conn = sqlite3.connect(str(path))
    added: list[dict[str, Any]] = []
    try:
        routines = list_nodes(conn, node_type=NodeType.ROUTINE.value, limit=limit)
        ts = utc_now_iso()
        for r in routines:
            node_id = r["node_id"]
            attrs = r.get("attributes") or {}
            conf = attrs.get("confidence") or attrs.get("confidence_value")
            if conf is not None and conf > max_confidence:
                continue
            item_id = stable_id("gr_routine", node_id, prefix="gr_")
            existing = get_graph_review_item(conn, item_id)
            if existing and existing.get("status") != STATUS_PENDING:
                continue
            payload = {
                "routine_id": node_id,
                "label": r.get("label", ""),
                "confidence": conf,
                "supporting_signals": attrs.get("supporting_signals", []),
                "routine_type": attrs.get("routine_type", ""),
                "project": attrs.get("project", ""),
            }
            save_graph_review_item(conn, item_id, KIND_ROUTINE_CONFIRMATION, payload, STATUS_PENDING, ts, ts)
            added.append({"item_id": item_id, "routine_id": node_id, "label": payload["label"]})
        conn.commit()
    finally:
        conn.close()
    return added


def suggest_patterns_for_review(
    repo_root: Path | str | None = None,
    max_confidence: float = 0.65,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Add uncertain patterns as pattern review items. Returns list of added item_ids.
    """
    from workflow_dataset.personal.graph_reports import uncertain_patterns
    from workflow_dataset.personal.graph_store import get_graph_review_item, save_graph_review_item
    path = _graph_path(repo_root)
    if not path.exists():
        return []
    patterns = uncertain_patterns(repo_root=repo_root, max_confidence=max_confidence, limit=limit)
    conn = _conn(repo_root)
    if not conn:
        return []
    added = []
    ts = utc_now_iso()
    try:
        for p in patterns:
            item_id = stable_id("gr_pattern", p.get("pattern_type", ""), str(p.get("count", 0)), str(p.get("confidence", "")), prefix="gr_")
            existing = get_graph_review_item(conn, item_id)
            if existing and existing.get("status") != STATUS_PENDING:
                continue
            save_graph_review_item(conn, item_id, KIND_PATTERN_REVIEW, dict(p), STATUS_PENDING, ts, ts)
            added.append({"item_id": item_id, "pattern_type": p.get("pattern_type"), "confidence": p.get("confidence")})
        conn.commit()
    finally:
        conn.close()
    return added


def list_pending_routines(repo_root: Path | str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """List suggested routines awaiting confirmation."""
    from workflow_dataset.personal.graph_store import init_store, list_graph_review_items
    path = _graph_path(repo_root)
    if not path.exists():
        return []
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        return list_graph_review_items(conn, kind=KIND_ROUTINE_CONFIRMATION, status=STATUS_PENDING, limit=limit)
    finally:
        conn.close()


def list_pending_patterns(repo_root: Path | str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """List weak/uncertain patterns awaiting review."""
    from workflow_dataset.personal.graph_store import init_store, list_graph_review_items
    path = _graph_path(repo_root)
    if not path.exists():
        return []
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        return list_graph_review_items(conn, kind=KIND_PATTERN_REVIEW, status=STATUS_PENDING, limit=limit)
    finally:
        conn.close()


def accept_routine(item_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark routine suggestion as accepted. Optionally set operator_confirmed on graph node."""
    from workflow_dataset.personal.graph_store import (
        init_store,
        get_graph_review_item,
        update_graph_review_status,
        get_node,
        add_node,
    )
    path = _graph_path(repo_root)
    if not path.exists():
        return {"ok": False, "error": "graph_not_found"}
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        item = get_graph_review_item(conn, item_id)
        if not item or item.get("kind") != KIND_ROUTINE_CONFIRMATION:
            return {"ok": False, "error": "item_not_found_or_not_routine"}
        if item.get("status") != STATUS_PENDING:
            return {"ok": True, "status": item.get("status"), "message": "already_decided"}
        update_graph_review_status(conn, item_id, STATUS_ACCEPTED, utc_now_iso())
        routine_id = (item.get("payload") or {}).get("routine_id")
        if routine_id:
            node = get_node(conn, routine_id)
            if node:
                node.attributes = dict(node.attributes or {})
                node.attributes["operator_confirmed"] = True
                node.attributes["confirmed_at"] = utc_now_iso()
                node.updated_utc = utc_now_iso()
                add_node(conn, node)
        conn.commit()
        return {"ok": True, "status": STATUS_ACCEPTED, "item_id": item_id}
    finally:
        conn.close()


def reject_routine(item_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark routine suggestion as rejected."""
    from workflow_dataset.personal.graph_store import init_store, get_graph_review_item, update_graph_review_status
    path = _graph_path(repo_root)
    if not path.exists():
        return {"ok": False, "error": "graph_not_found"}
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        item = get_graph_review_item(conn, item_id)
        if not item or item.get("kind") != KIND_ROUTINE_CONFIRMATION:
            return {"ok": False, "error": "item_not_found_or_not_routine"}
        if item.get("status") != STATUS_PENDING:
            return {"ok": True, "status": item.get("status"), "message": "already_decided"}
        update_graph_review_status(conn, item_id, STATUS_REJECTED, utc_now_iso())
        conn.commit()
        return {"ok": True, "status": STATUS_REJECTED, "item_id": item_id}
    finally:
        conn.close()


def edit_routine(item_id: str, new_label: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark routine as edited and update label in payload; optionally update graph node label."""
    from workflow_dataset.personal.graph_store import (
        init_store,
        get_graph_review_item,
        update_graph_review_status,
        get_node,
        add_node,
    )
    path = _graph_path(repo_root)
    if not path.exists():
        return {"ok": False, "error": "graph_not_found"}
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        item = get_graph_review_item(conn, item_id)
        if not item or item.get("kind") != KIND_ROUTINE_CONFIRMATION:
            return {"ok": False, "error": "item_not_found_or_not_routine"}
        if item.get("status") != STATUS_PENDING:
            return {"ok": True, "status": item.get("status"), "message": "already_decided"}
        payload = dict(item.get("payload") or {})
        payload["edited_label"] = new_label
        payload["label"] = new_label
        update_graph_review_status(conn, item_id, STATUS_EDIT, utc_now_iso(), payload_update=payload)
        routine_id = payload.get("routine_id")
        if routine_id and new_label:
            node = get_node(conn, routine_id)
            if node:
                node.label = new_label
                node.attributes = dict(node.attributes or {})
                node.attributes["operator_edited"] = True
                node.updated_utc = utc_now_iso()
                add_node(conn, node)
        conn.commit()
        return {"ok": True, "status": STATUS_EDIT, "item_id": item_id, "new_label": new_label}
    finally:
        conn.close()


def accept_pattern(item_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark pattern review item as accepted."""
    from workflow_dataset.personal.graph_store import init_store, get_graph_review_item, update_graph_review_status
    path = _graph_path(repo_root)
    if not path.exists():
        return {"ok": False, "error": "graph_not_found"}
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        item = get_graph_review_item(conn, item_id)
        if not item or item.get("kind") != KIND_PATTERN_REVIEW:
            return {"ok": False, "error": "item_not_found_or_not_pattern"}
        if item.get("status") != STATUS_PENDING:
            return {"ok": True, "status": item.get("status"), "message": "already_decided"}
        update_graph_review_status(conn, item_id, STATUS_ACCEPTED, utc_now_iso())
        conn.commit()
        return {"ok": True, "status": STATUS_ACCEPTED, "item_id": item_id}
    finally:
        conn.close()


def reject_pattern(item_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark pattern review item as rejected."""
    from workflow_dataset.personal.graph_store import init_store, get_graph_review_item, update_graph_review_status
    path = _graph_path(repo_root)
    if not path.exists():
        return {"ok": False, "error": "graph_not_found"}
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        item = get_graph_review_item(conn, item_id)
        if not item or item.get("kind") != KIND_PATTERN_REVIEW:
            return {"ok": False, "error": "item_not_found_or_not_pattern"}
        if item.get("status") != STATUS_PENDING:
            return {"ok": True, "status": item.get("status"), "message": "already_decided"}
        update_graph_review_status(conn, item_id, STATUS_REJECTED, utc_now_iso())
        conn.commit()
        return {"ok": True, "status": STATUS_REJECTED, "item_id": item_id}
    finally:
        conn.close()


def build_graph_review_inbox_items(
    repo_root: Path | str | None = None,
    status: str = "pending",
    limit: int = 50,
) -> list[Any]:
    """
    Build intervention items for the graph review inbox (for use by review_studio inbox).
    Returns list of InterventionItem-like dicts or InterventionItem instances.
    """
    from workflow_dataset.review_studio.models import InterventionItem
    from workflow_dataset.review_studio.models import ITEM_GRAPH_ROUTINE_CONFIRMATION, ITEM_GRAPH_PATTERN_REVIEW
    from workflow_dataset.personal.graph_store import init_store, list_graph_review_items
    path = _graph_path(repo_root)
    if not path.exists():
        return []
    init_store(path)
    conn = sqlite3.connect(str(path))
    items: list[InterventionItem] = []
    try:
        rows = list_graph_review_items(conn, status=status if status else None, limit=limit)
        for r in rows:
            payload = r.get("payload") or {}
            kind = r.get("kind", "")
            if kind == KIND_ROUTINE_CONFIRMATION:
                summary = f"Routine: {payload.get('label', r['item_id'])} (conf={payload.get('confidence')})"
                items.append(InterventionItem(
                    item_id=r["item_id"],
                    kind=ITEM_GRAPH_ROUTINE_CONFIRMATION,
                    status=r.get("status", STATUS_PENDING),
                    summary=summary[:80],
                    created_at=r.get("created_utc", ""),
                    priority="low",
                    entity_refs={"routine_id": payload.get("routine_id", ""), "item_id": r["item_id"]},
                    source_ref=payload.get("routine_id", r["item_id"]),
                ))
            elif kind == KIND_PATTERN_REVIEW:
                summary = f"Pattern: {payload.get('pattern_type', 'pattern')} (conf={payload.get('confidence')})"
                items.append(InterventionItem(
                    item_id=r["item_id"],
                    kind=ITEM_GRAPH_PATTERN_REVIEW,
                    status=r.get("status", STATUS_PENDING),
                    summary=summary[:80],
                    created_at=r.get("created_utc", ""),
                    priority="low",
                    entity_refs={"pattern_type": payload.get("pattern_type", ""), "item_id": r["item_id"]},
                    source_ref=r["item_id"],
                ))
        conn.close()
    except Exception:
        conn.close()
        raise
    return items
