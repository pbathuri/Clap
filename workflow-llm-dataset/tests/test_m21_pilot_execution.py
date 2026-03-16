"""M21: Tests for pilot session tracking, feedback capture, aggregation, CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.pilot.session_models import PilotSessionRecord, PilotFeedbackRecord
from workflow_dataset.pilot.session_log import (
    start_session,
    end_session,
    get_current_session_id,
    load_session,
    list_sessions,
    get_latest_session,
    append_session_commands,
    append_session_blocking,
)
from workflow_dataset.pilot.feedback_capture import capture_feedback, load_feedback
from workflow_dataset.pilot.aggregate import aggregate_sessions, write_aggregate_report


def test_session_start_end(tmp_path: Path) -> None:
    record = start_session(
        operator="op1", pilot_scope="ops", pilot_dir=tmp_path)
    assert record.session_id.startswith("pilot_")
    assert record.timestamp_start
    assert get_current_session_id(tmp_path) == record.session_id
    loaded = load_session(record.session_id, tmp_path)
    assert loaded is not None
    assert loaded.operator == "op1"
    ended = end_session(session_id=record.session_id, operator_notes="Done",
                        disposition="continue", pilot_dir=tmp_path)
    assert ended is not None
    assert ended.timestamp_end
    assert ended.disposition == "continue"
    assert get_current_session_id(tmp_path) == ""


def test_session_append_commands_blocking(tmp_path: Path) -> None:
    record = start_session(pilot_dir=tmp_path)
    append_session_commands(
        record.session_id, ["pilot verify", "release run"], pilot_dir=tmp_path)
    append_session_blocking(
        record.session_id, ["Graph missing"], pilot_dir=tmp_path)
    loaded = load_session(record.session_id, tmp_path)
    assert loaded is not None
    assert "pilot verify" in loaded.commands_run
    assert "Graph missing" in loaded.blocking_issues


def test_list_sessions(tmp_path: Path) -> None:
    r1 = start_session(operator="a", pilot_dir=tmp_path)
    end_session(r1.session_id, pilot_dir=tmp_path)
    r2 = start_session(operator="b", pilot_dir=tmp_path)
    sessions = list_sessions(tmp_path)
    assert len(sessions) >= 2
    latest = get_latest_session(tmp_path)
    assert latest is not None


def test_capture_feedback(tmp_path: Path) -> None:
    record = start_session(pilot_dir=tmp_path)
    path = capture_feedback(
        session_id=record.session_id,
        usefulness_score=4,
        trust_score=3,
        blocker_encountered=False,
        pilot_dir=tmp_path,
    )
    assert path.exists()
    fb = load_feedback(record.session_id, tmp_path)
    assert fb is not None
    assert fb.usefulness_score == 4
    assert fb.trust_score == 3


def test_capture_feedback_uses_current_session(tmp_path: Path) -> None:
    record = start_session(pilot_dir=tmp_path)
    path = capture_feedback(usefulness_score=3, pilot_dir=tmp_path)
    assert path.exists()
    assert record.session_id in str(path)


def test_aggregate_sessions(tmp_path: Path) -> None:
    r1 = start_session(pilot_dir=tmp_path, degraded_mode=True)
    append_session_blocking(
        r1.session_id, ["Graph missing"], pilot_dir=tmp_path)
    end_session(r1.session_id, disposition="fix", pilot_dir=tmp_path)
    capture_feedback(session_id=r1.session_id,
                     usefulness_score=3, pilot_dir=tmp_path)
    data = aggregate_sessions(pilot_dir=tmp_path)
    assert data["sessions_count"] >= 1
    assert "Graph missing" in data.get("recurring_blockers", [])
    assert data.get("degraded_count", 0) >= 1
    assert "fix" in data.get("disposition_counts", {})


def test_write_aggregate_report(tmp_path: Path) -> None:
    start_session(pilot_dir=tmp_path)
    json_path, md_path = write_aggregate_report(pilot_dir=tmp_path)
    assert json_path.exists()
    assert md_path.exists()
    assert "Sessions included" in md_path.read_text()
    assert "Structured evidence summary" in md_path.read_text()
    assert "Output quality (pilot evidence)" in md_path.read_text()
    data = json.loads(json_path.read_text())
    assert "evidence_quality" in data
    eq = data["evidence_quality"]
    assert "structured_user_quote_count" in eq
    assert "structured_friction_count" in eq


def test_cli_start_session(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    r = runner.invoke(app, ["pilot", "start-session",
                      "--pilot-dir", str(tmp_path)])
    assert r.exit_code == 0
    assert "Session started" in r.output


def test_cli_end_session(tmp_path: Path) -> None:
    from workflow_dataset.pilot.session_log import start_session
    rec = start_session(pilot_dir=tmp_path)
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    r = runner.invoke(app, ["pilot", "end-session", "--session-id", rec.session_id,
                      "--disposition", "continue", "--pilot-dir", str(tmp_path)])
    assert r.exit_code == 0
    assert "Session ended" in r.output


def test_cli_capture_feedback(tmp_path: Path) -> None:
    from workflow_dataset.pilot.session_log import start_session
    rec = start_session(pilot_dir=tmp_path)
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    r = runner.invoke(app, ["pilot", "capture-feedback", "--session-id",
                      rec.session_id, "--usefulness", "4", "--pilot-dir", str(tmp_path)])
    assert r.exit_code == 0
    assert "Feedback saved" in r.output


def test_cli_capture_feedback_structured_and_notes(tmp_path: Path) -> None:
    """--next-steps-specific and --report-location-clear are appended to notes."""
    from workflow_dataset.pilot.session_log import start_session
    rec = start_session(pilot_dir=tmp_path)
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    r = runner.invoke(
        app,
        [
            "pilot", "capture-feedback",
            "--session-id", rec.session_id,
            "--usefulness", "3",
            "--user-quote", "Where is the report?",
            "--friction", "Output path unclear",
            "--next-steps-specific", "no",
            "--report-location-clear", "yes",
            "--pilot-dir", str(tmp_path),
        ],
    )
    assert r.exit_code == 0
    assert "Feedback saved" in r.output
    fb = load_feedback(rec.session_id, tmp_path)
    assert fb is not None
    assert "next steps specific enough: no" in (fb.freeform_notes or "").lower()
    assert "report location clear: yes" in (fb.freeform_notes or "").lower()
    assert (fb.user_quote or "").strip() == "Where is the report?"
    assert (fb.operator_friction_notes or "").strip() == "Output path unclear"


def test_cli_aggregate(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    r = runner.invoke(app, ["pilot", "aggregate",
                      "--pilot-dir", str(tmp_path)])
    assert r.exit_code == 0
    assert "Aggregate report" in r.output


def test_cli_latest_summary(tmp_path: Path) -> None:
    from workflow_dataset.pilot.session_log import start_session
    start_session(pilot_dir=tmp_path)
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    r = runner.invoke(app, ["pilot", "latest-summary",
                      "--pilot-dir", str(tmp_path)])
    assert r.exit_code == 0
    assert "Latest session" in r.output or "session" in r.output.lower()


def test_pilot_verify_still_works() -> None:
    """Ensure existing pilot verify is unchanged (no crash)."""
    from workflow_dataset.pilot.health import pilot_verify_result
    result = pilot_verify_result()
    assert "ready" in result
    assert "blocking" in result
    assert "warnings" in result


def test_readiness_report_includes_m21_evidence(tmp_path: Path) -> None:
    """Readiness report includes M21 pilot evidence section (session/feedback counts)."""
    from workflow_dataset.pilot.health import write_pilot_readiness_report
    out = tmp_path / "pilot_readiness_report.md"
    write_pilot_readiness_report(output_path=out, pilot_dir=tmp_path)
    content = out.read_text()
    assert "M21 pilot evidence" in content
    assert "Pilot sessions completed" in content
    assert "Structured feedback entries" in content
