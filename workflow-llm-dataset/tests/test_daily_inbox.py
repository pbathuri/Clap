"""
M23V: Tests for daily inbox / digest.
"""

from pathlib import Path

import pytest


def test_build_daily_digest_structure(tmp_path: Path) -> None:
    """build_daily_digest returns DailyDigest with expected attributes."""
    from workflow_dataset.daily.inbox import build_daily_digest, DailyDigest
    digest = build_daily_digest(tmp_path)
    assert isinstance(digest, DailyDigest)
    assert hasattr(digest, "relevant_job_ids")
    assert hasattr(digest, "relevant_routine_ids")
    assert hasattr(digest, "blocked_items")
    assert hasattr(digest, "reminders_due")
    assert hasattr(digest, "approvals_needing_refresh")
    assert hasattr(digest, "trust_regressions")
    assert hasattr(digest, "recent_successful_runs")
    assert hasattr(digest, "recommended_next_action")
    assert hasattr(digest, "unresolved_corrections_count")
    assert isinstance(digest.relevant_job_ids, list)
    assert isinstance(digest.recommended_next_action, str)


def test_format_inbox_report(tmp_path: Path) -> None:
    """format_inbox_report produces non-empty string with expected sections."""
    from workflow_dataset.daily.inbox_report import format_inbox_report
    report = format_inbox_report(repo_root=tmp_path)
    assert isinstance(report, str)
    assert "Daily Inbox" in report or "start here" in report.lower()
    assert "Recommended next action" in report or "next action" in report.lower()
    assert "Operator-controlled" in report
