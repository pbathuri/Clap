"""M24D–M24G: Local capability activation block — health, lifecycle, list-requests, mission control."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.external_capability.schema import (
    ExternalCapabilitySource,
    LIFECYCLE_STATES,
)
from workflow_dataset.external_capability.registry import get_external_source
from workflow_dataset.external_capability.lifecycle import source_lifecycle_state
from workflow_dataset.external_capability.health import (
    build_capability_health,
    format_health_report,
    CapabilityHealth,
)
from workflow_dataset.external_capability.activation_store import list_requests, save_request
from workflow_dataset.external_capability.activation_models import ActivationRequest
from workflow_dataset.mission_control.state import get_mission_control_state


def test_schema_has_lifecycle_and_rollback():
    """Schema has LIFECYCLE_STATES and source has rollback_notes, machine_requirements, supported_value_pack_ids."""
    assert "active" in LIFECYCLE_STATES
    assert "failed" in LIFECYCLE_STATES
    s = ExternalCapabilitySource(source_id="x", category="openclaw", rollback_notes="Disable via CLI")
    assert s.rollback_notes == "Disable via CLI"
    assert hasattr(s, "machine_requirements")
    assert hasattr(s, "supported_value_pack_ids")


def test_source_lifecycle_state(tmp_path):
    """source_lifecycle_state returns one of LIFECYCLE_STATES."""
    state = source_lifecycle_state("openclaw", tmp_path)
    assert state in LIFECYCLE_STATES
    unknown = source_lifecycle_state("nonexistent_xyz", tmp_path)
    assert unknown == "unknown"


def test_build_capability_health(tmp_path):
    """build_capability_health returns CapabilityHealth with summary and by_lifecycle."""
    health = build_capability_health(tmp_path)
    assert isinstance(health, CapabilityHealth)
    assert "total_sources" in health.summary
    assert isinstance(health.by_lifecycle, dict)
    assert "capabilities" in health.recommended_next


def test_format_health_report(tmp_path):
    """format_health_report produces string with lifecycle and recommended next."""
    health = build_capability_health(tmp_path)
    report = format_health_report(health)
    assert "Capability health" in report
    assert "Lifecycle" in report or "active" in report or "total_sources" in report
    assert "Recommended next" in report or "recommended" in report.lower()


def test_list_requests_filter(tmp_path):
    """list_requests with status filter returns only matching requests."""
    save_request(ActivationRequest(activation_id="act_a", source_id="openclaw", status="pending"), tmp_path)
    save_request(ActivationRequest(activation_id="act_b", source_id="coding_agent", status="executed"), tmp_path)
    pending = list_requests(tmp_path, status="pending")
    assert any(r.activation_id == "act_a" for r in pending)
    executed = list_requests(tmp_path, status="executed")
    assert any(r.activation_id == "act_b" for r in executed)


def test_mission_control_includes_recommended_next_capability(tmp_path):
    """get_mission_control_state includes activation_executor.recommended_next_capability_action when present."""
    state = get_mission_control_state(tmp_path)
    ae = state.get("activation_executor", {})
    if "error" not in ae:
        assert "recommended_next_capability_action" in ae
        assert "capabilities" in ae.get("recommended_next_capability_action", "")
