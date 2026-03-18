"""
M49E–M49H Phase D: Mission control slice for migration/restore.
Latest restore candidate, restore blockers, reconcile-required, restore confidence, next recommended action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.migration_restore.bundle import get_bundle_manifest, list_bundle_refs
from workflow_dataset.migration_restore.validation import validate_bundle_for_target
from workflow_dataset.migration_restore.flows import conflict_aware_reconcile


def migration_restore_mission_control_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build mission-control slice: latest restore candidate, blockers, reconcile-required, confidence, next action."""
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    refs = list_bundle_refs(root)
    latest_ref = "latest"
    manifest = get_bundle_manifest(latest_ref, root)
    report = validate_bundle_for_target(latest_ref, target_repo_root=root)
    restore_blockers = [b.to_dict() for b in report.blockers]
    restore_confidence_score = report.restore_confidence.score if report.restore_confidence else 0.0
    reconcile_required_components: list[str] = []
    try:
        recon = conflict_aware_reconcile("latest", target_repo_root=root)
        reconcile_required_components = [r.get("subsystem_id", "") for r in recon.get("rebuild_required", [])]
        reconcile_required_components += list(set(a.get("subsystem_id", "") for a in recon.get("reconcile_actions", []) if a.get("subsystem_id")))
    except Exception:
        pass

    if report.passed and restore_confidence_score >= 0.9:
        next_recommended_restore_action = "workflow-dataset migration restore --bundle latest (optional: --approved to apply)"
    elif restore_blockers:
        next_recommended_restore_action = "workflow-dataset migration validate --bundle latest (fix blockers first)"
    else:
        next_recommended_restore_action = "workflow-dataset migration dry-run --bundle latest"

    return {
        "latest_restore_candidate_bundle_ref": latest_ref,
        "bundle_refs_available": refs,
        "restore_blockers": restore_blockers,
        "restore_blockers_count": len(restore_blockers),
        "reconcile_required_components": list(dict.fromkeys(reconcile_required_components)),
        "restore_confidence_score": restore_confidence_score,
        "restore_confidence_label": report.restore_confidence.label if report.restore_confidence else "unknown",
        "next_recommended_restore_action": next_recommended_restore_action,
    }
