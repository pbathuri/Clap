"""
M37I–M37L: Tests for state durability — startup health, resume target, partial state, stale handling, snapshot/reconcile.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from workflow_dataset.state_durability.models import (
    PersistenceBoundary,
    StartupReadiness,
    ResumeTarget,
    DurableStateSnapshot,
    RecoverablePartialState,
)
from workflow_dataset.state_durability.boundaries import (
    collect_all_boundaries,
    collect_stale_markers,
    collect_corrupt_notes,
)
from workflow_dataset.state_durability.startup_health import build_startup_readiness, build_recoverable_partial_state
from workflow_dataset.state_durability.resume_target import build_resume_target
from workflow_dataset.state_durability.maintenance import (
    build_durable_snapshot,
    build_stale_cleanup_report,
    build_reconcile_report,
    build_startup_readiness_summary,
)
from workflow_dataset.state_durability.store import save_snapshot, load_snapshot, get_state_durability_dir


def test_collect_boundaries_empty_repo(tmp_path: Path) -> None:
    """With empty repo, workday is missing; other boundaries may be missing."""
    boundaries = collect_all_boundaries(tmp_path)
    assert len(boundaries) >= 1
    workday = next((b for b in boundaries if b.subsystem_id == "workday"), None)
    assert workday is not None
    assert workday.status in ("ok", "missing")


def test_startup_readiness_returns_readiness(tmp_path: Path) -> None:
    """build_startup_readiness returns StartupReadiness with boundaries and summary."""
    r = build_startup_readiness(repo_root=tmp_path)
    assert isinstance(r, StartupReadiness)
    assert r.generated_at_utc
    assert isinstance(r.boundaries, list)
    assert isinstance(r.summary_lines, list)
    assert r.recommended_first_action


def test_resume_target_returns_target(tmp_path: Path) -> None:
    """build_resume_target returns ResumeTarget with label and command."""
    t = build_resume_target(repo_root=tmp_path)
    assert isinstance(t, ResumeTarget)
    assert t.label
    assert t.command
    assert t.quality in ("high", "medium", "low", "degraded", "")


def test_recoverable_partial_state(tmp_path: Path) -> None:
    """build_recoverable_partial_state returns RecoverablePartialState with ok/missing/corrupt lists."""
    p = build_recoverable_partial_state(repo_root=tmp_path)
    assert isinstance(p, RecoverablePartialState)
    assert isinstance(p.recommended_recovery_actions, list)


def test_stale_markers_empty_repo(tmp_path: Path) -> None:
    """With no state files, stale markers are empty."""
    markers = collect_stale_markers(tmp_path, stale_hours=24.0)
    assert isinstance(markers, list)


def test_corrupt_notes_empty_repo(tmp_path: Path) -> None:
    """With no corrupt files, corrupt_notes is empty."""
    notes = collect_corrupt_notes(tmp_path)
    assert isinstance(notes, list)


def test_durable_snapshot_build(tmp_path: Path) -> None:
    """build_durable_snapshot returns DurableStateSnapshot with readiness, resume_target, summary_lines."""
    snap = build_durable_snapshot(repo_root=tmp_path)
    assert isinstance(snap, DurableStateSnapshot)
    assert snap.snapshot_id.startswith("snap_")
    assert snap.readiness is not None
    assert snap.resume_target is not None
    assert isinstance(snap.summary_lines, list)


def test_snapshot_save_load(tmp_path: Path) -> None:
    """Save snapshot and load it back; resume_target is restored."""
    snap = build_durable_snapshot(repo_root=tmp_path)
    path = save_snapshot(snap, repo_root=tmp_path)
    assert path.exists()
    loaded = load_snapshot(tmp_path)
    assert loaded is not None
    assert loaded.snapshot_id == snap.snapshot_id
    assert loaded.resume_target is not None
    assert loaded.resume_target.command


def test_reconcile_report(tmp_path: Path) -> None:
    """build_reconcile_report returns dict with recommended_actions and can_resume_degraded."""
    report = build_reconcile_report(repo_root=tmp_path)
    assert "can_resume_degraded" in report
    assert "recommended_actions" in report
    assert isinstance(report["recommended_actions"], list)


def test_stale_cleanup_report(tmp_path: Path) -> None:
    """build_stale_cleanup_report returns dict with stale_subsystems and recommendation."""
    report = build_stale_cleanup_report(repo_root=tmp_path, stale_hours=24.0)
    assert "stale_subsystems" in report
    assert "recommendation" in report


def test_startup_readiness_summary(tmp_path: Path) -> None:
    """build_startup_readiness_summary returns list of strings."""
    summary = build_startup_readiness_summary(repo_root=tmp_path)
    assert isinstance(summary, list)
    assert all(isinstance(s, str) for s in summary)


# ---------- M37L.1 Maintenance profiles + compaction ----------


def test_list_maintenance_profiles() -> None:
    """list_maintenance_profiles returns at least light, balanced, aggressive."""
    from workflow_dataset.state_durability import list_maintenance_profiles
    profiles = list_maintenance_profiles()
    ids = [p.profile_id for p in profiles]
    assert "light" in ids
    assert "balanced" in ids
    assert "aggressive" in ids
    for p in profiles:
        assert p.label
        assert len(p.policies) >= 1


def test_get_maintenance_profile_balanced() -> None:
    """get_maintenance_profile('balanced') returns profile with policies."""
    from workflow_dataset.state_durability import get_maintenance_profile
    p = get_maintenance_profile("balanced")
    assert p.profile_id == "balanced"
    assert p.label
    assert any(pol.subsystem_id == "background_run" for pol in p.policies)


def test_build_compaction_recommendations_empty(tmp_path: Path) -> None:
    """build_compaction_recommendations with empty repo returns output with profile and empty or minimal recommendations."""
    from workflow_dataset.state_durability import build_compaction_recommendations
    out = build_compaction_recommendations(repo_root=tmp_path, profile_id="balanced")
    assert out.profile_id == "balanced"
    assert out.profile_label
    assert out.generated_at_utc
    assert isinstance(out.recommendations, list)
    assert isinstance(out.operator_summary_lines, list)
    assert len(out.operator_summary_lines) >= 1


def test_build_compaction_recommendations_with_profile_flag(tmp_path: Path) -> None:
    """build_compaction_recommendations respects profile_id (light/aggressive)."""
    from workflow_dataset.state_durability import build_compaction_recommendations
    out_light = build_compaction_recommendations(repo_root=tmp_path, profile_id="light")
    out_agg = build_compaction_recommendations(repo_root=tmp_path, profile_id="aggressive")
    assert out_light.profile_id == "light"
    assert out_agg.profile_id == "aggressive"
