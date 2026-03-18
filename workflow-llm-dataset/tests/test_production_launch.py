"""
M40I–M40L: Production launch discipline — runbooks, gates, decision pack, blocker/warning handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.production_launch.models import (
    LaunchBlocker,
    LaunchDecision,
    LaunchGateResult,
    LaunchWarning,
    ProductionRunbook,
    OperatingChecklistItem,
)
from workflow_dataset.production_launch.runbooks import get_production_runbook
from workflow_dataset.production_launch.gates import (
    evaluate_production_gates,
    PRODUCTION_GATE_RELEASE_READINESS_NOT_BLOCKED,
    PRODUCTION_GATE_LABELS,
)
from workflow_dataset.production_launch.decision_pack import (
    build_launch_decision_pack,
    explain_launch_decision,
    write_launch_decision_pack_to_dir,
)


def test_runbook_creation_empty_vertical(tmp_path):
    """Runbook for empty vertical has static checklist and daily review."""
    runbook = get_production_runbook("", tmp_path)
    assert isinstance(runbook, ProductionRunbook)
    assert runbook.vertical_id == ""
    assert len(runbook.operating_checklist) >= 3
    assert len(runbook.daily_operating_review) >= 2
    assert len(runbook.recovery_paths) >= 2
    assert len(runbook.support_paths) >= 2
    assert len(runbook.trusted_routine_review_steps) >= 1
    assert any(c.id == "release_readiness" for c in runbook.operating_checklist)


def test_runbook_creation_with_vertical(tmp_path):
    """Runbook for founder_operator_core merges vertical playbook recovery paths."""
    runbook = get_production_runbook("founder_operator_core", tmp_path)
    assert runbook.vertical_id == "founder_operator_core"
    assert "founder" in runbook.label.lower() or "operator" in runbook.label.lower() or "Production" in runbook.label
    # Should have added vertical recovery paths
    path_ids = [r.path_id for r in runbook.recovery_paths]
    assert "recovery_guide" in path_ids or "vertical_stalled" in path_ids or "recover_after_install" in path_ids


def test_runbook_to_dict(tmp_path):
    """ProductionRunbook.to_dict is serializable."""
    runbook = get_production_runbook("", tmp_path)
    d = runbook.to_dict()
    assert d["vertical_id"] == ""
    assert "operating_checklist" in d
    assert "daily_operating_review" in d
    assert "recovery_paths" in d
    assert "support_paths" in d


def test_gate_evaluation_returns_list(tmp_path):
    """evaluate_production_gates returns list of LaunchGateResult."""
    results = evaluate_production_gates(tmp_path)
    assert isinstance(results, list)
    assert len(results) >= 6
    for r in results:
        assert isinstance(r, LaunchGateResult)
        assert r.gate_id in PRODUCTION_GATE_LABELS or r.gate_id
        assert r.label
        assert isinstance(r.passed, bool)
        assert isinstance(r.detail, str)


def test_gate_result_to_dict():
    """LaunchGateResult.to_dict is serializable."""
    r = LaunchGateResult(
        gate_id=PRODUCTION_GATE_RELEASE_READINESS_NOT_BLOCKED,
        label="Release readiness not blocked",
        passed=False,
        detail="release_readiness=blocked",
    )
    d = r.to_dict()
    assert d["gate_id"] == PRODUCTION_GATE_RELEASE_READINESS_NOT_BLOCKED
    assert d["passed"] is False
    assert "blocked" in d["detail"]


def test_launch_decision_pack_structure(tmp_path):
    """build_launch_decision_pack returns dict with required keys."""
    pack = build_launch_decision_pack(tmp_path)
    assert "chosen_vertical_summary" in pack
    assert "supported_scope" in pack
    assert "release_gate_results" in pack
    assert "open_blockers" in pack
    assert "open_warnings" in pack
    assert "recovery_posture" in pack
    assert "trust_posture" in pack
    assert "support_posture" in pack
    assert "recommended_decision" in pack
    assert "explain" in pack
    assert pack["recommended_decision"] in (
        LaunchDecision.LAUNCH.value,
        LaunchDecision.LAUNCH_NARROWLY.value,
        LaunchDecision.PAUSE.value,
        LaunchDecision.REPAIR_AND_REVIEW.value,
    )


def test_launch_decision_pack_blockers_affect_decision(tmp_path):
    """When blockers exist, recommended_decision is repair_and_review or pause."""
    pack = build_launch_decision_pack(tmp_path)
    if pack["open_blockers"]:
        assert pack["recommended_decision"] in (
            LaunchDecision.REPAIR_AND_REVIEW.value,
            LaunchDecision.PAUSE.value,
        )
        assert "Blockers" in pack["explain"] or "blocker" in pack["explain"].lower()


def test_launch_decision_explain_returns_string(tmp_path):
    """explain_launch_decision returns non-empty string."""
    text = explain_launch_decision(repo_root=tmp_path)
    assert isinstance(text, str)
    assert "Recommended decision" in text or "recommended" in text.lower()
    assert "Blockers" in text or "blocker" in text.lower() or "Warnings" in text


def test_launch_decision_explain_with_pack():
    """explain_launch_decision(pack=...) uses provided pack."""
    pack = {
        "recommended_decision": LaunchDecision.REPAIR_AND_REVIEW.value,
        "explain": "Two blockers must be resolved.",
        "open_blockers": [{"id": "b1", "summary": "Env failed"}],
        "open_warnings": [],
        "release_gate_results": [{"gate_id": "g1", "passed": False, "detail": "failed"}],
    }
    text = explain_launch_decision(pack=pack)
    assert LaunchDecision.REPAIR_AND_REVIEW.value in text
    assert "Two blockers" in text


def test_write_launch_decision_pack_to_dir(tmp_path):
    """write_launch_decision_pack_to_dir creates JSON file."""
    out_dir = tmp_path / "data/local/production_launch"
    path = write_launch_decision_pack_to_dir(tmp_path, output_dir=out_dir)
    assert path == out_dir / "launch_decision_pack.json"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "recommended_decision" in content
    assert "open_blockers" in content


def test_launch_blocker_and_warning_to_dict():
    """LaunchBlocker and LaunchWarning to_dict are serializable."""
    b = LaunchBlocker(id="b1", summary="Block", source="gates", remediation_hint="Fix gate", severity="blocker")
    w = LaunchWarning(id="w1", summary="Warn", source="readiness")
    assert b.to_dict()["id"] == "b1"
    assert b.to_dict()["severity"] == "blocker"
    assert w.to_dict()["id"] == "w1"


def test_incomplete_readiness_state_behavior(tmp_path):
    """With minimal repo (no vertical, no readiness), decision pack still returns valid structure; decision may be pause/repair."""
    pack = build_launch_decision_pack(tmp_path)
    assert pack["chosen_vertical_summary"] is not None
    assert isinstance(pack["release_gate_results"], list)
    # With empty/minimal tmp_path, release readiness often blocked -> repair_or_pause
    assert pack["recommended_decision"] in (
        LaunchDecision.LAUNCH.value,
        LaunchDecision.LAUNCH_NARROWLY.value,
        LaunchDecision.PAUSE.value,
        LaunchDecision.REPAIR_AND_REVIEW.value,
    )


# ----- M40L.1 Production review cycles + sustained-use checkpoints + post-deployment guidance -----


def test_post_deployment_guidance_structure(tmp_path):
    """build_post_deployment_guidance returns guidance, reason, recommended_actions, evidence."""
    from workflow_dataset.production_launch import build_post_deployment_guidance
    from workflow_dataset.production_launch.models import PostDeploymentGuidance
    g = build_post_deployment_guidance(tmp_path)
    assert "guidance" in g
    assert g["guidance"] in (e.value for e in PostDeploymentGuidance)
    assert "reason" in g
    assert "recommended_actions" in g
    assert isinstance(g["recommended_actions"], list)
    assert "evidence" in g


def test_production_review_cycle_build(tmp_path):
    """build_production_review_cycle returns cycle, launch_decision_summary, post_deployment_guidance."""
    from workflow_dataset.production_launch import build_production_review_cycle
    data = build_production_review_cycle(tmp_path)
    assert "cycle" in data
    cy = data["cycle"]
    assert "cycle_id" in cy and "at_iso" in cy and "guidance_snapshot" in cy
    assert "findings" in cy and "recommended_actions" in cy
    assert "launch_decision_summary" in data
    assert "post_deployment_guidance" in data


def test_record_review_cycle(tmp_path):
    """record_review_cycle appends to review_cycles.json and returns path."""
    from workflow_dataset.production_launch import record_review_cycle, list_review_cycles
    path = record_review_cycle(tmp_path)
    assert path == tmp_path / "data/local/production_launch/review_cycles.json"
    assert path.exists()
    cycles = list_review_cycles(tmp_path)
    assert len(cycles) >= 1
    assert "at_iso" in cycles[0] and "guidance_snapshot" in cycles[0]


def test_sustained_use_checkpoint_build(tmp_path):
    """build_sustained_use_checkpoint returns checkpoint, post_deployment_guidance, criteria_met."""
    from workflow_dataset.production_launch import build_sustained_use_checkpoint
    data = build_sustained_use_checkpoint(tmp_path, kind="auto")
    assert "checkpoint" in data
    cp = data["checkpoint"]
    assert "checkpoint_id" in cp and "kind" in cp and "criteria_met" in cp
    assert "sessions_or_days_context" in cp and "guidance" in cp
    assert "post_deployment_guidance" in data
    assert "criteria_met" in data


def test_record_sustained_use_checkpoint(tmp_path):
    """record_sustained_use_checkpoint writes to sustained_use_checkpoints.json."""
    from workflow_dataset.production_launch import record_sustained_use_checkpoint, list_sustained_use_checkpoints
    path = record_sustained_use_checkpoint(tmp_path, kind="session_5")
    assert path == tmp_path / "data/local/production_launch/sustained_use_checkpoints.json"
    assert path.exists()
    records = list_sustained_use_checkpoints(tmp_path)
    assert len(records) >= 1
    assert records[0].get("kind") in ("session_5", "auto", "session_10", "day_7")


def test_ongoing_production_summary(tmp_path):
    """build_ongoing_production_summary returns guidance, review cycle, checkpoint, key_metrics, one_liner."""
    from workflow_dataset.production_launch import build_ongoing_production_summary, format_ongoing_summary_report
    summary = build_ongoing_production_summary(tmp_path)
    assert "post_deployment_guidance" in summary
    assert "current_review_cycle" in summary
    assert "current_sustained_use_checkpoint" in summary
    assert "key_metrics" in summary
    assert "one_liner" in summary
    assert "Guidance=" in summary["one_liner"] or "Blockers=" in summary["one_liner"]
    text = format_ongoing_summary_report(summary)
    assert "Ongoing production summary" in text
    assert "Post-deployment guidance" in text
    assert "Sustained-use" in text
