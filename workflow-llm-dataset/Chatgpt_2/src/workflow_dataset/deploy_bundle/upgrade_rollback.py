"""
M40E–M40H: Upgrade and rollback hardening for deployment bundle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.deploy_bundle.registry import get_deployment_bundle


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_supported_upgrade_path(
    bundle_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Return supported upgrade path for bundle and current version; delegate to install_upgrade."""
    bundle = get_deployment_bundle(bundle_id)
    if not bundle:
        return {"error": f"Bundle not found: {bundle_id}", "supported": False}
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "bundle_id": bundle_id,
        "supported_upgrade_path": bundle.supported_upgrade_path.to_dict(),
        "current_version": "",
        "target_version": "",
        "can_proceed": False,
        "warnings": [],
        "blocked_reasons": [],
    }
    try:
        from workflow_dataset.install_upgrade.version import read_current_version, get_package_version_from_pyproject
        from workflow_dataset.install_upgrade.upgrade_plan import build_upgrade_plan
        pv = read_current_version(root)
        current = (pv.version if pv else "") or get_package_version_from_pyproject(root) or "0.0.0"
        out["current_version"] = current
        target = get_package_version_from_pyproject(root) or current
        out["target_version"] = target
        plan = build_upgrade_plan(target_version=target, repo_root=root)
        out["can_proceed"] = plan.can_proceed
        out["warnings"] = list(plan.incompatible_warnings or [])
        out["blocked_reasons"] = list(plan.blocked_reasons or [])
    except Exception as e:
        out["blocked_reasons"].append(str(e))
    return out


def get_rollback_readiness(
    bundle_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Return rollback readiness: supported, checkpoint exists or can be created."""
    bundle = get_deployment_bundle(bundle_id)
    if not bundle:
        return {"error": f"Bundle not found: {bundle_id}", "ready": False}
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "bundle_id": bundle_id,
        "supported_rollback_path": bundle.supported_rollback_path.to_dict(),
        "ready": bundle.supported_rollback_path.supported,
        "checkpoint_required": bundle.supported_rollback_path.checkpoint_required_before_upgrade,
        "latest_checkpoint_id": "",
        "rollback_hints": list(bundle.supported_rollback_path.rollback_hints),
    }
    try:
        from workflow_dataset.install_upgrade.apply_upgrade import list_rollback_checkpoints
        checkpoints = list_rollback_checkpoints(root)
        if checkpoints:
            out["latest_checkpoint_id"] = checkpoints[0].checkpoint_id
    except Exception:
        pass
    return out


def get_risky_upgrade_warnings(
    bundle_id: str,
    target_version: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Return risky or unsupported upgrade warnings for bundle + target version."""
    bundle = get_deployment_bundle(bundle_id)
    if not bundle:
        return {"error": f"Bundle not found: {bundle_id}", "warnings": []}
    root = _repo_root(repo_root)
    out: dict[str, Any] = {"bundle_id": bundle_id, "target_version": target_version, "warnings": []}
    try:
        from workflow_dataset.install_upgrade.version import read_current_version, get_package_version_from_pyproject
        from workflow_dataset.install_upgrade.compatibility import get_unsafe_upgrade_warnings, check_upgrade_path
        current = ""
        pv = read_current_version(root)
        if pv:
            current = pv.version
        if not current:
            current = get_package_version_from_pyproject(root) or "0.0.0"
        target = target_version or get_package_version_from_pyproject(root) or current
        out["current_version"] = current
        out["target_version"] = target
        warnings = get_unsafe_upgrade_warnings(current, target)
        out["warnings"] = list(warnings) if warnings else []
        path_result = check_upgrade_path(current, target)
        if not path_result.get("allowed", True) and path_result.get("unsafe_reasons"):
            out["warnings"].extend(path_result["unsafe_reasons"])
    except Exception as e:
        out["warnings"].append(str(e))
    return out
