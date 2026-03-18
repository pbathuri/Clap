"""
M30A: Install bundle + upgrade models — product version, install profile,
env requirements, snapshots, migration requirements, rollback checkpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProductVersion:
    """Version identifier for the installed product (e.g. 0.1.0)."""
    version: str = ""
    bundle_id: str = ""
    installed_at_iso: str = ""
    source: str = ""  # pyproject | bundle | manifest


@dataclass
class EnvRequirements:
    """Environment requirements for an install (python, platform, disk)."""
    min_python: str = ""
    platform: list[str] = field(default_factory=list)
    disk_mb_min: int = 0


@dataclass
class EnabledModulesSnapshot:
    """Snapshot of enabled modules/capabilities at a point in time."""
    modules: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    captured_at_iso: str = ""


@dataclass
class PackRuntimeSnapshot:
    """Snapshot of pack/runtime state (ids and versions) for rollback."""
    pack_ids: list[str] = field(default_factory=list)
    runtime_summary: dict[str, Any] = field(default_factory=dict)
    captured_at_iso: str = ""


@dataclass
class InstallProfile:
    """M30: Install profile — version, env requirements, enabled modules, pack/runtime snapshot."""
    version: str = ""
    env_requirements: EnvRequirements = field(default_factory=EnvRequirements)
    enabled_modules: EnabledModulesSnapshot = field(default_factory=EnabledModulesSnapshot)
    pack_runtime_snapshot: PackRuntimeSnapshot = field(default_factory=PackRuntimeSnapshot)
    profile_id: str = ""


@dataclass
class MigrationRequirement:
    """One migration step required to move from version A to B."""
    migration_id: str = ""
    from_version: str = ""
    to_version: str = ""
    description: str = ""
    reversible: bool = True
    rollback_id: str = ""  # optional id for rollback step


@dataclass
class RollbackCheckpoint:
    """Checkpoint created before upgrade for possible rollback."""
    checkpoint_id: str = ""
    from_version: str = ""
    to_version: str = ""
    created_at_iso: str = ""
    backup_paths: list[str] = field(default_factory=list)
    state_snapshot: dict[str, Any] = field(default_factory=dict)


# M30D.1: Release channel
CHANNEL_STABLE = "stable"
CHANNEL_PREVIEW = "preview"
CHANNEL_INTERNAL = "internal"


@dataclass
class ReleaseChannel:
    """Release channel: stable / preview / internal. M30D.1."""
    channel_id: str = ""
    label: str = ""
    description: str = ""
    min_product_version: str = ""  # minimum product version supported on this channel
    allowed_policy_modes: tuple[str, ...] = ()  # e.g. enforce, audit, disabled
    supports_downgrade: bool = False
    upgrade_paths_to: tuple[str, ...] = ()  # channel ids that are valid upgrade targets from this channel


def product_version_to_dict(p: ProductVersion) -> dict[str, Any]:
    return {
        "version": p.version,
        "bundle_id": p.bundle_id,
        "installed_at_iso": p.installed_at_iso,
        "source": p.source,
    }


def product_version_from_dict(d: dict[str, Any]) -> ProductVersion:
    return ProductVersion(
        version=str(d.get("version", "")),
        bundle_id=str(d.get("bundle_id", "")),
        installed_at_iso=str(d.get("installed_at_iso", "")),
        source=str(d.get("source", "")),
    )


def rollback_checkpoint_to_dict(c: RollbackCheckpoint) -> dict[str, Any]:
    return {
        "checkpoint_id": c.checkpoint_id,
        "from_version": c.from_version,
        "to_version": c.to_version,
        "created_at_iso": c.created_at_iso,
        "backup_paths": list(c.backup_paths),
        "state_snapshot": dict(c.state_snapshot),
    }


def rollback_checkpoint_from_dict(d: dict[str, Any]) -> RollbackCheckpoint:
    return RollbackCheckpoint(
        checkpoint_id=str(d.get("checkpoint_id", "")),
        from_version=str(d.get("from_version", "")),
        to_version=str(d.get("to_version", "")),
        created_at_iso=str(d.get("created_at_iso", "")),
        backup_paths=list(d.get("backup_paths", [])),
        state_snapshot=dict(d.get("state_snapshot", {})),
    )
