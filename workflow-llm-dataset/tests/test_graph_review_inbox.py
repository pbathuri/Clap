"""
M31H.1: Routine confirmation + graph review inbox — store, suggest, list, accept/reject/edit, inbox integration.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from workflow_dataset.personal.graph_store import (
    init_store,
    save_graph_review_item,
    get_graph_review_item,
    list_graph_review_items,
    update_graph_review_status,
    add_node,
)
from workflow_dataset.personal.work_graph import NodeType, PersonalWorkGraphNode
from workflow_dataset.personal.graph_review_inbox import (
    KIND_ROUTINE_CONFIRMATION,
    KIND_PATTERN_REVIEW,
    STATUS_PENDING,
    STATUS_ACCEPTED,
    STATUS_REJECTED,
    STATUS_EDIT,
    list_pending_routines,
    list_pending_patterns,
    accept_routine,
    reject_routine,
    edit_routine,
    accept_pattern,
    reject_pattern,
    build_graph_review_inbox_items,
)
from workflow_dataset.utils.dates import utc_now_iso


def test_save_and_get_graph_review_item(tmp_path: Path) -> None:
    path = tmp_path / "g.sqlite"
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        save_graph_review_item(
            conn, "gr_routine_1", KIND_ROUTINE_CONFIRMATION,
            {"routine_id": "routine_abc", "label": "User often works in folder src", "confidence": 0.6},
            status=STATUS_PENDING, created_utc=utc_now_iso(), updated_utc=utc_now_iso(),
        )
        conn.commit()
        item = get_graph_review_item(conn, "gr_routine_1")
        assert item is not None
        assert item["kind"] == KIND_ROUTINE_CONFIRMATION
        assert item["status"] == STATUS_PENDING
        assert item["payload"]["label"] == "User often works in folder src"
    finally:
        conn.close()


def test_list_graph_review_items(tmp_path: Path) -> None:
    path = tmp_path / "g.sqlite"
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        save_graph_review_item(conn, "gr_1", KIND_ROUTINE_CONFIRMATION, {"label": "R1"}, STATUS_PENDING, "", "")
        save_graph_review_item(conn, "gr_2", KIND_PATTERN_REVIEW, {"pattern_type": "task_sequence"}, STATUS_PENDING, "", "")
        conn.commit()
        routines = list_graph_review_items(conn, kind=KIND_ROUTINE_CONFIRMATION, status=STATUS_PENDING, limit=10)
        patterns = list_graph_review_items(conn, kind=KIND_PATTERN_REVIEW, status=STATUS_PENDING, limit=10)
        assert len(routines) == 1
        assert len(patterns) == 1
        assert routines[0]["payload"]["label"] == "R1"
        assert patterns[0]["payload"]["pattern_type"] == "task_sequence"
    finally:
        conn.close()


def test_update_graph_review_status(tmp_path: Path) -> None:
    path = tmp_path / "g.sqlite"
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        save_graph_review_item(conn, "gr_1", KIND_ROUTINE_CONFIRMATION, {"label": "R1"}, STATUS_PENDING, "", "")
        conn.commit()
        ok = update_graph_review_status(conn, "gr_1", STATUS_ACCEPTED, "2025-01-01T00:00:00Z")
        assert ok
        item = get_graph_review_item(conn, "gr_1")
        assert item["status"] == STATUS_ACCEPTED
    finally:
        conn.close()


def test_list_pending_routines_empty(tmp_path: Path) -> None:
    # No graph or no items
    routines = list_pending_routines(repo_root=tmp_path)
    assert isinstance(routines, list)


def test_accept_reject_routine(tmp_path: Path) -> None:
    path = tmp_path / "data/local/work_graph.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        add_node(conn, PersonalWorkGraphNode(
            node_id="routine_xyz", node_type=NodeType.ROUTINE, label="Test routine",
            attributes={"confidence": 0.5}, created_utc="", updated_utc="",
        ))
        save_graph_review_item(
            conn, "gr_routine_xyz", KIND_ROUTINE_CONFIRMATION,
            {"routine_id": "routine_xyz", "label": "Test routine", "confidence": 0.5},
            STATUS_PENDING, "", "",
        )
        conn.commit()
    finally:
        conn.close()
    result = accept_routine("gr_routine_xyz", repo_root=tmp_path)
    assert result.get("ok") is True
    assert result.get("status") == STATUS_ACCEPTED
    result2 = reject_routine("gr_nonexistent", repo_root=tmp_path)
    assert result2.get("ok") is False or result2.get("status") == "already_decided"


def test_reject_routine(tmp_path: Path) -> None:
    path = tmp_path / "data/local/work_graph.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        save_graph_review_item(
            conn, "gr_rej", KIND_ROUTINE_CONFIRMATION,
            {"routine_id": "r2", "label": "R2"}, STATUS_PENDING, "", "",
        )
        conn.commit()
    finally:
        conn.close()
    result = reject_routine("gr_rej", repo_root=tmp_path)
    assert result.get("ok") is True
    assert result.get("status") == STATUS_REJECTED


def test_edit_routine(tmp_path: Path) -> None:
    path = tmp_path / "data/local/work_graph.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        add_node(conn, PersonalWorkGraphNode(
            node_id="routine_edit", node_type=NodeType.ROUTINE, label="Original",
            attributes={}, created_utc="", updated_utc="",
        ))
        save_graph_review_item(
            conn, "gr_edit", KIND_ROUTINE_CONFIRMATION,
            {"routine_id": "routine_edit", "label": "Original"}, STATUS_PENDING, "", "",
        )
        conn.commit()
    finally:
        conn.close()
    result = edit_routine("gr_edit", "Edited label", repo_root=tmp_path)
    assert result.get("ok") is True
    assert result.get("status") == STATUS_EDIT
    assert result.get("new_label") == "Edited label"


def test_accept_reject_pattern(tmp_path: Path) -> None:
    path = tmp_path / "data/local/work_graph.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        save_graph_review_item(
            conn, "gr_pat_1", KIND_PATTERN_REVIEW,
            {"pattern_type": "repeated_block", "confidence": 0.55}, STATUS_PENDING, "", "",
        )
        conn.commit()
    finally:
        conn.close()
    result = accept_pattern("gr_pat_1", repo_root=tmp_path)
    assert result.get("ok") is True
    assert result.get("status") == STATUS_ACCEPTED


def test_build_graph_review_inbox_items(tmp_path: Path) -> None:
    path = tmp_path / "data/local/work_graph.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    init_store(path)
    conn = sqlite3.connect(str(path))
    try:
        save_graph_review_item(
            conn, "gr_inbox_1", KIND_ROUTINE_CONFIRMATION,
            {"routine_id": "r1", "label": "Inbox routine"}, STATUS_PENDING, "", "",
        )
        conn.commit()
    finally:
        conn.close()
    items = build_graph_review_inbox_items(repo_root=tmp_path, status=STATUS_PENDING)
    assert isinstance(items, list)
    from workflow_dataset.review_studio.models import ITEM_GRAPH_ROUTINE_CONFIRMATION
    routine_items = [i for i in items if i.kind == ITEM_GRAPH_ROUTINE_CONFIRMATION]
    assert len(routine_items) >= 1
    assert "Inbox routine" in (routine_items[0].summary if routine_items else "")
