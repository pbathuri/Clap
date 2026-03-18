"""
M30C: Apply upgrade / rollback — stage, run migrations, preserve state, record failures, revert.
Operator-controlled; inspectable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.install_upgrade.models import (
    ProductVersion,
    RollbackCheckpoint,
    product_version_to_dict,
    product_version_from_dict,
    rollback_checkpoint_to_dict,
    rollback_checkpoint_from_dict,
)
from workflow_dataset.install_upgrade.version import (
    get_install_dir,
    get_current_version_path,
    read_current_version,
    write_current_version,
)
from workflow_dataset.install_upgrade.upgrade_plan import build_upgrade_plan, UpgradePlan

CHECKPOINTS_DIR = "checkpoints"
ROLLBACK_DIR = "rollbacks"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _stable_id(*parts: str) -> str:
    try:
        from workflow_dataset.utils.hashes import stable_id as _sid
        return _sid("upgrade", *parts, prefix="ck")
    except Exception:
        import hashlib
        h = hashlib.sha256("".join(parts).encode()).hexdigest()[:12]
        return f"ck_{h}"


def create_rollback_checkpoint(
    from_version: str,
    to_version: str,
    repo_root: Path | str | None = None,
) -> RollbackCheckpoint:
    """Create rollback checkpoint before upgrade: backup current version file, snapshot state."""
    root = _repo_root(repo_root)
    install_dir = get_install_dir(root)
    install_dir.mkdir(parents=True, exist_ok=True)
    version_path = get_current_version_path(root)
    backup_paths: list[str] = []
    state_snapshot: dict[str, Any] = {}

    pv = read_current_version(root)
    if pv:
        state_snapshot["previous_version"] = product_version_to_dict(pv)
    if version_path.exists():
        backup_dir = install_dir / ROLLBACK_DIR
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"current_version_{from_version.replace('.', '_')}.json.bak"
        backup_file.write_text(version_path.read_text(encoding="utf-8"), encoding="utf-8")
        backup_paths.append(str(backup_file))

    checkpoint_id = _stable_id(from_version, to_version, utc_now_iso())
    cp = RollbackCheckpoint(
        checkpoint_id=checkpoint_id,
        from_version=from_version,
        to_version=to_version,
        created_at_iso=utc_now_iso(),
        backup_paths=backup_paths,
        state_snapshot=state_snapshot,
    )
    checkpoints_dir = install_dir / CHECKPOINTS_DIR
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    cp_path = checkpoints_dir / f"{checkpoint_id}.json"
    cp_path.write_text(json.dumps(rollback_checkpoint_to_dict(cp), indent=2), encoding="utf-8")
    return cp


def apply_upgrade(
    plan: UpgradePlan | None = None,
    target_version: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Apply upgrade: create checkpoint, run migration steps, write new version.
    Returns: success, checkpoint_id, message, failures[].
    """
    root = _repo_root(repo_root)
    if plan is None:
        plan = build_upgrade_plan(target_version=target_version, repo_root=root)
    if not plan.can_proceed:
        return {
            "success": False,
            "checkpoint_id": "",
            "message": "Upgrade blocked: " + "; ".join(plan.blocked_reasons),
            "failures": list(plan.blocked_reasons),
        }
    failures: list[str] = []
    checkpoint_id = ""

    try:
        cp = create_rollback_checkpoint(plan.current_version, plan.target_version, root)
        checkpoint_id = cp.checkpoint_id
    except Exception as e:
        failures.append(f"Checkpoint creation: {e}")
        return {"success": False, "checkpoint_id": "", "message": str(e), "failures": failures}

    for step in plan.migration_steps:
        try:
            if step.migration_id == "ensure_install_dir":
                get_install_dir(root).mkdir(parents=True, exist_ok=True)
            elif step.migration_id == "write_current_version":
                pv = ProductVersion(
                    version=plan.target_version,
                    bundle_id=plan.target_bundle_id,
                    installed_at_iso=utc_now_iso(),
                    source="upgrade_apply",
                )
                write_current_version(pv, root)
        except Exception as e:
            failures.append(f"{step.migration_id}: {e}")

    if failures:
        return {
            "success": False,
            "checkpoint_id": checkpoint_id,
            "message": "Upgrade partially applied; failures: " + "; ".join(failures),
            "failures": failures,
        }
    return {
        "success": True,
        "checkpoint_id": checkpoint_id,
        "message": f"Upgrade applied: {plan.current_version} -> {plan.target_version}",
        "failures": [],
    }


def list_rollback_checkpoints(repo_root: Path | str | None = None) -> list[RollbackCheckpoint]:
    """List saved rollback checkpoints (newest first)."""
    root = _repo_root(repo_root)
    checkpoints_dir = get_install_dir(root) / CHECKPOINTS_DIR
    if not checkpoints_dir.exists():
        return []
    out: list[RollbackCheckpoint] = []
    for path in sorted(checkpoints_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            out.append(rollback_checkpoint_from_dict(data))
        except Exception:
            pass
    return out


def perform_rollback(
    checkpoint_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Restore state from checkpoint: restore version file from backup.
    Returns: success, message.
    """
    root = _repo_root(repo_root)
    checkpoints_dir = get_install_dir(root) / CHECKPOINTS_DIR
    if not checkpoint_id:
        checkpoints = list_rollback_checkpoints(root)
        if not checkpoints:
            return {"success": False, "message": "No rollback checkpoints found."}
        checkpoint_id = checkpoints[0].checkpoint_id
    cp_path = checkpoints_dir / f"{checkpoint_id}.json"
    if not cp_path.exists():
        return {"success": False, "message": f"Checkpoint not found: {checkpoint_id}"}
    try:
        data = json.loads(cp_path.read_text(encoding="utf-8"))
        cp = rollback_checkpoint_from_dict(data)
    except Exception as e:
        return {"success": False, "message": str(e)}

    version_path = get_current_version_path(root)
    prev = cp.state_snapshot.get("previous_version")
    if prev:
        pv = product_version_from_dict(prev)
        write_current_version(pv, root)
        return {"success": True, "message": f"Rolled back to version {pv.version}"}
    if cp.backup_paths:
        backup_path = Path(cp.backup_paths[0])
        if backup_path.exists():
            version_path.parent.mkdir(parents=True, exist_ok=True)
            version_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
            return {"success": True, "message": f"Restored version file from backup (from_version={cp.from_version})"}
    return {"success": False, "message": "Checkpoint has no backup or previous_version to restore."}
