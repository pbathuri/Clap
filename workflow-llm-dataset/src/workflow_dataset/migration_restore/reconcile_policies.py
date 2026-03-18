"""
M49H.1: Reconcile policies and restore playbooks.
Conservative restore, balanced restore, production-safe restore; playbooks for common migration cases.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.migration_restore.models import (
    ReconcilePolicy,
    RestorePlaybook,
    RestorePlaybookStep,
)
from workflow_dataset.migration_restore.models import ConflictClass


# Policy IDs
POLICY_CONSERVATIVE_RESTORE = "conservative_restore"
POLICY_BALANCED_RESTORE = "balanced_restore"
POLICY_PRODUCTION_SAFE_RESTORE = "production_safe_restore"


def _builtin_reconcile_policies() -> list[ReconcilePolicy]:
    return [
        ReconcilePolicy(
            policy_id=POLICY_CONSERVATIVE_RESTORE,
            name="Conservative restore",
            description="Do not overwrite target state; skip restored when target exists; suggest rebuild only.",
            overwrite_target_allowed=False,
            skip_restored_allowed=True,
            rebuild_required_action="suggest_only",
            require_review_for_overwrite=True,
            production_safe=True,
            scope_note="Safest for production or when target may have newer data.",
        ),
        ReconcilePolicy(
            policy_id=POLICY_BALANCED_RESTORE,
            name="Balanced restore",
            description="Allow overwrite with review; skip optional subsystems; suggest rebuild with optional review.",
            overwrite_target_allowed=True,
            skip_restored_allowed=True,
            rebuild_required_action="require_review",
            require_review_for_overwrite=True,
            production_safe=False,
            scope_note="Default for same-machine or dev; operator reviews overwrites.",
        ),
        ReconcilePolicy(
            policy_id=POLICY_PRODUCTION_SAFE_RESTORE,
            name="Production-safe restore",
            description="No overwrite of critical state; rebuild requires explicit review; production-safe defaults.",
            overwrite_target_allowed=False,
            skip_restored_allowed=True,
            rebuild_required_action="require_review",
            require_review_for_overwrite=True,
            production_safe=True,
            scope_note="For production or high-trust targets; never auto-overwrite.",
        ),
    ]


def get_reconcile_policy(policy_id: str, repo_root: Path | str | None = None) -> ReconcilePolicy | None:
    """Return reconcile policy by id (built-in first, then custom from data/local/migration_restore)."""
    for p in _builtin_reconcile_policies():
        if p.policy_id == policy_id:
            return p
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    for p in _load_custom_policies(root):
        if p.policy_id == policy_id:
            return p
    return None


def list_reconcile_policies(repo_root: Path | str | None = None) -> list[ReconcilePolicy]:
    """List all reconcile policies (built-in then custom)."""
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    seen: set[str] = set()
    out: list[ReconcilePolicy] = []
    for p in _builtin_reconcile_policies() + _load_custom_policies(root):
        if p.policy_id not in seen:
            seen.add(p.policy_id)
            out.append(p)
    return out


def _load_custom_policies(repo_root: Path) -> list[ReconcilePolicy]:
    path = repo_root / "data" / "local" / "migration_restore" / "reconcile_policies.yaml"
    if not path.is_file():
        path = repo_root / "data" / "local" / "migration_restore" / "reconcile_policies.json"
    if not path.is_file():
        return []
    try:
        import json
        raw = path.read_text()
        if path.suffix == ".json":
            data = json.loads(raw)
        else:
            import yaml
            data = yaml.safe_load(raw) or {}
        return [ReconcilePolicy.from_dict(x) for x in (data.get("policies") or [])]
    except Exception:
        return []


# Playbook IDs
PLAYBOOK_SAME_MACHINE_RESTORE = "same_machine_restore"
PLAYBOOK_NEW_MACHINE_RESTORE = "new_machine_restore"
PLAYBOOK_AFTER_UPGRADE_RESTORE = "after_upgrade_restore"
PLAYBOOK_PARTIAL_FAILURE_RECOVERY = "partial_failure_recovery"


def _builtin_restore_playbooks() -> list[RestorePlaybook]:
    return [
        RestorePlaybook(
            playbook_id=PLAYBOOK_SAME_MACHINE_RESTORE,
            name="Same-machine restore",
            description="Restore continuity state on the same machine (e.g. after reinstall or repair).",
            when_to_use="You are on the same machine; bundle was created here or from a backup of this repo.",
            suggested_policy_id=POLICY_BALANCED_RESTORE,
            applicable_conflict_classes=[ConflictClass.PARTIAL.value, ConflictClass.STALE.value],
            steps=[
                RestorePlaybookStep(1, "Validate bundle", "workflow-dataset migration validate --bundle latest", "Ensure bundle is valid for current target."),
                RestorePlaybookStep(2, "Dry-run", "workflow-dataset migration dry-run --bundle latest", "Review what would be restored."),
                RestorePlaybookStep(3, "Restore", "workflow-dataset migration restore --bundle latest --approved", "Apply restore after review."),
                RestorePlaybookStep(4, "Reconcile", "workflow-dataset migration reconcile --id <restore_id>", "Resolve conflicts if any."),
                RestorePlaybookStep(5, "Verify", "workflow-dataset migration verify --id <restore_id>", "Confirm startup readiness."),
            ],
        ),
        RestorePlaybook(
            playbook_id=PLAYBOOK_NEW_MACHINE_RESTORE,
            name="New-machine restore",
            description="Restore continuity state to a different machine or environment.",
            when_to_use="You moved the bundle to a new machine; target repo is empty or you want to bring over state.",
            suggested_policy_id=POLICY_CONSERVATIVE_RESTORE,
            applicable_conflict_classes=[ConflictClass.PARTIAL.value, ConflictClass.CONFLICTING.value, ConflictClass.UNSUPPORTED.value],
            steps=[
                RestorePlaybookStep(1, "Validate bundle", "workflow-dataset migration validate --bundle <bundle_ref>", "Check version and runtime compatibility on target."),
                RestorePlaybookStep(2, "Dry-run", "workflow-dataset migration dry-run --bundle <bundle_ref>", "See what would be restored; note local-only exclusions."),
                RestorePlaybookStep(3, "Restore (approved)", "workflow-dataset migration restore --bundle <bundle_ref> --approved", "Apply after confirming target is correct."),
                RestorePlaybookStep(4, "Reconcile", "workflow-dataset migration reconcile --id <restore_id>", "Address rebuild-required and stale components."),
                RestorePlaybookStep(5, "Operator summary", "workflow-dataset migration operator-summary --id <restore_id>", "Review what was restored, rebuilt, and needs review."),
            ],
        ),
        RestorePlaybook(
            playbook_id=PLAYBOOK_AFTER_UPGRADE_RESTORE,
            name="After-upgrade restore",
            description="Restore continuity state after a product version upgrade.",
            when_to_use="You ran upgrade-apply and want to bring back workday/continuity state from a pre-upgrade bundle.",
            suggested_policy_id=POLICY_BALANCED_RESTORE,
            applicable_conflict_classes=[ConflictClass.STALE.value, ConflictClass.CONFLICTING.value],
            steps=[
                RestorePlaybookStep(1, "Validate bundle", "workflow-dataset migration validate --bundle <bundle_ref>", "Ensure bundle version is compatible with upgraded product."),
                RestorePlaybookStep(2, "Dry-run", "workflow-dataset migration dry-run --bundle <bundle_ref>", "Review subsystems to restore."),
                RestorePlaybookStep(3, "Restore", "workflow-dataset migration restore --bundle <bundle_ref> --approved", "Apply; reconcile any conflicts."),
                RestorePlaybookStep(4, "Verify", "workflow-dataset migration verify --id <restore_id>", "Confirm startup and resume target."),
            ],
        ),
        RestorePlaybook(
            playbook_id=PLAYBOOK_PARTIAL_FAILURE_RECOVERY,
            name="Partial failure recovery",
            description="Recover when some subsystems failed to restore or are corrupt.",
            when_to_use="Restore completed but some components are rebuild-required or stale; you need to fix and re-verify.",
            suggested_policy_id=POLICY_CONSERVATIVE_RESTORE,
            applicable_conflict_classes=[ConflictClass.UNSUPPORTED.value, ConflictClass.PARTIAL.value],
            steps=[
                RestorePlaybookStep(1, "Reconcile", "workflow-dataset migration reconcile --id <restore_id>", "List rebuild-required and reconcile actions."),
                RestorePlaybookStep(2, "State health", "workflow-dataset state health", "Check persistence boundaries and fix corrupt/missing."),
                RestorePlaybookStep(3, "Refresh continuity", "workflow-dataset continuity shutdown (then re-run morning)", "Refresh shutdown/carry-forward if needed."),
                RestorePlaybookStep(4, "Verify", "workflow-dataset migration verify --id <restore_id>", "Re-check startup readiness."),
            ],
        ),
    ]


def get_restore_playbook(playbook_id: str, repo_root: Path | str | None = None) -> RestorePlaybook | None:
    """Return restore playbook by id."""
    for p in _builtin_restore_playbooks():
        if p.playbook_id == playbook_id:
            return p
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    for p in _load_custom_playbooks(root):
        if p.playbook_id == playbook_id:
            return p
    return None


def list_restore_playbooks(repo_root: Path | str | None = None) -> list[RestorePlaybook]:
    """List all restore playbooks."""
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    seen: set[str] = set()
    out: list[RestorePlaybook] = []
    for p in _builtin_restore_playbooks() + _load_custom_playbooks(root):
        if p.playbook_id not in seen:
            seen.add(p.playbook_id)
            out.append(p)
    return out


def _load_custom_playbooks(repo_root: Path) -> list[RestorePlaybook]:
    path = repo_root / "data" / "local" / "migration_restore" / "restore_playbooks.yaml"
    if not path.is_file():
        path = repo_root / "data" / "local" / "migration_restore" / "restore_playbooks.json"
    if not path.is_file():
        return []
    try:
        import json
        raw = path.read_text()
        if path.suffix == ".json":
            data = json.loads(raw)
        else:
            import yaml
            data = yaml.safe_load(raw) or {}
        return [RestorePlaybook.from_dict(x) for x in (data.get("playbooks") or [])]
    except Exception:
        return []
