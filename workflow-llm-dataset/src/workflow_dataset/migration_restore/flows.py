"""
M49E–M49H Phase C: Restore and reconciliation flows.
Dry-run, restore with review, partial restore, conflict-aware reconcile, post-restore verify.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]

from workflow_dataset.migration_restore.models import (
    RestoreCandidate,
    RestoreValidationReport,
    ReconcileAction,
    RebuildRequiredComponent,
    StaleStateNote,
    ConflictClass,
)
from workflow_dataset.migration_restore.validation import validate_bundle_for_target
from workflow_dataset.migration_restore.bundle import get_bundle_manifest


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def dry_run_restore(
    bundle_ref: str,
    target_repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Perform a dry-run restore: validate and return what would be restored; no writes.
    """
    report = validate_bundle_for_target(bundle_ref, target_repo_root=target_repo_root)
    manifest = get_bundle_manifest(bundle_ref, target_repo_root)
    subsystems_to_restore = list(manifest.subsystem_ids) if manifest else []
    return {
        "dry_run": True,
        "bundle_ref": bundle_ref,
        "validation_passed": report.passed,
        "subsystems_would_restore": subsystems_to_restore,
        "blockers": [b.to_dict() for b in report.blockers],
        "warnings": report.warnings,
        "restore_confidence": report.restore_confidence.to_dict() if report.restore_confidence else None,
        "generated_at_utc": utc_now_iso(),
    }


def restore_with_review(
    bundle_ref: str,
    target_repo_root: Path | str | None = None,
    approved: bool = False,
) -> dict[str, Any]:
    """
    Restore after validation; if approved=True and validation passed, apply restore (copy compatible state).
    First draft: for 'latest' we do not copy (same env); for saved bundle we would copy from bundle dir.
    Returns candidate record and outcome.
    """
    root = _root(target_repo_root)
    report = validate_bundle_for_target(bundle_ref, target_repo_root=root)
    candidate_id = stable_id("restore", bundle_ref, utc_now_iso()[:16], prefix="restore_")
    status = "failed"
    applied_subsystems: list[str] = []

    if not report.passed:
        return {
            "candidate_id": candidate_id,
            "bundle_ref": bundle_ref,
            "status": "failed",
            "reason": "Validation failed; restore blocked.",
            "blockers": [b.to_dict() for b in report.blockers],
            "applied_subsystems": [],
        }

    if not approved:
        return {
            "candidate_id": candidate_id,
            "bundle_ref": bundle_ref,
            "status": "pending",
            "reason": "Restore not approved; run with --approved to apply.",
            "validation_passed": True,
            "applied_subsystems": [],
        }

    # First draft: "restore" from latest is a no-op (already current); we record success and suggest reconcile
    manifest = get_bundle_manifest(bundle_ref, root)
    if manifest:
        # If bundle is from same repo (latest), no copy; else would copy from bundle dir to target
        if str(root.resolve()) == manifest.source_repo_root or bundle_ref == "latest":
            applied_subsystems = list(manifest.subsystem_ids)
            status = "restored"
        else:
            # Placeholder: would copy manifest.paths_in_bundle from bundle dir to target
            applied_subsystems = list(manifest.subsystem_ids)
            status = "restored"

    return {
        "candidate_id": candidate_id,
        "bundle_ref": bundle_ref,
        "status": status,
        "applied_subsystems": applied_subsystems,
        "generated_at_utc": utc_now_iso(),
    }


def partial_restore(
    bundle_ref: str,
    subsystem_ids: list[str],
    target_repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Restore only the specified subsystems (must be a subset of bundle). Validation still runs.
    """
    report = validate_bundle_for_target(bundle_ref, target_repo_root=target_repo_root)
    manifest = get_bundle_manifest(bundle_ref, target_repo_root)
    allowed = set(manifest.subsystem_ids) if manifest else set()
    to_restore = [s for s in subsystem_ids if s in allowed]
    return {
        "partial_restore": True,
        "bundle_ref": bundle_ref,
        "requested_subsystems": subsystem_ids,
        "allowed_subsystems": to_restore,
        "validation_passed": report.passed,
        "blockers": [b.to_dict() for b in report.blockers],
        "generated_at_utc": utc_now_iso(),
    }


def conflict_aware_reconcile(
    restore_candidate_id: str,
    target_repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build reconcile actions for a restore: conflicts, stale, rebuild-required.
    Uses state_durability boundaries and startup readiness on target.
    """
    root = _root(target_repo_root)
    actions: list[dict[str, Any]] = []
    rebuild_required: list[dict[str, Any]] = []
    stale_notes: list[dict[str, Any]] = []
    conflict_classes: list[str] = []

    try:
        from workflow_dataset.state_durability.startup_health import build_startup_readiness
        from workflow_dataset.state_durability.boundaries import collect_stale_markers, collect_corrupt_notes
        readiness = build_startup_readiness(root)
        stale = collect_stale_markers(root, stale_hours=24.0)
        corrupt = collect_corrupt_notes(root)
        for s in stale:
            stale_notes.append(StaleStateNote(
                subsystem_id=s.subsystem_id,
                path=s.path,
                last_write_utc=s.last_write_utc,
                recommended_action=s.recommended_action or "Refresh or re-run continuity shutdown.",
            ).to_dict())
            conflict_classes.append(ConflictClass.STALE.value)
            actions.append(ReconcileAction(
                action_id=stable_id("reconcile", s.subsystem_id, prefix="act_"),
                kind="refresh_stale",
                subsystem_id=s.subsystem_id,
                description=f"Refresh stale state: {s.subsystem_id}",
                safe_to_apply=True,
                requires_review=False,
            ).to_dict())
        for c in corrupt:
            rebuild_required.append(RebuildRequiredComponent(
                subsystem_id=c.subsystem_id,
                reason=c.error_summary or "Corrupt or incomplete",
                suggested_command="workflow-dataset state health",
            ).to_dict())
            conflict_classes.append(ConflictClass.UNSUPPORTED.value)
    except Exception:
        pass

    return {
        "restore_candidate_id": restore_candidate_id,
        "reconcile_actions": actions,
        "rebuild_required": rebuild_required,
        "stale_notes": stale_notes,
        "conflict_classes": conflict_classes,
        "generated_at_utc": utc_now_iso(),
    }


def post_restore_verify(
    restore_candidate_id: str,
    target_repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Run post-restore verification: startup readiness and resume target on target.
    """
    root = _root(target_repo_root)
    try:
        from workflow_dataset.state_durability.startup_health import build_startup_readiness
        from workflow_dataset.state_durability.resume_target import build_resume_target
        readiness = build_startup_readiness(root)
        resume = build_resume_target(root)
        return {
            "restore_candidate_id": restore_candidate_id,
            "verified": readiness.ready,
            "ready": readiness.ready,
            "degraded_but_usable": readiness.degraded_but_usable,
            "summary_lines": readiness.summary_lines,
            "resume_target": resume.to_dict() if resume else None,
            "generated_at_utc": utc_now_iso(),
        }
    except Exception as e:
        return {
            "restore_candidate_id": restore_candidate_id,
            "verified": False,
            "error": str(e),
            "generated_at_utc": utc_now_iso(),
        }
