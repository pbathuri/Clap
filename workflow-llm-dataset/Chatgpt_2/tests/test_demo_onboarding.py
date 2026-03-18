"""
M51E–M51H: Demo onboarding — session, role preset, bounded memory bootstrap, ready-state.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.demo_onboarding.models import DemoOnboardingSession
from workflow_dataset.demo_onboarding.presets import (
    get_role_preset,
    list_role_preset_ids,
    get_default_role_preset,
)
from workflow_dataset.demo_onboarding.store import save_session, load_session
from workflow_dataset.demo_onboarding.flow import (
    demo_onboarding_start,
    demo_onboarding_select_role,
    demo_onboarding_bootstrap_memory,
    build_completion_state,
    build_ready_to_assist_state,
    build_demo_sequence,
)
from workflow_dataset.demo_onboarding.memory_bootstrap import run_bounded_memory_bootstrap


def test_demo_session_roundtrip(tmp_path: Path):
    s = DemoOnboardingSession(session_id="abc", started_at_utc="2025-01-01T00:00:00Z", role_preset_id="founder_operator_demo")
    save_session(s, tmp_path)
    loaded = load_session(tmp_path)
    assert loaded is not None
    assert loaded.session_id == "abc"
    assert loaded.role_preset_id == "founder_operator_demo"


def test_role_presets():
    assert "founder_operator_demo" in list_role_preset_ids()
    p = get_role_preset("founder_operator_demo")
    assert p is not None
    assert p.day_preset_id == "founder_operator"
    assert p.vertical_pack_id == "founder_operator_core"
    assert p.trust_posture and p.trust_posture.simulate_first
    d = get_default_role_preset()
    assert d.preset_id == "founder_operator_demo"


def test_demo_onboarding_start_and_role(tmp_path: Path):
    s1 = demo_onboarding_start(tmp_path, reset=True)
    assert s1.session_id
    s2, err = demo_onboarding_select_role("document_review_demo", tmp_path)
    assert not err
    assert s2 and s2.role_preset_id == "document_review_demo"


def test_bounded_memory_bootstrap_sample_files(tmp_path: Path):
    ws = tmp_path / "demo_ws"
    (ws / "proj_a").mkdir(parents=True)
    (ws / "proj_a" / "note.md").write_text("Priority: ship MVP. Todo: weekly status. Meeting with team.", encoding="utf-8")
    (ws / "proj_a" / "extra.txt").write_text("deadline friday report", encoding="utf-8")
    summary = run_bounded_memory_bootstrap(ws, repo_root=tmp_path, session_id="t1")
    assert summary["files_scanned"] >= 2
    assert "proj_a" in summary.get("project_hints", []) or any("proj" in h for h in summary.get("project_hints", []))
    assert summary.get("confidence", {}).get("level") in ("medium", "low", "high")


def test_bootstrap_empty_workspace(tmp_path: Path):
    ws = tmp_path / "empty"
    ws.mkdir()
    summary = run_bounded_memory_bootstrap(ws, repo_root=tmp_path)
    assert summary["files_scanned"] == 0
    assert summary["confidence"]["level"] == "insufficient"


def test_ready_state_incomplete(tmp_path: Path):
    demo_onboarding_start(tmp_path, reset=True)
    comp = build_completion_state(tmp_path)
    assert not comp.ready_for_assist
    assert comp.missing_steps
    state = build_ready_to_assist_state(tmp_path)
    assert not state.ready


def test_ready_state_complete(tmp_path: Path):
    demo_onboarding_start(tmp_path, reset=True)
    demo_onboarding_select_role("founder_operator_demo", tmp_path)
    ws = tmp_path / "w"
    ws.mkdir()
    (ws / "a.md").write_text("priority: demo success", encoding="utf-8")
    demo_onboarding_bootstrap_memory(str(ws), tmp_path)
    state = build_ready_to_assist_state(tmp_path)
    assert state.ready
    assert "Founder" in state.chosen_role_label or "founder" in state.chosen_role_label.lower()
    assert state.recommended_first_value_action
    assert state.bootstrap_confidence


def test_demo_sequence():
    seq = build_demo_sequence()
    assert "steps" in seq
    assert len(seq["steps"]) >= 4
    assert "founder_operator_demo" in seq.get("default_role", "")
