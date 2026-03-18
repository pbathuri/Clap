"""
M30D: Migration report and install/upgrade report formatting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.install_upgrade.version import read_current_version, get_current_version_display, get_package_version_from_pyproject
from workflow_dataset.install_upgrade.upgrade_plan import build_upgrade_plan, format_upgrade_plan
from workflow_dataset.install_upgrade.apply_upgrade import list_rollback_checkpoints


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_migration_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build migration/upgrade status report: current version, available upgrade, rollback checkpoints, blocked."""
    root = _repo_root(repo_root)
    version_str, source = get_current_version_display(root)
    pkg_version = get_package_version_from_pyproject(root)
    plan = build_upgrade_plan(target_version=pkg_version, repo_root=root)
    checkpoints = list_rollback_checkpoints(root)
    return {
        "current_version": version_str,
        "version_source": source,
        "package_version_pyproject": pkg_version,
        "upgrade_available": plan.current_version != plan.target_version and plan.can_proceed,
        "target_version": plan.target_version,
        "blocked_reasons": plan.blocked_reasons,
        "rollback_checkpoints_count": len(checkpoints),
        "latest_checkpoint_id": checkpoints[0].checkpoint_id if checkpoints else "",
        "migration_steps_count": len(plan.migration_steps),
    }


def format_migration_report(report: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Human-readable migration report."""
    if report is None:
        report = build_migration_report(repo_root)
    lines = [
        "=== Migration / upgrade report ===",
        "",
        f"Current version:     {report.get('current_version', '—')}  (source: {report.get('version_source', '—')})",
        f"Package (pyproject): {report.get('package_version_pyproject', '—')}",
        f"Target version:      {report.get('target_version', '—')}",
        f"Upgrade available:   {report.get('upgrade_available', False)}",
        f"Migration steps:     {report.get('migration_steps_count', 0)}",
        f"Rollback checkpoints: {report.get('rollback_checkpoints_count', 0)}",
        "",
    ]
    if report.get("latest_checkpoint_id"):
        lines.append(f"Latest checkpoint:   {report['latest_checkpoint_id']}")
        lines.append("")
    if report.get("blocked_reasons"):
        lines.append("[Blocked reasons]")
        for r in report["blocked_reasons"]:
            lines.append(f"  - {r}")
        lines.append("")
    lines.append("(Operator-controlled. Use release upgrade-plan and release upgrade-apply to upgrade.)")
    return "\n".join(lines)
