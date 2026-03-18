"""
M29I–M29L: Tests for activity timeline, intervention inbox, review studio.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.review_studio.models import (
    TimelineEvent,
    InterventionItem,
    EVENT_ACTION_QUEUED,
    EVENT_EXECUTOR_COMPLETED,
    ITEM_APPROVAL_QUEUE,
    ITEM_BLOCKED_RUN,
)
from workflow_dataset.review_studio.timeline import build_timeline
from workflow_dataset.review_studio.inbox import build_inbox
from workflow_dataset.review_studio.studio import get_item, inspect_item
from workflow_dataset.review_studio.store import load_inbox_snapshot, save_operator_note, load_operator_notes


def test_timeline_empty(tmp_path: Path) -> None:
    events = build_timeline(repo_root=tmp_path, limit=10)
    assert isinstance(events, list)
    # May be empty if no queue/handoffs/runs/projects
    assert len(events) <= 10


def test_timeline_project_filter(tmp_path: Path) -> None:
    events = build_timeline(repo_root=tmp_path, project_id="nonexistent_project", limit=5)
    assert isinstance(events, list)
    for e in events:
        assert e.project_id == "nonexistent_project" or not e.project_id


def test_inbox_empty_or_pending(tmp_path: Path) -> None:
    items = build_inbox(repo_root=tmp_path, status="pending", limit=20)
    assert isinstance(items, list)
    for i in items:
        assert i.status == "pending"


def test_inbox_all_status(tmp_path: Path) -> None:
    items = build_inbox(repo_root=tmp_path, status="", limit=30)
    assert isinstance(items, list)


def test_get_item_unknown(tmp_path: Path) -> None:
    item = get_item("inbox_nonexistent_id_xyz", repo_root=tmp_path)
    assert item is None


def test_inspect_item_unknown(tmp_path: Path) -> None:
    info = inspect_item("inbox_nonexistent_id_xyz", repo_root=tmp_path)
    assert "error" in info
    assert "not found" in info["error"].lower()


def test_timeline_event_roundtrip() -> None:
    e = TimelineEvent(
        event_id="evt_1",
        kind=EVENT_ACTION_QUEUED,
        timestamp_utc="2025-01-15T10:00:00",
        summary="Action queued",
        entity_refs={"queue_id": "q1"},
    )
    d = e.to_dict()
    e2 = TimelineEvent.from_dict(d)
    assert e2.event_id == e.event_id
    assert e2.kind == e.kind
    assert e2.entity_refs == e.entity_refs


def test_intervention_item_roundtrip() -> None:
    i = InterventionItem(
        item_id="inbox_1",
        kind=ITEM_APPROVAL_QUEUE,
        status="pending",
        summary="Approve run",
        source_ref="queue_abc",
    )
    d = i.to_dict()
    i2 = InterventionItem.from_dict(d)
    assert i2.item_id == i.item_id
    assert i2.kind == i.kind
    assert i2.source_ref == i.source_ref


def test_operator_notes_save_load(tmp_path: Path) -> None:
    save_operator_note("item_1", "test note", tmp_path)
    notes = load_operator_notes(tmp_path)
    assert notes.get("item_1") == "test note"


def test_inbox_snapshot_after_build(tmp_path: Path) -> None:
    build_inbox(repo_root=tmp_path, status="pending", limit=10)
    snapshot = load_inbox_snapshot(tmp_path)
    assert "inbox_count" in snapshot or snapshot == {}


# M29L.1 Digest views
from workflow_dataset.review_studio.digests import (
    DigestView,
    build_morning_summary,
    build_end_of_day_summary,
    build_project_summary,
    build_rollout_support_summary,
    format_digest_view,
)


def test_digest_morning(tmp_path: Path) -> None:
    d = build_morning_summary(repo_root=tmp_path, timeline_limit=10)
    assert d.digest_type == "morning"
    assert d.title == "Morning summary"
    assert "What changed" in format_digest_view(d)
    assert "What is blocked" in format_digest_view(d)
    assert "What needs approval" in format_digest_view(d)
    assert "Most important intervention" in format_digest_view(d)


def test_digest_end_of_day(tmp_path: Path) -> None:
    d = build_end_of_day_summary(repo_root=tmp_path, timeline_limit=10)
    assert d.digest_type == "end_of_day"
    assert "End-of-day" in d.title


def test_digest_project(tmp_path: Path) -> None:
    d = build_project_summary(project_id="founder_case_alpha", repo_root=tmp_path, timeline_limit=10)
    assert d.digest_type == "project"
    assert "founder_case_alpha" in d.title
    assert d.details.get("project_id") == "founder_case_alpha"


def test_digest_rollout_support(tmp_path: Path) -> None:
    d = build_rollout_support_summary(repo_root=tmp_path)
    assert d.digest_type == "rollout_support"
    assert "Rollout" in d.title or "support" in d.title


def test_format_digest_view() -> None:
    dv = DigestView(
        digest_type="morning",
        title="Test",
        what_changed=["  a"],
        what_is_blocked=["  b"],
        what_needs_approval=["  c"],
        most_important_intervention="do X",
    )
    out = format_digest_view(dv)
    assert "Test" in out
    assert "do X" in out
    assert "What changed" in out
    assert "What is blocked" in out
