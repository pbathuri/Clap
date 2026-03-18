"""
M36I–M36L: Tests for continuity engine — morning flow, shutdown flow, resume, changes-since-last, carry-forward, empty state.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from workflow_dataset.continuity_engine.models import (
    ChangeSinceLastSession,
    MorningEntryBrief,
    ShutdownSummary,
    ResumeCard,
)
from workflow_dataset.continuity_engine.store import (
    get_last_session_end_utc,
    save_last_session_end,
    load_last_shutdown,
    save_next_session_recommendation,
)
from workflow_dataset.continuity_engine.models import NextSessionRecommendation
from workflow_dataset.continuity_engine.changes import build_changes_since_last_session
from workflow_dataset.continuity_engine.morning_flow import build_morning_entry_flow
from workflow_dataset.continuity_engine.shutdown_flow import build_shutdown_summary, build_carry_forward_list
from workflow_dataset.continuity_engine.resume_flow import build_resume_flow, get_strongest_resume_target
from workflow_dataset.continuity_engine.rhythm import list_rhythm_templates, get_rhythm_template, get_recommended_first_phase
from workflow_dataset.continuity_engine.carry_forward_policy import apply_carry_forward_policy, build_next_day_operating_recommendation
from workflow_dataset.continuity_engine.store import load_next_session_recommendation


def test_changes_since_last_session_empty(tmp_path: Path) -> None:
    """When no last session end, changes summary says so."""
    change = build_changes_since_last_session(repo_root=tmp_path)
    assert change.last_session_end_utc == ""
    assert "No previous session" in " ".join(change.summary_lines) or "No significant" in " ".join(change.summary_lines)


def test_morning_flow_generation(tmp_path: Path) -> None:
    """Morning entry flow produces brief with recommended first action."""
    brief = build_morning_entry_flow(repo_root=tmp_path)
    assert brief.brief_id.startswith("brief_")
    assert brief.generated_at_utc
    assert brief.recommended_first_action
    assert brief.recommended_first_command


@pytest.mark.slow
def test_shutdown_flow_generation(tmp_path: Path) -> None:
    """Shutdown summary is built and persisted; carry-forward list is populated."""
    summary = build_shutdown_summary(repo_root=tmp_path)
    assert summary.summary_id.startswith("shutdown_")
    assert summary.day_id
    assert summary.end_of_day_readiness in ("ready", "has_unresolved", "has_blocked", "")
    last = load_last_shutdown(tmp_path)
    assert last is not None
    assert last.summary_id == summary.summary_id


@pytest.mark.slow
def test_resume_flow_generation(tmp_path: Path) -> None:
    """Resume flow produces card with suggested first action."""
    card = build_resume_flow(repo_root=tmp_path)
    assert card.card_id.startswith("card_")
    assert card.suggested_first_action
    assert card.resume_target_label
    assert card.resume_target_command


@pytest.mark.slow
def test_strongest_resume_target(tmp_path: Path) -> None:
    """get_strongest_resume_target returns (label, command)."""
    label, cmd = get_strongest_resume_target(repo_root=tmp_path)
    assert label
    assert cmd


@pytest.mark.slow
def test_carry_forward_after_shutdown(tmp_path: Path) -> None:
    """After shutdown, carry-forward list can be loaded."""
    build_shutdown_summary(repo_root=tmp_path)
    items = build_carry_forward_list(repo_root=tmp_path)
    # May be 0 if queue was empty
    assert isinstance(items, list)


def test_save_last_session_end(tmp_path: Path) -> None:
    """Saving last session end allows changes_since_last to have a baseline."""
    save_last_session_end("2025-01-01T18:00:00Z", repo_root=tmp_path)
    assert get_last_session_end_utc(tmp_path) == "2025-01-01T18:00:00Z"
    change = build_changes_since_last_session(repo_root=tmp_path)
    assert change.last_session_end_utc == "2025-01-01T18:00:00Z"


@pytest.mark.slow
def test_empty_state_no_prior_session(tmp_path: Path) -> None:
    """Empty state: no prior session, morning and resume still return valid structures."""
    brief = build_morning_entry_flow(repo_root=tmp_path)
    assert brief.change_since_last is None or brief.change_since_last.last_session_end_utc == ""
    card = build_resume_flow(repo_root=tmp_path)
    assert card.what_remains or card.suggested_first_action


# ---------- M36L.1 Daily rhythm templates + carry-forward policy ----------


def test_rhythm_list_returns_default(tmp_path: Path) -> None:
    """List rhythm templates returns at least the default template."""
    templates = list_rhythm_templates(repo_root=tmp_path)
    assert len(templates) >= 1
    assert any(t.template_id == "default" for t in templates)
    t = get_rhythm_template(template_id="default", repo_root=tmp_path)
    assert t is not None
    assert t.name
    assert len(t.phases) >= 1


def test_rhythm_recommended_first_phase(tmp_path: Path) -> None:
    """get_recommended_first_phase returns phase_id, label, command."""
    phase_id, label, cmd = get_recommended_first_phase(repo_root=tmp_path)
    assert phase_id
    assert label
    assert cmd


def test_carry_forward_policy_empty_queue(tmp_path: Path) -> None:
    """Apply carry-forward policy to empty queue returns empty classes and rationale."""
    policy = apply_carry_forward_policy([], repo_root=tmp_path)
    assert policy.urgent_items == []
    assert policy.optional_items == []
    assert policy.automated_follow_up_items == []
    assert "No carry-forward" in " ".join(policy.rationale_lines) or len(policy.rationale_lines) >= 1


def test_build_next_day_operating_recommendation(tmp_path: Path) -> None:
    """build_next_day_operating_recommendation returns label, command, rationale."""
    from workflow_dataset.continuity_engine.models import CarryForwardPolicyOutput
    policy = CarryForwardPolicyOutput(
        urgent_items=[],
        optional_items=[],
        automated_follow_up_items=[],
        rationale_lines=["No items."],
        generated_at_utc="2025-01-01T00:00:00Z",
    )
    label, cmd, rationale = build_next_day_operating_recommendation(policy, tomorrow_start="", repo_root=tmp_path)
    assert label
    assert cmd
    assert isinstance(rationale, list)


def test_next_session_recommendation_m36l1_fields_roundtrip(tmp_path: Path) -> None:
    """NextSessionRecommendation with M36L.1 fields persists and loads."""
    rec = NextSessionRecommendation(
        generated_at_utc="2025-01-01T12:00:00Z",
        day_id="2025-01-01",
        likely_start_context="Project: proj_1",
        first_action_label="Review urgent carry-forward",
        first_action_command="workflow-dataset continuity carry-forward",
        carry_forward_count=2,
        blocked_count=0,
        urgent_carry_forward_count=1,
        optional_carry_forward_count=1,
        automated_follow_up_count=0,
        operating_mode="review_first",
        rationale_lines=["1 urgent carry-forward (approvals/blocked).", "1 optional carry-forward."],
    )
    save_next_session_recommendation(rec, repo_root=tmp_path)
    loaded = load_next_session_recommendation(repo_root=tmp_path)
    assert loaded is not None
    assert loaded.operating_mode == "review_first"
    assert loaded.urgent_carry_forward_count == 1
    assert loaded.optional_carry_forward_count == 1
    assert "urgent" in " ".join(loaded.rationale_lines)
