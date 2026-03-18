"""
Tests for the operator console state store.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.apply.apply_models import ApplyPlan
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def test_console_state_defaults() -> None:
    state = ConsoleState()
    assert state.selected_session_id == ""
    assert state.selected_project_id == ""
    assert state.selected_workspace_path == ""
    assert state.pending_apply_plan is None
    assert state.chat_messages == []


def test_console_state_set_session() -> None:
    state = ConsoleState()
    state.set_session("sess_123")
    assert state.selected_session_id == "sess_123"
    state.set_session("")
    assert state.selected_session_id == ""


def test_console_state_set_project() -> None:
    state = ConsoleState()
    state.set_project("proj_abc")
    assert state.selected_project_id == "proj_abc"


def test_console_state_set_workspace() -> None:
    state = ConsoleState()
    state.set_workspace("/tmp/ws")
    assert state.selected_workspace_path == "/tmp/ws"
    state.set_workspace(Path("/tmp/ws2"))
    assert state.selected_workspace_path == "/tmp/ws2"


def test_console_state_set_pending_apply() -> None:
    state = ConsoleState()
    plan = ApplyPlan(plan_id=stable_id("p", "1", utc_now_iso()), created_utc=utc_now_iso())
    state.set_pending_apply(plan, "/ws", "/target")
    assert state.pending_apply_plan is plan
    assert state.pending_apply_workspace_path == "/ws"
    assert state.pending_apply_target_path == "/target"
    state.clear_pending_apply()
    assert state.pending_apply_plan is None
    assert state.pending_apply_workspace_path == ""


def test_console_state_chat_turn() -> None:
    state = ConsoleState()
    state.add_chat_turn("user", "Hello")
    state.add_chat_turn("assistant", "Hi")
    assert len(state.chat_messages) == 2
    assert state.chat_messages[0]["role"] == "user"
    assert state.chat_messages[0]["content"] == "Hello"
    for _ in range(25):
        state.add_chat_turn("user", "x")
    assert len(state.chat_messages) <= 22
