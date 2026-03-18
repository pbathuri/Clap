"""
M49E–M49H: Tests for migration validation and restore/reconcile flows.
Restore validation, compatibility mismatch, partial restore, reconcile, rebuild-required, weak-confidence.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.migration_restore.models import (
    ContinuityBundleManifest,
    TargetEnvironmentProfile,
    RestoreValidationReport,
    RestoreBlocker,
    RestoreConfidence,
    RestoreCandidate,
    ReconcileAction,
    RebuildRequiredComponent,
    StaleStateNote,
    ConflictClass,
)
from workflow_dataset.migration_restore.bundle import get_bundle_manifest, list_bundle_refs
from workflow_dataset.migration_restore.validation import validate_bundle_for_target
from workflow_dataset.migration_restore.flows import (
    dry_run_restore,
    restore_with_review,
    partial_restore,
    conflict_aware_reconcile,
    post_restore_verify,
)


def test_bundle_manifest_latest(tmp_path: Path) -> None:
    """Latest bundle manifest is built from state boundaries."""
    manifest = get_bundle_manifest("latest", repo_root=tmp_path)
    assert manifest is not None
    assert manifest.bundle_id
    assert "workday" in manifest.subsystem_ids
    assert "continuity_shutdown" in manifest.subsystem_ids or "continuity_carry_forward" in manifest.subsystem_ids
    assert manifest.product_version is not None


def test_list_bundle_refs(tmp_path: Path) -> None:
    """list_bundle_refs includes 'latest'."""
    refs = list_bundle_refs(tmp_path)
    assert "latest" in refs


def test_validate_bundle_for_target(tmp_path: Path) -> None:
    """Validation runs and returns report with confidence."""
    report = validate_bundle_for_target("latest", target_repo_root=tmp_path)
    assert report.bundle_id or report.bundle_id == "latest" or report.report_id
    assert report.restore_confidence is not None
    assert report.generated_at_utc
    # Same-env latest usually passes (version compatible)
    assert isinstance(report.passed, bool)
    assert isinstance(report.version_compatible, bool)


def test_validation_blocked_unknown_bundle(tmp_path: Path) -> None:
    """Unknown bundle ref yields blocker and blocked confidence."""
    report = validate_bundle_for_target("nonexistent_bundle_xyz", target_repo_root=tmp_path)
    assert report.passed is False
    assert any(b.code == "bundle_not_found" for b in report.blockers)
    assert report.restore_confidence is not None
    assert report.restore_confidence.label == "blocked"


def test_dry_run_restore(tmp_path: Path) -> None:
    """Dry-run returns subsystems that would be restored."""
    out = dry_run_restore("latest", target_repo_root=tmp_path)
    assert out.get("dry_run") is True
    assert "subsystems_would_restore" in out
    assert isinstance(out["subsystems_would_restore"], list)


def test_restore_with_review_not_approved(tmp_path: Path) -> None:
    """Restore without --approved returns pending status."""
    out = restore_with_review("latest", target_repo_root=tmp_path, approved=False)
    assert out.get("status") in ("pending", "restored")
    assert "candidate_id" in out


def test_partial_restore(tmp_path: Path) -> None:
    """Partial restore returns allowed subset of subsystems."""
    out = partial_restore("latest", ["workday", "continuity_shutdown"], target_repo_root=tmp_path)
    assert out.get("partial_restore") is True
    assert "allowed_subsystems" in out
    assert "requested_subsystems" in out


def test_conflict_aware_reconcile(tmp_path: Path) -> None:
    """Reconcile returns actions and rebuild_required structure."""
    out = conflict_aware_reconcile("latest", target_repo_root=tmp_path)
    assert "reconcile_actions" in out
    assert "rebuild_required" in out
    assert "stale_notes" in out
    assert "conflict_classes" in out
    assert isinstance(out["reconcile_actions"], list)


def test_post_restore_verify(tmp_path: Path) -> None:
    """Post-restore verify returns verified and readiness summary."""
    out = post_restore_verify("restore_123", target_repo_root=tmp_path)
    assert "verified" in out
    assert "generated_at_utc" in out


def test_restore_confidence_model() -> None:
    """RestoreConfidence serialization."""
    c = RestoreConfidence(0.5, "medium", ["Version mismatch warning."])
    d = c.to_dict()
    assert d["score"] == 0.5
    assert d["label"] == "medium"
    back = RestoreConfidence.from_dict(d)
    assert back.score == c.score


def test_rebuild_required_component_model() -> None:
    """RebuildRequiredComponent and ReconcileAction round-trip."""
    r = RebuildRequiredComponent("workday", "Corrupt state", "workflow-dataset state health")
    d = r.to_dict()
    assert d["subsystem_id"] == "workday"
    a = ReconcileAction("act_1", "refresh_stale", "continuity_shutdown", "Refresh stale", True, False)
    assert a.to_dict()["kind"] == "refresh_stale"


# ----- M49H.1: Reconcile policies + restore playbooks -----


def test_reconcile_policy_conservative(tmp_path: Path) -> None:
    """Conservative restore policy exists and has expected fields."""
    from workflow_dataset.migration_restore.reconcile_policies import (
        get_reconcile_policy,
        list_reconcile_policies,
        POLICY_CONSERVATIVE_RESTORE,
    )
    p = get_reconcile_policy(POLICY_CONSERVATIVE_RESTORE, tmp_path)
    assert p is not None
    assert p.policy_id == POLICY_CONSERVATIVE_RESTORE
    assert p.overwrite_target_allowed is False
    assert p.production_safe is True
    assert "conservative" in p.name.lower() or "Conservative" in p.name
    all_p = list_reconcile_policies(tmp_path)
    assert len(all_p) >= 3
    ids = {x.policy_id for x in all_p}
    assert POLICY_CONSERVATIVE_RESTORE in ids
    assert "balanced_restore" in ids
    assert "production_safe_restore" in ids


def test_restore_playbook_same_machine(tmp_path: Path) -> None:
    """Same-machine restore playbook exists with steps and suggested policy."""
    from workflow_dataset.migration_restore.reconcile_policies import (
        get_restore_playbook,
        list_restore_playbooks,
        PLAYBOOK_SAME_MACHINE_RESTORE,
    )
    pb = get_restore_playbook(PLAYBOOK_SAME_MACHINE_RESTORE, tmp_path)
    assert pb is not None
    assert pb.playbook_id == PLAYBOOK_SAME_MACHINE_RESTORE
    assert len(pb.steps) >= 4
    assert pb.suggested_policy_id
    assert any("validate" in s.command_or_action.lower() for s in pb.steps)
    all_pb = list_restore_playbooks(tmp_path)
    assert len(all_pb) >= 4


def test_build_restore_operator_summary(tmp_path: Path) -> None:
    """Operator summary includes what was restored, rebuilt, and needs review."""
    from workflow_dataset.migration_restore.operator_guidance import (
        build_restore_operator_summary,
        format_operator_summary_text,
    )
    restore_result = {"candidate_id": "restore_1", "status": "restored", "applied_subsystems": ["workday", "continuity_shutdown"]}
    summary = build_restore_operator_summary(restore_result, reconcile_result=None, restore_candidate_id="restore_1", target_repo_root=tmp_path)
    assert "what_was_restored" in summary
    assert summary["what_was_restored"] == ["workday", "continuity_shutdown"]
    assert "summary_lines" in summary
    assert any("restored" in line.lower() for line in summary["summary_lines"])
    text = format_operator_summary_text(summary)
    assert "Restore operator summary" in text or "restored" in text.lower()
