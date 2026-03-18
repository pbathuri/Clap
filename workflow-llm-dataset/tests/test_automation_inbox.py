"""
M34I–M34L: Tests for automation inbox and recurring outcome digests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.automation_inbox.models import (
    AutomationInboxItem,
    RecurringDigest,
    ITEM_BLOCKED_AUTOMATION,
    ITEM_AUTOMATION_RESULT,
    STATUS_PENDING,
)
from workflow_dataset.automation_inbox.store import (
    get_automation_inbox_root,
    save_decision,
    get_latest_decision,
    list_decisions,
    save_operator_note,
    load_operator_notes,
)
from workflow_dataset.automation_inbox.collect import build_automation_inbox, collect_from_background_runs
from workflow_dataset.automation_inbox.digests import (
    build_morning_automation_digest,
    build_blocked_automation_digest,
    format_digest,
)
from workflow_dataset.automation_inbox.flows import (
    get_item,
    inspect_item,
    accept_item,
    archive_item,
    dismiss_item,
    escalate_item,
)


def test_automation_inbox_item_model():
    item = AutomationInboxItem(
        item_id="auto_abc123",
        kind=ITEM_BLOCKED_AUTOMATION,
        status=STATUS_PENDING,
        summary="Blocked: run_1",
        run_id="run_1",
        automation_id="aut_1",
    )
    d = item.to_dict()
    assert d["item_id"] == "auto_abc123"
    assert d["kind"] == ITEM_BLOCKED_AUTOMATION
    loaded = AutomationInboxItem.from_dict(d)
    assert loaded.run_id == item.run_id


def test_recurring_digest_model():
    digest = RecurringDigest(
        digest_id="dig_xyz",
        digest_type="morning_automation",
        title="Morning automation digest",
        completed_runs=["  run_1: ok"],
        blocked_or_failed=["  run_2: blocked"],
        most_important_follow_up="Review inbox",
    )
    d = digest.to_dict()
    assert d["digest_type"] == "morning_automation"
    loaded = RecurringDigest.from_dict(d)
    assert loaded.most_important_follow_up == digest.most_important_follow_up


def test_save_and_get_decision(tmp_path: Path):
    save_decision("auto_1", "accepted", note="Done", repo_root=tmp_path)
    dec = get_latest_decision("auto_1", repo_root=tmp_path)
    assert dec is not None
    assert dec.get("decision") == "accepted"
    assert dec.get("item_id") == "auto_1"
    entries = list_decisions(item_id="auto_1", repo_root=tmp_path)
    assert len(entries) >= 1


def test_operator_notes(tmp_path: Path):
    save_operator_note("auto_1", "My note", repo_root=tmp_path)
    notes = load_operator_notes(tmp_path)
    assert notes.get("auto_1") == "My note"


def test_build_automation_inbox_empty(tmp_path: Path):
    """Empty state: no background runs -> empty inbox."""
    items = build_automation_inbox(repo_root=tmp_path, status="pending", limit=50)
    assert isinstance(items, list)
    assert len(items) == 0


def test_morning_digest_empty(tmp_path: Path):
    """Empty state: morning digest still returns valid structure."""
    digest = build_morning_automation_digest(repo_root=tmp_path)
    assert digest.digest_type == "morning_automation"
    assert digest.title == "Morning automation digest"
    assert "completed_runs" in digest.to_dict()
    assert "blocked_or_failed" in digest.to_dict()
    text = format_digest(digest)
    assert "Morning automation digest" in text
    assert "Most important follow-up" in text or "follow-up" in text.lower()


def test_blocked_digest_empty(tmp_path: Path):
    digest = build_blocked_automation_digest(repo_root=tmp_path)
    assert digest.digest_type == "blocked_automation"
    assert "Blocked automation digest" in digest.title


def test_accept_archive_flow(tmp_path: Path):
    """Accept/archive/dismiss record decision; get_item on unknown returns None."""
    result = get_item("nonexistent_id", repo_root=tmp_path)
    assert result is None
    # Create a synthetic item by having one in inbox from a real run would require background_run data;
    # instead test that accept_item returns error for missing item
    out = accept_item("nonexistent_id", repo_root=tmp_path)
    assert out.get("error") is not None
    out = archive_item("nonexistent_id", repo_root=tmp_path)
    assert out.get("error") is not None
    out = dismiss_item("nonexistent_id", repo_root=tmp_path)
    assert out.get("error") is not None
    out = escalate_item("nonexistent_id", repo_root=tmp_path)
    assert out.get("error") is not None


def test_inspect_missing_item(tmp_path: Path):
    info = inspect_item("nonexistent_id", repo_root=tmp_path)
    assert info.get("error") == "Automation inbox item not found: nonexistent_id"


def test_get_automation_inbox_root(tmp_path: Path):
    root = get_automation_inbox_root(tmp_path)
    assert "automation_inbox" in str(root)
    assert root == tmp_path / "data/local/automation_inbox"


# ----- M34L.1 Morning briefs + continuity cards -----

def test_morning_brief_card_model():
    from workflow_dataset.automation_inbox.models import MorningBriefCard, HandoffTarget
    handoff = HandoffTarget(label="Review inbox", target_type="action", command="workflow-dataset inbox list")
    brief = MorningBriefCard(
        brief_id="brief_abc",
        title="Morning brief",
        what_happened_while_away=["  Completed: run_1"],
        top_next_action="workflow-dataset automation-inbox list",
        handoff=handoff,
    )
    d = brief.to_dict()
    assert d["brief_id"] == "brief_abc"
    assert d["handoff"]["label"] == "Review inbox"
    loaded = MorningBriefCard.from_dict(d)
    assert loaded.top_next_action == brief.top_next_action


def test_continuity_card_model():
    from workflow_dataset.automation_inbox.models import ResumeWorkContinuityCard
    card = ResumeWorkContinuityCard(
        card_id="card_xyz",
        resume_context="Last context: founder_case_alpha",
        what_happened_while_away=["  (no recent activity)"],
        suggested_next="workflow-dataset inbox list",
    )
    d = card.to_dict()
    assert d["card_id"] == "card_xyz"
    assert "founder_case_alpha" in d["resume_context"]


def test_build_morning_brief(tmp_path: Path):
    from workflow_dataset.automation_inbox import build_morning_brief, format_morning_brief
    brief = build_morning_brief(repo_root=tmp_path)
    assert brief.title == "Morning brief"
    assert "what_happened_while_away" in brief.to_dict()
    assert brief.top_next_action
    text = format_morning_brief(brief)
    assert "Morning brief" in text
    assert "What happened" in text or "what happened" in text.lower()


def test_build_resume_continuity_card(tmp_path: Path):
    from workflow_dataset.automation_inbox import build_resume_continuity_card, format_continuity_card
    card = build_resume_continuity_card(repo_root=tmp_path)
    assert card.title == "Resume work"
    assert card.resume_context
    assert "what_happened_while_away" in card.to_dict()
    text = format_continuity_card(card)
    assert "Resume" in text
    assert "Suggested next" in text or "suggested" in text.lower()


def test_build_what_happened_summary(tmp_path: Path):
    from workflow_dataset.automation_inbox import build_what_happened_summary
    lines = build_what_happened_summary(repo_root=tmp_path)
    assert isinstance(lines, list)
    assert len(lines) >= 1
    assert "(no recent activity)" in lines[0] or "Completed" in lines[0] or "[" in lines[0]


def test_get_recommended_handoff(tmp_path: Path):
    from workflow_dataset.automation_inbox import get_recommended_handoff
    handoff = get_recommended_handoff(repo_root=tmp_path)
    assert handoff is not None
    assert handoff.label
    assert handoff.command
