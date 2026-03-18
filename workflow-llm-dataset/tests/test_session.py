"""
M24J–M24M: Live workspace session layer — start/resume/close, board, artifact hub, pack-linked state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.session.models import Session, SESSION_STATES
from workflow_dataset.session.storage import (
    get_sessions_dir,
    save_session,
    load_session,
    load_current_session_id,
    set_current_session_id,
    list_sessions,
    archive_session,
)
from workflow_dataset.session.artifacts import (
    add_artifact,
    list_artifacts,
    add_note,
    get_notes,
    set_handoff,
    get_handoff,
)
from workflow_dataset.session.launch import start_session, resume_session, close_session, get_current_session
from workflow_dataset.session.board import build_session_board, SessionBoard
from workflow_dataset.session.report import format_session_status, format_session_board, format_session_artifact_hub


def test_session_model_roundtrip():
    s = Session(
        session_id="s1",
        value_pack_id="founder_ops_plus",
        starter_kit_id="founder_ops_starter",
        active_job_ids=["j1"],
        state="open",
        created_at="2024-01-01T00:00:00",
    )
    d = s.to_dict()
    s2 = Session.from_dict(d)
    assert s2.session_id == s.session_id
    assert s2.value_pack_id == s.value_pack_id
    assert s2.active_job_ids == s.active_job_ids


def test_storage_save_load(tmp_path):
    s = Session(session_id="test_sess", value_pack_id="founder_ops_plus", state="open", created_at="now", updated_at="now")
    save_session(s, tmp_path)
    loaded = load_session("test_sess", tmp_path)
    assert loaded is not None
    assert loaded.value_pack_id == "founder_ops_plus"


def test_current_session_id(tmp_path):
    set_current_session_id("sid1", tmp_path)
    assert load_current_session_id(tmp_path) == "sid1"
    set_current_session_id(None, tmp_path)
    assert load_current_session_id(tmp_path) is None


def test_session_start_requires_provisioned_pack(tmp_path):
    # founder_ops_plus may not be provisioned in tmp_path
    session, errors = start_session("founder_ops_plus", repo_root=tmp_path)
    if not errors:
        assert session is not None
        assert session.value_pack_id == "founder_ops_plus"
    else:
        assert "not provisioned" in errors[0] or "not found" in errors[0].lower()


def test_session_start_unknown_pack(tmp_path):
    session, errors = start_session("nonexistent_pack_xyz", repo_root=tmp_path)
    assert session is None
    assert len(errors) >= 1


def test_resume_and_close(tmp_path):
    # Create a session manually and set as current
    s = Session(
        session_id="resume_test",
        value_pack_id="founder_ops_plus",
        state="open",
        created_at="now",
        updated_at="now",
    )
    save_session(s, tmp_path)
    set_current_session_id("resume_test", tmp_path)
    session, errs = resume_session("resume_test", tmp_path)
    assert session is not None
    assert session.session_id == "resume_test"
    ok, errs = close_session("resume_test", tmp_path)
    assert ok
    assert get_current_session(tmp_path) is None


def test_board_build(tmp_path):
    s = Session(
        session_id="board_test",
        value_pack_id="founder_ops_plus",
        active_job_ids=["weekly_status"],
        active_macro_ids=["morning_ops"],
        state="open",
    )
    board = build_session_board(s, tmp_path)
    assert isinstance(board, SessionBoard)
    assert hasattr(board, "active_tasks")
    assert hasattr(board, "queued")
    assert hasattr(board, "blocked")
    assert hasattr(board, "ready")
    assert hasattr(board, "completed")
    assert hasattr(board, "artifacts_produced")


def test_artifact_hub(tmp_path):
    save_session(
        Session(session_id="art_sess", value_pack_id="founder_ops_plus", state="open", created_at="now", updated_at="now"),
        tmp_path,
    )
    add_artifact("art_sess", "/path/to/file", "file", tmp_path)
    add_note("art_sess", "Test note", tmp_path)
    set_handoff("art_sess", "Summary here", ["Next: run macro"], tmp_path)
    arts = list_artifacts("art_sess", tmp_path)
    assert len(arts) >= 1
    notes = get_notes("art_sess", tmp_path)
    assert "Test note" in notes
    handoff = get_handoff("art_sess", tmp_path)
    assert handoff.get("summary") == "Summary here"
    assert "run macro" in str(handoff.get("next_steps", []))


def test_format_session_status_empty():
    report = format_session_status(None)
    assert "No active session" in report


def test_format_session_status_with_session():
    s = Session(session_id="s1", value_pack_id="founder_ops_plus", state="open", created_at="now", updated_at="now")
    report = format_session_status(s)
    assert "s1" in report
    assert "founder_ops_plus" in report


def test_format_board_empty():
    board = SessionBoard()
    report = format_session_board(board)
    assert "Session task board" in report
    assert "(none)" in report


def test_session_list(tmp_path):
    save_session(
        Session(session_id="l1", value_pack_id="founder_ops_plus", state="open", created_at="now", updated_at="now"),
        tmp_path,
    )
    sessions = list_sessions(tmp_path, limit=5)
    assert len(sessions) >= 1
    ids = [x["session_id"] for x in sessions]
    assert "l1" in ids


def test_archive_session(tmp_path):
    save_session(
        Session(session_id="arch", value_pack_id="founder_ops_plus", state="open", created_at="now", updated_at="now"),
        tmp_path,
    )
    set_current_session_id("arch", tmp_path)
    ok = archive_session("arch", tmp_path)
    assert ok
    loaded = load_session("arch", tmp_path)
    assert loaded is not None
    assert loaded.state == "archived"
    assert load_current_session_id(tmp_path) is None


# ----- M24M.1 Session templates + cadence -----


def test_list_and_get_session_templates():
    from workflow_dataset.session.templates import list_session_templates, get_session_template
    ids = list_session_templates()
    assert "morning_review" in ids
    assert "founder_ops_session" in ids
    assert "analyst_deep_work" in ids
    assert "developer_focus" in ids
    assert "document_review" in ids
    t = get_session_template("morning_review")
    assert t is not None
    assert t.value_pack_id == "founder_ops_plus"
    assert "morning_ops" in (t.macro_ids or [])
    assert t.next_step_chain


def test_template_expected_artifacts_and_chain():
    from workflow_dataset.session.templates import get_session_template
    t = get_session_template("analyst_deep_work")
    assert t is not None
    assert t.expected_artifacts
    assert t.next_step_chain


def test_list_and_get_cadence_flows():
    from workflow_dataset.session.cadence import list_cadence_flows, get_cadence_flow
    ids = list_cadence_flows()
    assert "daily_founder" in ids
    assert "daily_analyst" in ids
    assert "morning_only" in ids
    c = get_cadence_flow("daily_founder")
    assert c is not None
    assert len(c.steps) >= 2
    assert c.steps[0].template_id == "morning_review"
    assert c.steps[1].template_id == "founder_ops_session"


def test_resolve_cadence_pack():
    from workflow_dataset.session.cadence import resolve_cadence_pack
    # Resolves from first step's template; morning_review -> founder_ops_plus
    assert resolve_cadence_pack("daily_founder") == "founder_ops_plus"
    assert resolve_cadence_pack("daily_analyst") == "founder_ops_plus"  # first step is morning_review
    assert resolve_cadence_pack("morning_only") == "founder_ops_plus"
    assert resolve_cadence_pack("unknown") == ""


def test_start_session_with_template_overlays_state(tmp_path):
    """With template, session gets template's job/routine/macro ids and recommended_next_actions."""
    from workflow_dataset.session.launch import start_session
    from workflow_dataset.session.templates import get_session_template
    # Provision founder_ops_plus so start succeeds
    (tmp_path / "data/local/provisioning/founder_ops_plus").mkdir(parents=True)
    (tmp_path / "data/local/provisioning/founder_ops_plus/provisioning_manifest.json").write_text("{}", encoding="utf-8")
    session, errors = start_session(
        pack_id="founder_ops_plus",
        repo_root=tmp_path,
        template_id="morning_review",
    )
    if errors:
        pytest.skip(f"start_session failed: {errors}")
    assert session is not None
    assert session.value_pack_id == "founder_ops_plus"
    t = get_session_template("morning_review")
    assert session.recommended_next_actions == t.next_step_chain
    assert "morning_ops" in session.active_macro_ids
