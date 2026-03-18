"""
M35E–M35H operator mode; M35H.1 bundles, pause, revocation, work-impact explanation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.operator_mode.models import (
    DelegatedResponsibility,
    ResponsibilityKind,
    ResponsibilityBundle,
    PauseState,
    PauseKind,
    RevocationRecord,
    WorkImpactExplanation,
    PauseRevocationReport,
    SuspensionRevocationState,
)
from workflow_dataset.operator_mode.store import (
    save_responsibility,
    save_bundle,
    load_pause_state,
    save_pause_state,
    load_suspension_revocation_state,
    save_suspension_revocation_state,
    load_revocation_history,
    append_revocation_record,
    get_bundle,
    get_responsibility,
    list_bundle_ids,
    list_responsibility_ids,
)
from workflow_dataset.operator_mode.bundles import (
    create_bundle,
    add_responsibility_to_bundle,
    resolve_bundle_responsibility_ids,
)
from workflow_dataset.operator_mode.pause_revocation import (
    set_emergency_pause,
    set_safe_pause,
    clear_pause,
    revoke_responsibility,
    revoke_bundle,
    build_pause_revocation_report,
)
from workflow_dataset.operator_mode.explain import explain_work_impact


def test_delegated_responsibility_model():
    r = DelegatedResponsibility(
        responsibility_id="r1",
        kind=ResponsibilityKind.MORNING_CONTINUITY,
        label="Morning digest",
        authority_tier_id="founder",
        review_gates=["before_real"],
    )
    assert r.responsibility_id == "r1"
    assert r.kind == ResponsibilityKind.MORNING_CONTINUITY
    assert "before_real" in r.review_gates


def test_responsibility_bundle_model():
    b = ResponsibilityBundle(
        bundle_id="b1",
        label="Morning ops",
        responsibility_ids=["r1", "r2"],
    )
    assert b.bundle_id == "b1"
    assert len(b.responsibility_ids) == 2


def test_pause_state_model():
    p = PauseState(kind=PauseKind.EMERGENCY, reason="Incident")
    assert p.kind == PauseKind.EMERGENCY
    assert p.reason == "Incident"


def test_save_and_load_bundle(tmp_path):
    b = ResponsibilityBundle(bundle_id="test_bundle", label="Test", responsibility_ids=[])
    save_bundle(b, repo_root=tmp_path)
    assert "test_bundle" in list_bundle_ids(repo_root=tmp_path)
    loaded = get_bundle("test_bundle", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.label == "Test"


def test_create_bundle_and_add_responsibility(tmp_path):
    save_responsibility(
        DelegatedResponsibility(responsibility_id="resp_a", label="A"),
        repo_root=tmp_path,
    )
    b = create_bundle("b2", "Bundle 2", responsibility_ids=[], repo_root=tmp_path)
    assert b.bundle_id == "b2"
    b2 = add_responsibility_to_bundle("b2", "resp_a", repo_root=tmp_path)
    assert b2 is not None
    assert "resp_a" in b2.responsibility_ids


def test_resolve_bundle_responsibility_ids(tmp_path):
    save_responsibility(DelegatedResponsibility(responsibility_id="x", label="X"), repo_root=tmp_path)
    b = create_bundle("b3", "B3", responsibility_ids=["x", "nonexistent"], repo_root=tmp_path)
    resolved = resolve_bundle_responsibility_ids("b3", repo_root=tmp_path)
    assert "x" in resolved
    assert "nonexistent" not in resolved


def test_emergency_pause(tmp_path):
    set_emergency_pause(reason="Test emergency", repo_root=tmp_path)
    p = load_pause_state(repo_root=tmp_path)
    assert p.kind == PauseKind.EMERGENCY
    assert "emergency" in p.reason.lower() or "Test" in p.reason
    clear_pause(repo_root=tmp_path)
    p2 = load_pause_state(repo_root=tmp_path)
    assert p2.kind == PauseKind.NONE


def test_safe_pause(tmp_path):
    set_safe_pause(reason="Safe", safe_continue_responsibility_ids=["r1"], repo_root=tmp_path)
    p = load_pause_state(repo_root=tmp_path)
    assert p.kind == PauseKind.SAFE
    assert "r1" in p.safe_continue_responsibility_ids


def test_revoke_responsibility(tmp_path):
    save_responsibility(DelegatedResponsibility(responsibility_id="rev_r", label="R"), repo_root=tmp_path)
    rec = revoke_responsibility("rev_r", reason="Test revoke", repo_root=tmp_path)
    assert rec.responsibility_id == "rev_r"
    assert rec.revoked_responsibility_ids == ["rev_r"]
    state = load_suspension_revocation_state(repo_root=tmp_path)
    assert "rev_r" in state.revoked_ids
    history = load_revocation_history(repo_root=tmp_path)
    assert any(r.responsibility_id == "rev_r" for r in history)


def test_revoke_bundle(tmp_path):
    save_responsibility(DelegatedResponsibility(responsibility_id="br1", label="BR1"), repo_root=tmp_path)
    save_responsibility(DelegatedResponsibility(responsibility_id="br2", label="BR2"), repo_root=tmp_path)
    create_bundle("b_rev", "To revoke", responsibility_ids=["br1", "br2"], repo_root=tmp_path)
    rec = revoke_bundle("b_rev", reason="Retire bundle", repo_root=tmp_path)
    assert rec is not None
    assert set(rec.revoked_responsibility_ids) == {"br1", "br2"}
    state = load_suspension_revocation_state(repo_root=tmp_path)
    assert "br1" in state.revoked_ids
    assert "br2" in state.revoked_ids


def test_explain_work_impact_no_pause(tmp_path):
    save_responsibility(DelegatedResponsibility(responsibility_id="e1", label="E1"), repo_root=tmp_path)
    impact = explain_work_impact(repo_root=tmp_path)
    assert impact.revoked_count >= 0
    assert "continue" in impact.summary.lower() or "no impact" in impact.summary.lower() or "0" in impact.summary


def test_explain_work_impact_with_emergency_pause(tmp_path):
    save_responsibility(DelegatedResponsibility(responsibility_id="p1", label="P1"), repo_root=tmp_path)
    set_emergency_pause(reason="Test", repo_root=tmp_path)
    impact = explain_work_impact(repo_root=tmp_path)
    assert impact.pause_active is True
    assert impact.pause_kind == "emergency"
    assert "P1" in impact.what_stops
    clear_pause(repo_root=tmp_path)


def test_build_pause_revocation_report(tmp_path):
    save_responsibility(DelegatedResponsibility(responsibility_id="rep1", label="Rep1"), repo_root=tmp_path)
    set_safe_pause(reason="Safe", safe_continue_responsibility_ids=["rep1"], repo_root=tmp_path)
    report = build_pause_revocation_report(repo_root=tmp_path)
    assert report.pause_state.kind == PauseKind.SAFE
    assert report.impact.pause_active is True
    assert "Rep1" in report.impact.what_continues
    clear_pause(repo_root=tmp_path)
