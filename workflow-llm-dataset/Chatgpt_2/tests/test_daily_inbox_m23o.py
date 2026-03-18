"""
M23O: Tests for daily inbox digest — inbox items (reason/trust/mode/blockers/outcome),
digest history, compare, explain, no-data behavior.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.daily.inbox import build_daily_digest, DailyDigest
from workflow_dataset.daily.inbox_report import format_inbox_report, format_explain_why_now
from workflow_dataset.daily.digest_history import (
    save_digest_snapshot,
    load_digest_snapshot,
    list_digest_snapshots,
    compare_digests,
    DigestCompare,
)


def test_digest_has_inbox_items_and_top_next(tmp_path: Path) -> None:
    digest = build_daily_digest(tmp_path, include_drift=False)
    assert hasattr(digest, "inbox_items")
    assert isinstance(digest.inbox_items, list)
    assert hasattr(digest, "top_next_recommended")
    assert isinstance(digest.top_next_recommended, dict)
    assert hasattr(digest, "created_at")
    assert hasattr(digest, "what_changed")


def test_digest_inbox_item_fields(tmp_path: Path) -> None:
    digest = build_daily_digest(tmp_path, include_drift=False)
    for item in digest.inbox_items[:5]:
        assert "id" in item or "reason" in item
        assert "kind" in item
        assert "reason" in item
        assert "mode_available" in item
        assert "blockers" in item
        assert "expected_outcome" in item


def test_format_inbox_report_includes_sections(tmp_path: Path) -> None:
    report = format_inbox_report(repo_root=tmp_path)
    assert "Daily Inbox" in report
    assert "Recommended next action" in report or "Top next" in report
    assert "Operator-controlled" in report


def test_format_explain_why_now(tmp_path: Path) -> None:
    text = format_explain_why_now(repo_root=tmp_path)
    assert "why these items now" in text or "inbox" in text.lower()


def test_blocked_state_reporting(tmp_path: Path) -> None:
    digest = build_daily_digest(tmp_path, include_drift=False)
    report = format_inbox_report(digest=digest)
    if digest.blocked_items:
        assert "Blocked" in report
        assert any(b.get("id") in report for b in digest.blocked_items)


def test_save_and_load_digest_snapshot(tmp_path: Path) -> None:
    digest = build_daily_digest(tmp_path, include_drift=False)
    path = save_digest_snapshot(digest, tmp_path)
    assert path.exists()
    loaded = load_digest_snapshot("latest", tmp_path)
    assert loaded is not None
    assert loaded.get("created_at")
    assert "recommended_next_action" in loaded or "top_next_recommended" in loaded


def test_compare_digests(tmp_path: Path) -> None:
    digest1 = build_daily_digest(tmp_path, include_drift=False)
    digest1.relevant_job_ids = ["job_a"]
    digest1.inbox_items = [{"id": "job_a", "kind": "job", "reason": "r1"}]
    digest1.blocked_items = [{"id": "job_a", "kind": "job", "reason": "blocked"}]
    d1 = {
        "inbox_item_ids": ["job_a"],
        "blocked_items": [{"id": "job_a"}],
        "created_at": "2025-01-01T00:00:00",
    }
    d2 = {
        "inbox_item_ids": ["job_a", "job_b"],
        "blocked_items": [],
        "created_at": "2025-01-02T00:00:00",
    }
    result = compare_digests(d1, d2)
    assert "job_b" in result.newly_appeared
    assert "job_a" in result.escalated


def test_list_digest_snapshots(tmp_path: Path) -> None:
    digest = build_daily_digest(tmp_path, include_drift=False)
    save_digest_snapshot(digest, tmp_path)
    listings = list_digest_snapshots(limit=5, repo_root=tmp_path)
    assert isinstance(listings, list)


def test_no_data_behavior(tmp_path: Path) -> None:
    digest = build_daily_digest(tmp_path, include_drift=False)
    assert digest.recommended_next_action != ""
    assert digest.top_next_recommended.get("label") is not None or digest.top_next_recommended.get("command") is not None
