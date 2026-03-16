"""M19: Tests for feedback models, store, summary, and aggregation."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.feedback.feedback_models import TrialFeedbackEntry, TrialSessionSummary
from workflow_dataset.feedback.feedback_store import (
    save_feedback_entry,
    load_feedback_entries,
    save_session_summary,
    load_session_summaries,
)
from workflow_dataset.feedback.feedback_summary import aggregate_feedback, write_feedback_report
from workflow_dataset.feedback.friendly_tasks import load_friendly_trial_tasks, get_task_by_id
from workflow_dataset.feedback.session_store import get_current_session, set_current_session, clear_current_session
from workflow_dataset.feedback.trial_events import record_trial_event, load_trial_events


def test_feedback_entry_model() -> None:
    """TrialFeedbackEntry validates and defaults."""
    e = TrialFeedbackEntry(
        task_id="ops_summarize_reporting",
        session_id="sess_abc",
        outcome_rating="completed",
        usefulness_rating=4,
        trust_rating=3,
    )
    assert e.task_id == "ops_summarize_reporting"
    assert e.usefulness_rating == 4
    assert e.trust_rating == 3
    assert e.feedback_id == ""


def test_session_summary_model() -> None:
    """TrialSessionSummary validates."""
    s = TrialSessionSummary(
        session_id="sess_xyz",
        tasks_attempted=3,
        tasks_completed=2,
    )
    assert s.tasks_attempted == 3
    assert s.tasks_completed == 2


def test_save_and_load_feedback_entries(tmp_path: Path) -> None:
    """Save feedback entries and load them back; IDs auto-generated."""
    e1 = TrialFeedbackEntry(
        session_id="s1",
        task_id="ops_next_steps",
        outcome_rating="completed",
        created_utc="2025-01-01T00:00:00Z",
    )
    e2 = TrialFeedbackEntry(
        feedback_id="fb_custom123",
        session_id="s1",
        task_id="ops_summarize_reporting",
        outcome_rating="partial",
    )
    p1 = save_feedback_entry(e1, tmp_path)
    p2 = save_feedback_entry(e2, tmp_path)
    assert p1.parent == tmp_path / "feedback"
    assert p2.name == "fb_custom123.json"
    loaded = load_feedback_entries(tmp_path)
    assert len(loaded) == 2
    task_ids = {x.task_id for x in loaded}
    assert "ops_next_steps" in task_ids
    assert "ops_summarize_reporting" in task_ids


def test_save_and_load_session_summaries(tmp_path: Path) -> None:
    """Save session summaries and load back."""
    s = TrialSessionSummary(
        session_id="sess_1",
        user_id_or_alias="alice",
        tasks_attempted=2,
        tasks_completed=1,
    )
    path = save_session_summary(s, tmp_path)
    assert path.parent == tmp_path / "summaries"
    assert path.name.startswith("sum_")
    summaries = load_session_summaries(tmp_path)
    assert len(summaries) == 1
    assert summaries[0].session_id == "sess_1"
    assert summaries[0].tasks_completed == 1


def test_aggregate_feedback(tmp_path: Path) -> None:
    """Aggregate produces counts and samples."""
    for i, task_id in enumerate(["ops_summarize_reporting", "ops_next_steps", "ops_next_steps"]):
        e = TrialFeedbackEntry(
            session_id="s1",
            task_id=task_id,
            outcome_rating="completed" if i < 2 else "failed",
            usefulness_rating=4,
            trust_rating=3,
            freeform_feedback=f"note_{i}",
        )
        save_feedback_entry(e, tmp_path)
    s = TrialSessionSummary(
        session_id="s1",
        tasks_attempted=3,
        tasks_completed=2,
    )
    save_session_summary(s, tmp_path)
    agg = aggregate_feedback(tmp_path)
    assert agg["num_entries"] == 3
    assert agg["num_sessions"] == 1
    assert agg["outcome_completed"] == 2
    assert agg["outcome_failed"] == 1
    assert agg["by_task"]["ops_summarize_reporting"] == 1
    assert agg["by_task"]["ops_next_steps"] == 2
    assert agg["avg_usefulness"] == 4.0
    assert "note_" in str(agg["freeform_samples"])


def test_write_feedback_report(tmp_path: Path) -> None:
    """write_feedback_report produces a markdown file with recommendation."""
    e = TrialFeedbackEntry(
        session_id="s1",
        task_id="ops_summarize_reporting",
        outcome_rating="completed",
        usefulness_rating=4,
        trust_rating=3,
    )
    save_feedback_entry(e, tmp_path)
    out_path = tmp_path / "report.md"
    path = write_feedback_report(output_path=out_path, store_path=tmp_path)
    assert path == out_path
    content = path.read_text()
    assert "Trial feedback report" in content
    assert "ops_summarize_reporting" in content
    assert "Recommendation" in content


def test_load_friendly_trial_tasks_empty(tmp_path: Path) -> None:
    """Missing tasks file returns empty list."""
    tasks = load_friendly_trial_tasks(tmp_path / "nonexistent.json")
    assert tasks == []


def test_load_friendly_trial_tasks_from_fixture(tmp_path: Path) -> None:
    """Load tasks from a JSON array."""
    tasks_file = tmp_path / "friendly_trial_tasks.json"
    tasks_file.write_text(
        '[{"task_id": "ops_a", "priority": "must_try", "short_description": "Do A"},'
        '{"task_id": "ops_b", "priority": "nice_to_try", "short_description": "Do B"}]'
    )
    tasks = load_friendly_trial_tasks(tasks_file)
    assert len(tasks) == 2
    assert get_task_by_id("ops_a", tasks_file)["short_description"] == "Do A"
    assert get_task_by_id("ops_c", tasks_file) is None


def test_session_store(tmp_path: Path) -> None:
    """get/set/clear current session."""
    assert get_current_session(tmp_path) == {}
    data = set_current_session(user_alias="bob", store_path=tmp_path)
    assert "session_id" in data
    assert data["user_alias"] == "bob"
    assert get_current_session(tmp_path)["session_id"] == data["session_id"]
    clear_current_session(tmp_path)
    assert get_current_session(tmp_path) == {}


def test_trial_events(tmp_path: Path) -> None:
    """record_trial_event and load_trial_events."""
    record_trial_event("task_selected", {"task_id": "ops_next_steps"}, store_path=tmp_path)
    record_trial_event("generation_succeeded", {"task_id": "ops_next_steps"}, store_path=tmp_path)
    events = load_trial_events(tmp_path)
    assert len(events) == 2
    types = {e["event_type"] for e in events}
    assert "task_selected" in types
    assert "generation_succeeded" in types
