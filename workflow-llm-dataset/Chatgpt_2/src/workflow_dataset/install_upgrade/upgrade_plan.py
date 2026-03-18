"""
M30B: Upgrade plan / migration plan — current version, target, impact preview,
migration steps, incompatible state warnings, blocked upgrade reasons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.install_upgrade.version import read_current_version, get_package_version_from_pyproject
from workflow_dataset.install_upgrade.models import MigrationRequirement, ProductVersion
from workflow_dataset.install_upgrade.compatibility import get_unsafe_upgrade_warnings, check_upgrade_path
from workflow_dataset.install_upgrade.models import CHANNEL_STABLE


@dataclass
class UpgradePlan:
    """Upgrade plan from current version to target version. M30D.1: channels + compatibility warnings."""
    current_version: str = ""
    target_version: str = ""
    target_bundle_id: str = ""
    current_channel: str = ""
    target_channel: str = ""
    generated_at_iso: str = ""
    migration_steps: list[MigrationRequirement] = field(default_factory=list)
    impact_preview: list[str] = field(default_factory=list)
    incompatible_warnings: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    can_proceed: bool = False
    reversible_overall: bool = True


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _version_tuple(v: str) -> tuple[int, ...]:
    """Parse version string to tuple for comparison (e.g. 0.1.0 -> (0, 1, 0))."""
    parts: list[int] = []
    for s in v.replace("-", ".").split("."):
        s = "".join(c for c in s if c.isdigit())
        parts.append(int(s) if s else 0)
    return tuple(parts)


def build_upgrade_plan(
    target_version: str = "",
    target_bundle_id: str = "",
    current_channel: str = "",
    target_channel: str = "",
    repo_root: Path | str | None = None,
) -> UpgradePlan:
    """
    Build upgrade plan from current to target version.
    If target_version is empty, uses package version from pyproject as target.
    """
    root = _repo_root(repo_root)
    plan = UpgradePlan(generated_at_iso=utc_now_iso())

    pv = read_current_version(root)
    plan.current_version = (pv.version if pv else "") or get_package_version_from_pyproject(root)
    if not plan.current_version:
        plan.current_version = "0.0.0"

    plan.target_version = target_version or get_package_version_from_pyproject(root)
    plan.target_bundle_id = target_bundle_id or f"bundle_{plan.target_version.replace('.', '_')}"
    plan.current_channel = (current_channel or CHANNEL_STABLE).strip().lower()
    plan.target_channel = (target_channel or plan.current_channel or CHANNEL_STABLE).strip().lower()

    # M30D.1: compatibility and unsafe upgrade path warnings
    path_check = check_upgrade_path(
        plan.current_version,
        plan.target_version,
        plan.current_channel,
        plan.target_channel,
    )
    for w in path_check.get("warnings", []):
        plan.incompatible_warnings.append(w)
    for u in path_check.get("unsafe_reasons", []):
        plan.blocked_reasons.append(u)
    if path_check.get("unsafe_reasons"):
        plan.can_proceed = False

    if plan.current_version == plan.target_version:
        plan.blocked_reasons.append("Current version equals target; no upgrade needed.")
        plan.can_proceed = False
        return plan

    try:
        cur_t = _version_tuple(plan.current_version)
        tgt_t = _version_tuple(plan.target_version)
        if tgt_t < cur_t:
            plan.blocked_reasons.append("Target version is lower than current (downgrade not supported in first-draft).")
            plan.can_proceed = False
    except Exception:
        plan.blocked_reasons.append("Version format not comparable.")
        plan.can_proceed = False

    if not plan.blocked_reasons:
        plan.migration_steps.append(MigrationRequirement(
            migration_id="ensure_install_dir",
            from_version=plan.current_version,
            to_version=plan.target_version,
            description="Ensure data/local/install exists.",
            reversible=True,
        ))
        plan.migration_steps.append(MigrationRequirement(
            migration_id="write_current_version",
            from_version=plan.current_version,
            to_version=plan.target_version,
            description="Write current_version.json with target version.",
            reversible=True,
            rollback_id="restore_version_file",
        ))
        plan.impact_preview.append("Current version file will be updated.")
        plan.can_proceed = True
        plan.reversible_overall = all(s.reversible for s in plan.migration_steps)

    return plan


def format_upgrade_plan(plan: UpgradePlan) -> str:
    """Human-readable upgrade plan."""
    lines = [
        "=== Upgrade plan ===",
        "",
        f"Current version: {plan.current_version}  channel: {plan.current_channel or 'stable'}",
        f"Target version:  {plan.target_version}  channel: {plan.target_channel or 'stable'}",
        f"Target bundle:   {plan.target_bundle_id}",
        f"Generated:       {plan.generated_at_iso}",
        "",
        "[Migration steps]",
    ]
    for s in plan.migration_steps:
        lines.append(f"  - {s.migration_id}: {s.description}  (reversible={s.reversible})")
    lines.append("")
    lines.append("[Impact preview]")
    for i in plan.impact_preview:
        lines.append(f"  - {i}")
    if plan.incompatible_warnings:
        lines.append("")
        lines.append("[Incompatible / warnings]")
        for w in plan.incompatible_warnings:
            lines.append(f"  - {w}")
    if plan.blocked_reasons:
        lines.append("")
        lines.append("[Blocked]")
        for b in plan.blocked_reasons:
            lines.append(f"  - {b}")
    lines.append("")
    lines.append(f"Can proceed: {plan.can_proceed}  Reversible overall: {plan.reversible_overall}")
    lines.append("(Operator-controlled. Run 'workflow-dataset release upgrade-apply' to apply.)")
    return "\n".join(lines)
