"""
M39I–M39L: Tests for vertical launch kits, success proof, operator playbooks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.vertical_launch.models import (
    VerticalLaunchKit,
    RequiredSetupChecklist,
    SuccessProofMetric,
    OperatorSupportPlaybook,
)
from workflow_dataset.vertical_launch.store import (
    get_active_launch,
    set_active_launch,
    clear_active_launch,
    get_proof_state,
    set_proof_state,
    record_proof_met,
)
from workflow_dataset.vertical_launch.success_proof import (
    build_success_proof_report,
    get_proof_metrics_for_kit,
    PROOF_FIRST_RUN_COMPLETED,
)
from workflow_dataset.vertical_launch.kits import (
    build_launch_kit_for_vertical,
    list_launch_kits,
)


def test_list_launch_kits():
    """List launch kits returns at least one (from playbooks)."""
    kits = list_launch_kits()
    assert isinstance(kits, list)
    assert len(kits) >= 1
    for k in kits:
        assert k.launch_kit_id.endswith("_launch")
        assert k.curated_pack_id
        assert k.operator_playbook.playbook_id


def test_build_launch_kit_for_vertical():
    """Build launch kit for founder_operator_core has path, setup, proofs, playbook."""
    kit = build_launch_kit_for_vertical("founder_operator_core")
    assert kit.launch_kit_id == "founder_operator_core_launch"
    assert kit.curated_pack_id == "founder_operator_core"
    assert kit.first_run_path.entry_point
    assert len(kit.required_setup.items) >= 1
    assert len(kit.success_proof_metrics) >= 1
    assert kit.operator_playbook.setup_guidance
    assert kit.supported_unsupported.supported_surface_ids or kit.supported_unsupported.out_of_scope_hint


def test_set_get_active_launch(tmp_path):
    """Set and get active launch kit."""
    clear_active_launch(tmp_path)
    assert get_active_launch(tmp_path) == {}
    set_active_launch("founder_operator_core_launch", "founder_operator_core", repo_root=tmp_path)
    active = get_active_launch(tmp_path)
    assert active.get("active_launch_kit_id") == "founder_operator_core_launch"
    assert active.get("launch_started_at_utc")
    clear_active_launch(tmp_path)
    assert get_active_launch(tmp_path) == {}


def test_proof_state_and_report(tmp_path):
    """Proof state and success-proof report: met/pending counts."""
    set_proof_state("founder_operator_core_launch", [
        {"proof_id": PROOF_FIRST_RUN_COMPLETED, "status": "met", "reached_at_utc": "2025-01-01T00:00:00Z"},
    ], repo_root=tmp_path)
    report = build_success_proof_report("founder_operator_core_launch", repo_root=tmp_path)
    assert report["launch_kit_id"] == "founder_operator_core_launch"
    assert report["met_count"] >= 1
    assert report["pending_count"] >= 0
    met_ids = [p["proof_id"] for p in report["proofs"] if p.get("status") == "met"]
    assert PROOF_FIRST_RUN_COMPLETED in met_ids


def test_record_proof_met(tmp_path):
    """Record a proof as met updates proof state."""
    set_active_launch("founder_operator_core_launch", "founder_operator_core", repo_root=tmp_path)
    set_proof_state("founder_operator_core_launch", [], repo_root=tmp_path)
    record_proof_met(PROOF_FIRST_RUN_COMPLETED, "founder_operator_core_launch", repo_root=tmp_path)
    state = get_proof_state(tmp_path)
    proofs = state.get("proofs", [])
    assert any(p.get("proof_id") == PROOF_FIRST_RUN_COMPLETED and p.get("status") == "met" for p in proofs)


def test_operator_playbook_in_kit():
    """Launch kit includes operator playbook with setup, recovery, escalation hints."""
    kit = build_launch_kit_for_vertical("founder_operator_core")
    op = kit.operator_playbook
    assert op.setup_guidance
    assert op.first_value_coaching
    assert op.common_recovery_guidance
    assert op.when_to_narrow_scope
    assert op.when_to_escalate_downgrade_cohort
    assert op.trust_operator_review_hint
    assert isinstance(op.commands, list)


def test_supported_unsupported_boundaries():
    """Launch kit has supported/unsupported boundaries."""
    kit = build_launch_kit_for_vertical("founder_operator_core")
    b = kit.supported_unsupported
    assert isinstance(b.supported_surface_ids, list)
    assert isinstance(b.supported_workflow_ids, list) or b.out_of_scope_hint


# ----- M39L.1 Value dashboards + rollout review -----


def test_build_value_dashboard(tmp_path):
    """Value dashboard has proof summary, working/not_working, operator_summary."""
    from workflow_dataset.vertical_launch.dashboard import build_value_dashboard
    dash = build_value_dashboard("founder_operator_core", repo_root=tmp_path)
    assert dash.get("launch_kit_id") == "founder_operator_core_launch"
    assert "proof_summary" in dash
    assert "what_is_working" in dash
    assert "what_is_not_working" in dash
    assert "operator_summary" in dash
    assert dash["proof_summary"]["met_count"] >= 0
    assert isinstance(dash["what_is_working"], list)
    assert isinstance(dash["what_is_not_working"], list)


def test_build_rollout_review_pack(tmp_path):
    """Rollout review pack has recommended decision, evidence, working/not."""
    from workflow_dataset.vertical_launch.rollout_review import build_rollout_review_pack
    from workflow_dataset.vertical_launch.models import ROLLOUT_CONTINUE, ROLLOUT_NARROW, ROLLOUT_PAUSE, ROLLOUT_EXPAND
    pack = build_rollout_review_pack("founder_operator_core", repo_root=tmp_path)
    assert pack.launch_kit_id == "founder_operator_core_launch"
    assert pack.recommended_decision in (ROLLOUT_CONTINUE, ROLLOUT_NARROW, ROLLOUT_PAUSE, ROLLOUT_EXPAND)
    assert pack.recommended_rationale
    assert pack.evidence_summary
    assert isinstance(pack.what_is_working, list)
    assert isinstance(pack.what_is_not_working, list)
    assert pack.operator_summary


def test_rollout_decision_record_and_list(tmp_path):
    """Record rollout decision and list by launch_kit_id."""
    from workflow_dataset.vertical_launch.store import save_rollout_decision, list_rollout_decisions
    save_rollout_decision("founder_operator_core", "founder_operator_core_launch", "continue", rationale="On track", repo_root=tmp_path)
    decisions = list_rollout_decisions(launch_kit_id="founder_operator_core_launch", repo_root=tmp_path)
    assert len(decisions) >= 1
    assert decisions[0].get("decision") == "continue"
    assert "founder_operator_core" in decisions[0].get("vertical_id", "")
