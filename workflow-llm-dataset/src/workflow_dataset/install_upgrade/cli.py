"""
M30D: CLI commands for install-bundle, current-version, upgrade-plan, upgrade-apply, rollback, migration-report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.distribution.bundle import build_install_bundle, write_install_bundle
from workflow_dataset.install_upgrade.version import (
    read_current_version,
    get_current_version_display,
    get_package_version_from_pyproject,
    write_current_version,
)
from workflow_dataset.install_upgrade.models import ProductVersion
from workflow_dataset.install_upgrade.upgrade_plan import build_upgrade_plan, format_upgrade_plan
from workflow_dataset.install_upgrade.apply_upgrade import (
    apply_upgrade,
    list_rollback_checkpoints,
    perform_rollback,
)
from workflow_dataset.install_upgrade.reports import build_migration_report, format_migration_report
from workflow_dataset.install_upgrade.compatibility import build_compatibility_matrix, format_compatibility_matrix
from workflow_dataset.install_upgrade.channels import list_channels


def cmd_install_bundle(
    bundle_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Build and write install bundle; return path and bundle summary."""
    path = None
    try:
        bundle = build_install_bundle(repo_root=repo_root, bundle_id=bundle_id or "local_bundle")
        ver = get_package_version_from_pyproject(repo_root)
        bundle.version = ver
        path = write_install_bundle(bundle, repo_root=repo_root)
        return {
            "success": True,
            "path": str(path),
            "bundle_id": bundle.bundle_id,
            "version": bundle.version,
        }
    except Exception as e:
        return {"success": False, "path": path, "error": str(e)}


def cmd_current_version(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return current installed version and source."""
    version_str, source = get_current_version_display(repo_root)
    pkg = get_package_version_from_pyproject(repo_root)
    return {
        "version": version_str,
        "source": source,
        "package_version_pyproject": pkg,
    }


def cmd_upgrade_plan(
    target_version: str = "",
    target_bundle_id: str = "",
    current_channel: str = "",
    target_channel: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Build and return upgrade plan (current, target, channels, steps, blocked, warnings). M30D.1: channels + compatibility."""
    plan = build_upgrade_plan(
        target_version=target_version or None,
        target_bundle_id=target_bundle_id or None,
        current_channel=current_channel or None,
        target_channel=target_channel or None,
        repo_root=repo_root,
    )
    return {
        "current_version": plan.current_version,
        "target_version": plan.target_version,
        "target_bundle_id": plan.target_bundle_id,
        "current_channel": plan.current_channel,
        "target_channel": plan.target_channel,
        "can_proceed": plan.can_proceed,
        "reversible_overall": plan.reversible_overall,
        "migration_steps": [
            {"migration_id": s.migration_id, "description": s.description, "reversible": s.reversible}
            for s in plan.migration_steps
        ],
        "blocked_reasons": plan.blocked_reasons,
        "incompatible_warnings": plan.incompatible_warnings,
        "impact_preview": plan.impact_preview,
    }


def cmd_compatibility_matrix(
    repo_root: Path | str | None = None,
    json_out: bool = False,
) -> dict[str, Any] | str:
    """Build compatibility matrix (channels × version × runtime × policy). Returns dict or formatted string."""
    matrix = build_compatibility_matrix(repo_root=repo_root)
    if json_out:
        return matrix
    return format_compatibility_matrix(matrix)


def cmd_channels_list() -> list[dict[str, Any]]:
    """List release channels (stable, preview, internal)."""
    return [
        {
            "channel_id": ch.channel_id,
            "label": ch.label,
            "description": ch.description,
            "min_product_version": ch.min_product_version,
            "allowed_policy_modes": list(ch.allowed_policy_modes),
            "upgrade_paths_to": list(ch.upgrade_paths_to),
        }
        for ch in list_channels()
    ]


def cmd_upgrade_apply(
    target_version: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Apply upgrade; return success, checkpoint_id, message, failures."""
    return apply_upgrade(target_version=target_version or None, repo_root=repo_root)


def cmd_rollback(
    checkpoint_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Perform rollback to checkpoint (or latest if id empty)."""
    return perform_rollback(checkpoint_id=checkpoint_id or None, repo_root=repo_root)


def cmd_migration_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build migration/upgrade status report."""
    return build_migration_report(repo_root=repo_root)
