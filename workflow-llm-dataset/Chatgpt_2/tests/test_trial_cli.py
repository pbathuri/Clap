"""M19: CLI tests for friendly trial commands (trial start, tasks, record-feedback, summary, aggregate-feedback)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from workflow_dataset.cli import app

runner = CliRunner()


def test_trial_start_creates_session(tmp_path: Path) -> None:
    """trial start creates current_session and prints session id."""
    result = runner.invoke(app, ["trial", "start", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "Trial session started" in result.output
    assert "sess_" in result.output
    sess_file = tmp_path / "current_session.json"
    assert sess_file.exists()
    import json
    data = json.loads(sess_file.read_text())
    assert "session_id" in data


def test_trial_start_with_user_alias(tmp_path: Path) -> None:
    """trial start --user sets alias in session."""
    result = runner.invoke(app, ["trial", "start", "--user", "alice", "--store", str(tmp_path)])
    assert result.exit_code == 0
    import json
    data = json.loads((tmp_path / "current_session.json").read_text())
    assert data.get("user_alias") == "alice"


def test_trial_tasks_empty_store(tmp_path: Path) -> None:
    """trial tasks with no tasks file prints message and exits 0."""
    result = runner.invoke(app, ["trial", "tasks", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "No tasks" in result.output or "no tasks" in result.output.lower()


def test_trial_tasks_with_fixture(tmp_path: Path) -> None:
    """trial tasks lists tasks from friendly_trial_tasks.json."""
    tasks_file = tmp_path / "friendly_trial_tasks.json"
    tasks_file.write_text(
        '[{"task_id": "ops_a", "priority": "must_try", "short_description": "Do A"},'
        '{"task_id": "ops_b", "priority": "nice_to_try", "short_description": "Do B"}]'
    )
    result = runner.invoke(app, ["trial", "tasks", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "ops_a" in result.output
    assert "ops_b" in result.output


def test_trial_record_feedback_creates_entry(tmp_path: Path) -> None:
    """trial record-feedback saves a feedback entry."""
    from workflow_dataset.feedback.session_store import set_current_session
    set_current_session(session_id="sess_test123", user_alias="bob", store_path=tmp_path)
    result = runner.invoke(app, [
        "trial", "record-feedback", "ops_summarize_reporting",
        "--outcome", "completed",
        "--usefulness", "4",
        "--trust", "3",
        "--store", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert "Feedback saved" in result.output
    feedback_dir = tmp_path / "feedback"
    assert feedback_dir.exists()
    files = list(feedback_dir.glob("fb_*.json"))
    assert len(files) >= 1


def test_trial_summary_no_session(tmp_path: Path) -> None:
    """trial summary without active session exits 1 with message."""
    result = runner.invoke(app, ["trial", "summary", "--store", str(tmp_path)])
    assert result.exit_code == 1
    assert "No active session" in result.output or "trial start" in result.output.lower()


def test_trial_summary_with_session_and_feedback(tmp_path: Path) -> None:
    """trial summary with session and feedback writes summary."""
    from workflow_dataset.feedback.session_store import set_current_session
    from workflow_dataset.feedback.feedback_store import save_feedback_entry
    from workflow_dataset.feedback.feedback_models import TrialFeedbackEntry
    set_current_session(session_id="sess_summary_test", user_alias="alice", store_path=tmp_path)
    e = TrialFeedbackEntry(
        session_id="sess_summary_test",
        task_id="ops_next_steps",
        outcome_rating="completed",
        usefulness_rating=4,
    )
    save_feedback_entry(e, tmp_path)
    result = runner.invoke(app, ["trial", "summary", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "Session summary" in result.output
    assert (tmp_path / "summaries").exists()
    assert list((tmp_path / "summaries").glob("sum_*.json"))


def test_trial_aggregate_feedback_creates_report(tmp_path: Path) -> None:
    """trial aggregate-feedback writes report file."""
    report_path = tmp_path / "latest_feedback_report.md"
    result = runner.invoke(app, [
        "trial", "aggregate-feedback",
        "--store", str(tmp_path),
        "--report", str(report_path),
    ])
    assert result.exit_code == 0
    assert "Feedback report" in result.output
    assert report_path.exists()
    content = report_path.read_text()
    assert "Trial feedback report" in content
    assert "Recommendation" in content


def test_trial_help() -> None:
    """trial --help shows subcommands."""
    result = runner.invoke(app, ["trial", "--help"])
    assert result.exit_code == 0
    assert "start" in result.output
    assert "tasks" in result.output
    assert "record-feedback" in result.output
    assert "summary" in result.output
    assert "aggregate-feedback" in result.output
