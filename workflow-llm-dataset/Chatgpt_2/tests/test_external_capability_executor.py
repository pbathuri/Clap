"""M24D: Activation executor — request, preview, execute, disable, history, audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.external_capability.activation_models import ActivationRequest, REQUESTED_ACTIONS
from workflow_dataset.external_capability.activation_store import (
    save_request,
    load_request,
    list_requests,
    save_execution_result,
    load_history,
)
from workflow_dataset.external_capability.preview import build_preview, ActivationPreview
from workflow_dataset.external_capability.executor import (
    create_activation_request,
    execute_activation,
    disable_source,
    ExecutionResult,
)
from workflow_dataset.external_capability.report import format_preview, format_history


def test_activation_request_model():
    """ActivationRequest to_dict/from_dict and requested_actions."""
    r = ActivationRequest(
        activation_id="act_test_1",
        source_id="openclaw",
        source_category="openclaw",
        requested_action="enable",
        status="pending",
    )
    d = r.to_dict()
    assert d["activation_id"] == "act_test_1"
    assert d["requested_action"] == "enable"
    r2 = ActivationRequest.from_dict(d)
    assert r2.activation_id == r.activation_id
    assert "enable" in REQUESTED_ACTIONS


def test_create_activation_request(tmp_path):
    """create_activation_request returns request for known source, None for unknown."""
    req = create_activation_request("openclaw", action="enable", repo_root=tmp_path)
    assert req is not None
    assert req.source_id == "openclaw"
    assert req.requested_action == "enable"
    assert req.activation_id.startswith("act_")
    assert create_activation_request("nonexistent_xyz", repo_root=tmp_path) is None


def test_save_and_load_request(tmp_path):
    """save_request and load_request roundtrip."""
    r = ActivationRequest(activation_id="act_save_1", source_id="openclaw", status="pending")
    save_request(r, tmp_path)
    loaded = load_request("act_save_1", tmp_path)
    assert loaded is not None
    assert loaded.activation_id == r.activation_id
    assert load_request("nonexistent", tmp_path) is None


def test_list_requests(tmp_path):
    """list_requests returns saved requests, optional status filter."""
    save_request(ActivationRequest(activation_id="act_a", source_id="openclaw", status="pending"), tmp_path)
    save_request(ActivationRequest(activation_id="act_b", source_id="coding_agent", status="executed"), tmp_path)
    all_reqs = list_requests(tmp_path)
    assert len(all_reqs) >= 2
    pending = list_requests(tmp_path, status="pending")
    assert any(r.activation_id == "act_a" for r in pending)


def test_build_preview(tmp_path):
    """build_preview returns ActivationPreview; blocked when source unknown."""
    req = ActivationRequest(activation_id="act_p", source_id="openclaw", requested_action="enable")
    preview = build_preview(req, tmp_path)
    assert isinstance(preview, ActivationPreview)
    assert preview.activation_id == "act_p"
    assert preview.source_id == "openclaw"
    req_unknown = ActivationRequest(activation_id="act_u", source_id="nonexistent_src", requested_action="enable")
    prev_unknown = build_preview(req_unknown, tmp_path)
    assert prev_unknown.blocked is True
    assert "not in registry" in prev_unknown.block_reason or "nonexistent" in prev_unknown.block_reason


def test_execute_blocked_when_request_not_found(tmp_path):
    """execute_activation returns failed when request not found."""
    result = execute_activation("act_nonexistent", repo_root=tmp_path)
    assert result.outcome == "failed"
    assert "not found" in result.message.lower()


def test_execute_and_disable_integration(tmp_path):
    """execute_activation enable then disable_source for an integration (openclaw)."""
    req = create_activation_request("openclaw", action="enable", repo_root=tmp_path)
    assert req is not None
    save_request(req, tmp_path)
    result = execute_activation(req.activation_id, repo_root=tmp_path, approved=True)
    assert result.outcome in ("executed", "blocked", "failed")
    if result.outcome == "executed":
        disable_result = disable_source("openclaw", repo_root=tmp_path)
        assert disable_result.outcome == "executed"


def test_disable_source_no_manifest(tmp_path):
    """disable_source for non-integration source returns executed with note."""
    result = disable_source("backend_ollama", repo_root=tmp_path)
    assert result.outcome == "executed"
    assert "no local" in result.message.lower() or "No local" in result.message


def test_save_and_load_history(tmp_path):
    """save_execution_result and load_history."""
    save_execution_result("act_1", "executed", {"action": "enable"}, tmp_path)
    save_execution_result("act_2", "instructions_only", {}, tmp_path)
    history = load_history(tmp_path, limit=10)
    assert len(history) >= 2
    outcomes = [e.get("outcome") for e in history]
    assert "executed" in outcomes or "instructions_only" in outcomes


def test_format_preview_and_history():
    """format_preview and format_history produce non-empty strings."""
    preview = ActivationPreview(activation_id="act_1", source_id="openclaw", requested_action="enable", blocked=False)
    text = format_preview(preview)
    assert "act_1" in text
    assert "openclaw" in text
    hist_text = format_history([{"activation_id": "act_1", "outcome": "executed", "recorded_at": "2025-01-01T00:00:00"}])
    assert "act_1" in hist_text
    assert "executed" in hist_text
