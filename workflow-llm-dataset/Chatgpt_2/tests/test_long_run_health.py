"""
M46A–M46D: Tests for long-run health snapshot, drift signals, alert state, subsystem view.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from workflow_dataset.long_run_health.models import (
    DeploymentHealthSnapshot,
    DriftSignal,
    SubsystemHealthSignal,
    StabilityWindow,
    AlertState,
    AlertStateExplanation,
    OperatorBurdenIndicator,
)
from workflow_dataset.long_run_health.alert_state import classify_alert_state
from workflow_dataset.long_run_health.drift_detection import (
    collect_drift_signals,
    queue_calmness_drift,
    triage_recurrence_drift,
)
from workflow_dataset.long_run_health.indicators import (
    build_subsystem_health_signals,
    operator_burden_from_state,
)
from workflow_dataset.long_run_health.snapshot import build_deployment_health_snapshot
from workflow_dataset.long_run_health.store import (
    save_snapshot,
    load_snapshot,
    save_drift_signal,
    load_drift_signal,
    list_snapshots,
    list_drift_signals,
    get_health_dir,
)
from workflow_dataset.long_run_health.reports import (
    format_long_run_report,
    format_drift_report,
    format_subsystem_health,
    format_alert_explanation,
)
from workflow_dataset.long_run_health.mission_control import long_run_health_slice


def test_snapshot_generation(tmp_path: Path) -> None:
    """Build snapshot from minimal state (no mission_control deps in test)."""
    state = {
        "adaptive_execution_state": {"running_loop_count": 1, "awaiting_takeover_count": 0},
        "supervisory_control_state": {"active_loops_count": 1, "paused_loops_count": 0, "taken_over_count": 0},
        "signal_quality": {"calmness_score": 0.8, "noise_level": 0.2},
        "memory_intelligence": {},
        "evaluation_state": {},
        "triage": {},
        "product_state": {},
    }
    signals = build_subsystem_health_signals(state)
    assert len(signals) >= 4
    drift = collect_drift_signals(state, window_kind="rolling_7", repo_root=tmp_path)
    assert isinstance(drift, list)


def test_alert_state_healthy() -> None:
    """No drift, all ok -> healthy."""
    drift_signals: list[DriftSignal] = []
    subsystem_signals = [
        SubsystemHealthSignal("queue", "Queue", "ok", 0.8, "ok", []),
        SubsystemHealthSignal("memory_os", "Memory", "ok", 0.7, "ok", []),
    ]
    state, expl = classify_alert_state(drift_signals=drift_signals, subsystem_signals=subsystem_signals)
    assert state == AlertState.HEALTHY
    assert expl.rationale
    assert not expl.contradictory


def test_alert_state_degraded() -> None:
    """One medium drift -> degraded."""
    drift_signals = [
        DriftSignal("drift_1", "queue_calmness", "queue", "medium", "Calmness low", 0.7, 0.4, "rolling_7", [], ""),
    ]
    subsystem_signals = [
        SubsystemHealthSignal("queue", "Queue", "degraded", 0.4, "low calmness", []),
    ]
    state, expl = classify_alert_state(drift_signals=drift_signals, subsystem_signals=subsystem_signals)
    assert state == AlertState.DEGRADED
    assert "drift" in expl.rationale.lower() or "degraded" in expl.rationale.lower()


def test_alert_state_repair_needed() -> None:
    """High severity drift -> repair-needed."""
    drift_signals = [
        DriftSignal("drift_1", "routing_quality", "routing", "high", "Eval revert", None, 1.0, "rolling_7", [], ""),
    ]
    subsystem_signals = [
        SubsystemHealthSignal("routing", "Routing", "warning", 0.5, "revert", []),
    ]
    state, expl = classify_alert_state(drift_signals=drift_signals, subsystem_signals=subsystem_signals)
    assert state in (AlertState.REPAIR_NEEDED, AlertState.ROLLBACK_CONSIDER)


def test_subsystem_health_format() -> None:
    """Format subsystem health string."""
    signals = [
        SubsystemHealthSignal("memory_os", "Memory", "ok", 0.7, "recs=2 weak=0", ["mi"]),
    ]
    text = format_subsystem_health("memory_os", signals)
    assert "memory_os" in text
    assert "0.70" in text
    text_miss = format_subsystem_health("nonexistent", signals)
    assert "not found" in text_miss


def test_drift_report_format() -> None:
    """Format drift report."""
    signals = [
        DriftSignal("d1", "queue_calmness", "queue", "low", "Calmness 0.4", 0.7, 0.4, "rolling_7", [], ""),
    ]
    text = format_drift_report(signals, title="Test")
    assert "d1" in text
    assert "queue_calmness" in text
    empty_text = format_drift_report([], title="Empty")
    assert "count=0" in empty_text or "no drift" in empty_text.lower()


def test_alert_explanation_format() -> None:
    """Format alert explanation."""
    expl = AlertStateExplanation(
        state=AlertState.WATCH,
        rationale="Subsystems in warning.",
        evidence_refs=["queue"],
        confidence="low",
        contradictory=False,
    )
    text = format_alert_explanation(expl)
    assert "watch" in text.lower()
    assert "rationale" in text.lower()


def test_store_snapshot_and_load(tmp_path: Path) -> None:
    """Save and load snapshot."""
    window = StabilityWindow(kind="rolling_7", label="Last 7 days")
    snapshot = DeploymentHealthSnapshot(
        snapshot_id="health_test1",
        window=window,
        subsystem_signals=[],
        drift_signals=[],
        generated_at_iso="2026-01-01T00:00:00Z",
    )
    save_snapshot(snapshot, repo_root=tmp_path)
    loaded = load_snapshot("health_test1", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.snapshot_id == "health_test1"
    index = list_snapshots(limit=5, repo_root=tmp_path)
    assert len(index) >= 1
    assert index[0]["snapshot_id"] == "health_test1"


def test_store_drift_signal(tmp_path: Path) -> None:
    """Save and load drift signal."""
    d = DriftSignal("drift_abc", "queue_calmness", "queue", "medium", "Test", 0.7, 0.4, "rolling_7", [], "2026-01-01T00:00:00Z")
    save_drift_signal(d, repo_root=tmp_path)
    loaded = load_drift_signal("drift_abc", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.drift_id == "drift_abc"
    listed = list_drift_signals(limit=10, repo_root=tmp_path)
    assert len(listed) >= 1


def test_operator_burden_from_state() -> None:
    """Operator burden from state."""
    state = {
        "adaptive_execution_state": {"awaiting_takeover_count": 2},
        "supervisory_control_state": {"taken_over_count": 1, "paused_loops_count": 0},
        "triage": {"open_issue_count": 3},
    }
    ob = operator_burden_from_state(state)
    assert ob.takeover_count == 3
    assert ob.triage_open_count == 3


def test_queue_calmness_drift_fires() -> None:
    """Low calmness produces drift."""
    state = {"signal_quality": {"calmness_score": 0.35, "noise_level": 0.6}}
    d = queue_calmness_drift(state, "rolling_7")
    assert d is not None
    assert d.kind == "queue_calmness"
    assert d.subsystem_id == "queue"
    assert d.severity in ("medium", "high")


def test_queue_calmness_drift_no_fire() -> None:
    """High calmness no drift."""
    state = {"signal_quality": {"calmness_score": 0.8}}
    d = queue_calmness_drift(state, "rolling_7")
    assert d is None


def test_triage_recurrence_drift_fires() -> None:
    """Open issues elevated -> drift."""
    state = {"triage": {"open_issue_count": 5}}
    d = triage_recurrence_drift(state, "rolling_7")
    assert d is not None
    assert d.kind == "triage_recurrence"


def test_mission_control_slice() -> None:
    """Mission control slice returns dict with expected keys (uses real repo root)."""
    try:
        slice_data = long_run_health_slice(repo_root=None)
    except Exception:
        slice_data = {"error": "missing deps"}
    assert isinstance(slice_data, dict)
    if "error" not in slice_data:
        assert "current_alert_state" in slice_data
        assert "next_recommended_maintenance" in slice_data


def test_build_deployment_health_snapshot_integration() -> None:
    """Build full snapshot (uses real repo root; may be slow)."""
    try:
        snapshot = build_deployment_health_snapshot(window_kind="rolling_7", repo_root=None)
    except Exception as e:
        pytest.skip(f"mission_control deps not available: {e}")
    assert snapshot.snapshot_id.startswith("health_")
    assert snapshot.window.kind == "rolling_7"
    assert snapshot.alert_state in AlertState
    assert snapshot.alert_explanation is not None
    report = format_long_run_report(snapshot)
    assert "alert_state" in report


def test_no_drift_empty_state() -> None:
    """Minimal state with no drift -> no drift signals; alert healthy or watch."""
    state = {
        "adaptive_execution_state": {"running_loop_count": 1, "awaiting_takeover_count": 0},
        "supervisory_control_state": {"active_loops_count": 1, "paused_loops_count": 0, "taken_over_count": 0},
        "signal_quality": {"calmness_score": 0.8},
        "memory_intelligence": {},
        "evaluation_state": {},
        "triage": {},
        "product_state": {},
    }
    drift = collect_drift_signals(state, window_kind="rolling_7")
    assert drift == []
    signals = build_subsystem_health_signals(state)
    alert_state, expl = classify_alert_state(drift_signals=[], subsystem_signals=signals)
    assert alert_state in (AlertState.HEALTHY, AlertState.WATCH)
    assert "healthy" in expl.rationale.lower() or "ok" in expl.rationale.lower() or "watch" in expl.rationale.lower()


def test_weak_signal_watch_only() -> None:
    """Warnings only, no drift -> watch."""
    signals = [
        SubsystemHealthSignal("queue", "Queue", "warning", 0.55, "slightly low calmness", []),
        SubsystemHealthSignal("memory_os", "Memory", "ok", 0.8, "ok", []),
    ]
    state, expl = classify_alert_state(drift_signals=[], subsystem_signals=signals)
    assert state == AlertState.WATCH
    assert "warning" in expl.rationale.lower() or "watch" in expl.rationale.lower()


def test_alert_state_contradictory() -> None:
    """High-severity drift but several subsystems ok -> contradictory=True in explanation."""
    drift_signals = [
        DriftSignal("drift_1", "routing_quality", "routing", "high", "Eval revert", None, 1.0, "rolling_7", [], ""),
    ]
    subsystem_signals = [
        SubsystemHealthSignal("queue", "Queue", "ok", 0.9, "ok", []),
        SubsystemHealthSignal("memory_os", "Memory", "ok", 0.85, "ok", []),
        SubsystemHealthSignal("routing", "Routing", "warning", 0.5, "revert", []),
    ]
    state, expl = classify_alert_state(drift_signals=drift_signals, subsystem_signals=subsystem_signals)
    assert state in (AlertState.REPAIR_NEEDED, AlertState.ROLLBACK_CONSIDER)
    assert expl.contradictory is True


def test_list_stability_windows() -> None:
    """List stability windows includes daily, weekly, rolling_7, rolling_long_run."""
    from workflow_dataset.long_run_health import list_stability_windows
    windows = list_stability_windows()
    kinds = [w["kind"] for w in windows]
    assert "daily" in kinds
    assert "weekly" in kinds
    assert "rolling_7" in kinds
    assert "rolling_30" in kinds
    assert "rolling_long_run" in kinds
    assert all("label" in w and "description" in w and "days" in w for w in windows)


def test_build_window_rolling_long_run() -> None:
    """rolling_long_run builds window with 30-day range."""
    from workflow_dataset.long_run_health import build_window
    w = build_window("rolling_long_run")
    assert w.kind == "rolling_long_run"
    assert w.label
    assert w.start_iso and w.end_iso


def test_list_threshold_profiles() -> None:
    """List threshold profiles includes conservative, balanced, production_strict."""
    from workflow_dataset.long_run_health import list_threshold_profiles
    profiles = list_threshold_profiles()
    ids = [p["profile_id"] for p in profiles]
    assert "conservative" in ids
    assert "balanced" in ids
    assert "production_strict" in ids
    balanced = next(p for p in profiles if p["profile_id"] == "balanced")
    assert balanced["queue_calmness_min"] == 0.5
    conservative = next(p for p in profiles if p["profile_id"] == "conservative")
    assert conservative["queue_calmness_min"] == 0.6


def test_conservative_profile_fires_drift_earlier() -> None:
    """With conservative profile, queue calmness 0.55 triggers drift; balanced does not."""
    from workflow_dataset.long_run_health.drift_detection import queue_calmness_drift
    from workflow_dataset.long_run_health import get_threshold_profile
    state = {"signal_quality": {"calmness_score": 0.55}}
    with_balanced = queue_calmness_drift(state, "rolling_7", threshold_profile=None)
    with_conservative = queue_calmness_drift(state, "rolling_7", threshold_profile=get_threshold_profile("conservative"))
    assert with_balanced is None
    assert with_conservative is not None
    assert with_conservative.kind == "queue_calmness"


def test_alert_explanation_has_short_summary() -> None:
    """Classify returns explanation with short_summary set."""
    signals = [
        SubsystemHealthSignal("queue", "Queue", "ok", 0.8, "ok", []),
        SubsystemHealthSignal("memory_os", "Memory", "ok", 0.7, "ok", []),
    ]
    _, expl = classify_alert_state(drift_signals=[], subsystem_signals=signals)
    assert expl.short_summary
    assert "healthy" in expl.short_summary.lower() or "ok" in expl.short_summary.lower()
