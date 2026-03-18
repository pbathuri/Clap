"""
Tests for M31 observation runtime: source model, boundaries, normalized events, CLI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.observe.sources import (
    get_observation_source_registry,
    list_source_ids,
    ObservationSourceDef,
)
from workflow_dataset.observe.boundaries import (
    check_source_enabled,
    check_file_scope,
    get_source_health,
    get_boundary_state,
)
from workflow_dataset.observe.local_events import (
    ObservationEvent,
    EventSource,
    normalized_payload_extra,
    ACTIVITY_TYPE_KEY,
)
from workflow_dataset.observe.state import (
    load_observation_state,
    enable_source,
    disable_source,
    save_observation_state,
    effective_observation_config,
)


def test_source_registry_has_all_sources() -> None:
    registry = get_observation_source_registry()
    ids = list_source_ids()
    assert "file" in ids
    assert "app" in ids
    assert "teaching" in ids
    for sid in ids:
        assert sid in registry
        d = registry[sid]
        assert isinstance(d, ObservationSourceDef)
        assert d.source_id == sid
        assert d.consent_required is True
        assert d.display_name


def test_file_source_implemented_others_stub() -> None:
    registry = get_observation_source_registry()
    assert registry["file"].implemented is True
    for sid in ["app", "browser", "terminal", "calendar"]:
        assert registry[sid].implemented is False


def test_check_source_enabled() -> None:
    ok, reason = check_source_enabled("file", False, ["file"])
    assert ok is False
    assert reason == "observation_disabled"

    ok, reason = check_source_enabled("file", True, [])
    assert ok is False
    assert reason == "source_not_allowed"

    ok, reason = check_source_enabled("file", True, ["file"])
    assert ok is True
    assert reason == "ok"


def test_check_file_scope() -> None:
    root = Path("/allowed/root")
    in_scope, reason = check_file_scope(root / "a/b.txt", [root], set())
    assert in_scope is True
    in_scope, _ = check_file_scope(Path("/other/path"), [root], set())
    assert in_scope is False
    in_scope, _ = check_file_scope(root / "node_modules/x", [root], {"node_modules"})
    assert in_scope is False


def test_get_source_health() -> None:
    health, detail = get_source_health("file", False, ["file"], scope_ok=True, collector_ok=True)
    assert health == "blocked_disabled"
    health, detail = get_source_health("file", True, [], scope_ok=True, collector_ok=True)
    assert health == "blocked_not_allowed"
    health, detail = get_source_health("file", True, ["file"], scope_ok=True, collector_ok=True)
    assert health == "ok"
    health, detail = get_source_health("app", True, ["app"], scope_ok=True, collector_ok=True)
    assert health == "stub"


def test_get_boundary_state() -> None:
    state = get_boundary_state(True, ["file"], file_root_paths=["/tmp"])
    assert state["observation_enabled"] is True
    assert "file" in state["enabled_sources"]
    assert state["file_root_paths_configured"] is True
    state2 = get_boundary_state(False, [], file_root_paths=None)
    assert state2["enabled_sources"] == []
    assert state2["file_root_paths_configured"] is False


def test_normalized_payload_extra() -> None:
    extra = normalized_payload_extra("file_snapshot", project_hint="proj1", provenance="scan")
    assert extra[ACTIVITY_TYPE_KEY] == "file_snapshot"
    assert extra["project_hint"] == "proj1"
    assert extra["provenance"] == "scan"
    assert "session_hint" not in extra
    assert "redaction_marker" not in extra


def test_observation_event_normalized_view() -> None:
    evt = ObservationEvent(
        event_id="evt_abc",
        source=EventSource.FILE,
        timestamp_utc="2025-01-01T12:00:00Z",
        payload={"path": "/x", "activity_type": "file_snapshot", "provenance": "scan"},
    )
    v = evt.normalized_view()
    assert v["event_id"] == "evt_abc"
    assert v["source"] == "file"
    assert v["activity_type"] == "file_snapshot"
    assert v["provenance"] == "scan"


def test_state_enable_disable(tmp_path: Path) -> None:
    state_dir = tmp_path / "data" / "local"
    assert load_observation_state(state_dir) == {}
    enable_source("file", state_dir=state_dir)
    state = load_observation_state(state_dir)
    assert state["enabled_sources"] == ["file"]
    assert state["observation_enabled"] is True
    enable_source("app", state_dir=state_dir)
    assert load_observation_state(state_dir)["enabled_sources"] == ["file", "app"]
    disable_source("app", state_dir=state_dir)
    assert load_observation_state(state_dir)["enabled_sources"] == ["file"]


def test_effective_observation_config_uses_state_file(tmp_path: Path) -> None:
    state_dir = tmp_path / "local"
    save_observation_state(["file", "app"], observation_enabled=True, state_dir=state_dir)
    enabled, sources = effective_observation_config(False, [], state_dir=state_dir)
    assert enabled is True
    assert sources == ["file", "app"]


def test_effective_observation_config_fallback_to_config(tmp_path: Path) -> None:
    enabled, sources = effective_observation_config(True, ["file"], state_dir=tmp_path / "nonexistent")
    assert enabled is True
    assert sources == ["file"]


def test_blocked_source_behavior() -> None:
    state = get_boundary_state(True, ["terminal"], file_root_paths=None)
    assert "terminal" in state["stub_sources"]
    blocked = [b for b in state["blocked_sources"] if b.get("source") == "file"]
    assert len(blocked) == 1
    assert blocked[0]["reason"] == "blocked_not_allowed"
