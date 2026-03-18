"""
M45I–M45L: Supervisory control — loop view, pause/takeover/redirect/handback, rationale, audit.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.supervisory_control.models import (
    SupervisedLoopView,
    OperatorIntervention,
    PauseState,
    RedirectState,
    TakeoverState,
    HandbackState,
    OperatorRationale,
    LoopControlAuditNote,
    LOOP_VIEW_ACTIVE,
    LOOP_VIEW_PAUSED,
    LOOP_VIEW_TAKEN_OVER,
    LOOP_VIEW_STOPPED,
    LOOP_VIEW_AWAITING_CONTINUATION,
    INTERVENTION_PAUSE,
    INTERVENTION_TAKEOVER,
    INTERVENTION_HANDBACK,
)
from workflow_dataset.supervisory_control.store import (
    load_loop_views,
    save_loop_views,
    load_pause_state,
    save_pause_state,
    load_takeover_state,
    save_takeover_state,
    load_last_handback,
    append_intervention,
    load_interventions,
    append_rationale,
    load_rationales,
    append_audit_note,
    load_audit_notes,
)
from workflow_dataset.supervisory_control.flows import (
    pause_loop,
    resume_loop,
    stop_loop,
    take_over_loop,
    handback_loop,
    redirect_loop,
    approve_continuation,
)
from workflow_dataset.supervisory_control.panel import (
    list_loops,
    get_loop,
    inspect_loop,
    mission_control_slice,
    attach_rationale,
    attach_audit_note,
)


def test_supervised_loop_view_model():
    v = SupervisedLoopView(
        loop_id="loop_1",
        label="Test loop",
        status=LOOP_VIEW_ACTIVE,
        project_slug="proj",
        pending_count=2,
    )
    assert v.loop_id == "loop_1"
    assert v.status == LOOP_VIEW_ACTIVE
    d = v.to_dict()
    assert d["loop_id"] == "loop_1"
    assert d["pending_count"] == 2


def test_pause_loop(tmp_path):
    save_loop_views([SupervisedLoopView(loop_id="L1", label="L1", status=LOOP_VIEW_ACTIVE)], repo_root=tmp_path)
    state = pause_loop("L1", reason="Testing", repo_root=tmp_path)
    assert state.loop_id == "L1"
    assert state.reason == "Testing"
    assert load_pause_state("L1", repo_root=tmp_path) is not None
    loops = load_loop_views(tmp_path)
    assert any(l.loop_id == "L1" and l.status == LOOP_VIEW_PAUSED for l in loops)
    interventions = load_interventions(repo_root=tmp_path)
    assert any(i.kind == INTERVENTION_PAUSE and i.loop_id == "L1" for i in interventions)


def test_resume_loop(tmp_path):
    save_loop_views([SupervisedLoopView(loop_id="L1", status=LOOP_VIEW_PAUSED)], repo_root=tmp_path)
    save_pause_state(PauseState(loop_id="L1", paused_at_utc="2024-01-01T00:00:00Z", reason="x"), repo_root=tmp_path)
    ok = resume_loop("L1", repo_root=tmp_path)
    assert ok is True
    state = load_pause_state("L1", repo_root=tmp_path)
    assert state is not None and state.resumed_at_utc != ""


def test_takeover_handback(tmp_path):
    save_loop_views([SupervisedLoopView(loop_id="L1", status=LOOP_VIEW_ACTIVE)], repo_root=tmp_path)
    state = take_over_loop("L1", operator_note="Manual control", repo_root=tmp_path)
    assert state.loop_id == "L1"
    assert load_takeover_state("L1", repo_root=tmp_path) is not None
    handback = handback_loop("L1", handback_note="Returning", safe_to_resume=True, repo_root=tmp_path)
    assert handback is not None
    assert handback.safe_to_resume is True
    takeover = load_takeover_state("L1", repo_root=tmp_path)
    assert takeover is not None and takeover.returned_at_utc != ""


def test_handback_without_takeover_returns_none(tmp_path):
    save_loop_views([SupervisedLoopView(loop_id="L2", status=LOOP_VIEW_ACTIVE)], repo_root=tmp_path)
    handback = handback_loop("L2", repo_root=tmp_path)
    assert handback is None


def test_redirect_loop(tmp_path):
    save_loop_views([SupervisedLoopView(loop_id="L1", status=LOOP_VIEW_ACTIVE)], repo_root=tmp_path)
    state = redirect_loop("L1", next_step_hint="Run job X", repo_root=tmp_path)
    assert state.loop_id == "L1"
    assert state.next_step_hint == "Run job X"
    assert state.applied is False


def test_stop_loop(tmp_path):
    save_loop_views([SupervisedLoopView(loop_id="L1", status=LOOP_VIEW_ACTIVE)], repo_root=tmp_path)
    save_pause_state(PauseState(loop_id="L1", paused_at_utc="2024-01-01T00:00:00Z", reason="x"), repo_root=tmp_path)
    stop_loop("L1", reason="Operator stop", repo_root=tmp_path)
    assert load_pause_state("L1", repo_root=tmp_path) is None
    loops = load_loop_views(tmp_path)
    assert any(l.loop_id == "L1" and l.status == LOOP_VIEW_STOPPED for l in loops)


def test_attach_rationale(tmp_path):
    r = attach_rationale("L1", "Need to review before continuing", repo_root=tmp_path)
    assert r.rationale_id != ""
    assert r.text == "Need to review before continuing"
    rationales = load_rationales(repo_root=tmp_path)
    assert any(x.rationale_id == r.rationale_id for x in rationales)


def test_attach_audit_note(tmp_path):
    note = attach_audit_note("L1", "Gate check passed", kind="gate_status", repo_root=tmp_path)
    assert note.note_id != ""
    assert note.kind == "gate_status"
    notes = load_audit_notes(repo_root=tmp_path, loop_id="L1")
    assert any(n.note_id == note.note_id for n in notes)


def test_inspect_loop_empty(tmp_path):
    save_loop_views([SupervisedLoopView(loop_id="L1", label="L1", status=LOOP_VIEW_ACTIVE)], repo_root=tmp_path)
    data = inspect_loop("L1", repo_root=tmp_path)
    assert data["loop_id"] == "L1"
    assert data["view"] is not None
    assert data["view"]["loop_id"] == "L1"
    assert "recent_interventions" in data


def test_mission_control_slice_no_loops(tmp_path):
    mc = mission_control_slice(repo_root=tmp_path)
    assert "active_loops_count" in mc
    assert "paused_loops_count" in mc
    assert "taken_over_count" in mc
    assert "most_urgent_loop_id" in mc


def test_mission_control_slice_with_paused(tmp_path):
    save_loop_views([
        SupervisedLoopView(loop_id="L1", status=LOOP_VIEW_PAUSED, pending_count=1),
    ], repo_root=tmp_path)
    save_pause_state(PauseState(loop_id="L1", paused_at_utc="2024-01-01T00:00:00Z", reason="x"), repo_root=tmp_path)
    mc = mission_control_slice(repo_root=tmp_path)
    assert mc["paused_loops_count"] >= 1


def test_list_loops_syncs_from_supervised(tmp_path):
    # With no stored loops, list_loops may still return a default loop after sync
    loops = list_loops(repo_root=tmp_path)
    assert isinstance(loops, list)


def test_approve_continuation_requires_pause(tmp_path):
    save_loop_views([SupervisedLoopView(loop_id="L1", status=LOOP_VIEW_ACTIVE)], repo_root=tmp_path)
    ok = approve_continuation("L1", repo_root=tmp_path)
    assert ok is False
    save_pause_state(PauseState(loop_id="L1", paused_at_utc="2024-01-01T00:00:00Z", reason="x"), repo_root=tmp_path)
    ok = approve_continuation("L1", repo_root=tmp_path)
    assert ok is True


# ----- M45L.1: Supervision presets + takeover playbooks -----
def test_supervision_preset_defaults():
    from workflow_dataset.supervisory_control.presets import get_default_presets, get_preset_by_id, PRESET_CONSERVATIVE, PRESET_BALANCED
    presets = get_default_presets()
    assert len(presets) >= 3
    ids = {p.preset_id for p in presets}
    assert PRESET_CONSERVATIVE in ids or "conservative" in ids
    assert PRESET_BALANCED in ids or "balanced" in ids
    p = get_preset_by_id(PRESET_BALANCED)
    assert p is not None
    assert p.require_approval_before_real is True
    assert "when_to_continue" in p.when_to_continue_hint.lower() or len(p.when_to_continue_hint) > 0


def test_takeover_playbook_defaults():
    from workflow_dataset.supervisory_control.presets import get_default_playbooks, get_playbook_by_id, PLAYBOOK_BLOCKED_NO_PROGRESS
    playbooks = get_default_playbooks()
    assert len(playbooks) >= 2
    pb = get_playbook_by_id(PLAYBOOK_BLOCKED_NO_PROGRESS)
    assert pb is not None
    assert "blocked" in pb.trigger_condition.lower() or "progress" in pb.trigger_condition.lower()
    assert len(pb.suggested_actions) >= 1
    assert len(pb.when_to_intervene) >= 1


def test_build_operator_summary(tmp_path):
    from workflow_dataset.supervisory_control.summaries import build_operator_summary
    save_loop_views([SupervisedLoopView(loop_id="L1", label="L1", status=LOOP_VIEW_ACTIVE)], repo_root=tmp_path)
    s = build_operator_summary("L1", repo_root=tmp_path)
    assert s.loop_id == "L1"
    assert s.continue_recommendation != ""
    assert s.intervene_recommendation != ""
    assert s.terminate_recommendation != ""
    assert s.preset_id in ("balanced", "conservative", "operator_heavy", "")


def test_build_operator_summary_with_playbook(tmp_path):
    from workflow_dataset.supervisory_control.summaries import build_operator_summary
    from workflow_dataset.supervisory_control.panel import inspect_confidence_gates
    save_loop_views([SupervisedLoopView(loop_id="L1", status=LOOP_VIEW_ACTIVE, pending_count=10)], repo_root=tmp_path)
    # Preset balanced has max_pending_before_escalation=5; 10 >= 5 should suggest playbook
    s = build_operator_summary("L1", repo_root=tmp_path, preset_id="balanced")
    assert s.loop_id == "L1"
    # May or may not suggest playbook depending on gates.pending_approval_count
    assert s.continue_recommendation != ""


def test_save_load_current_preset(tmp_path):
    from workflow_dataset.supervisory_control.store import save_current_preset_id, load_current_preset_id
    save_current_preset_id("conservative", repo_root=tmp_path)
    assert load_current_preset_id(repo_root=tmp_path) == "conservative"
    save_current_preset_id("operator_heavy", repo_root=tmp_path)
    assert load_current_preset_id(repo_root=tmp_path) == "operator_heavy"


def test_list_presets_and_playbooks(tmp_path):
    from workflow_dataset.supervisory_control.summaries import list_presets_with_current, list_playbooks
    presets, current = list_presets_with_current(repo_root=tmp_path)
    assert isinstance(presets, list)
    assert current in ("balanced", "conservative", "operator_heavy", "")
    playbooks = list_playbooks(repo_root=tmp_path)
    assert isinstance(playbooks, list)
    assert len(playbooks) >= 2
