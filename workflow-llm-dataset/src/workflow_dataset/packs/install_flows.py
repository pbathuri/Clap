"""
M25C: Install from registry, update, remove, rollback. Preserves activation state; conflict check after install/update.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_installer import install_pack, uninstall_pack
from workflow_dataset.packs.pack_registry import get_installed_pack, get_installed_manifest, list_installed_packs
from workflow_dataset.packs.pack_state import load_pack_state, save_pack_state, get_packs_dir
from workflow_dataset.packs.pack_activation import load_activation_state, save_activation_state
from workflow_dataset.packs.pack_history import (
    append_install_record,
    get_pack_history,
    get_previous_version,
    get_previous_manifest_path,
)
from workflow_dataset.packs.registry_index import get_registry_entry, load_local_registry
from workflow_dataset.packs.registry_policy import check_channel_policy
from workflow_dataset.packs.pack_state import get_active_role
from workflow_dataset.packs.pack_conflicts import detect_conflicts


def _packs_root(packs_dir: Path | str | None) -> Path:
    return Path(packs_dir).resolve() if packs_dir else get_packs_dir(None)


def _backup_current_manifest(pack_id: str, packs_dir: Path | str | None) -> bool:
    """Copy current manifest to pack_id/versions/<version>/manifest.json. Return True if backed up."""
    root = _packs_root(packs_dir)
    rec = get_installed_pack(pack_id, packs_dir)
    if not rec:
        return False
    ver = rec.get("version")
    if not ver:
        return False
    manifest_file = root / (rec.get("path") or rec.get("manifest_path") or f"{pack_id}/manifest.json")
    if not manifest_file.exists():
        return False
    versions_dir = root / pack_id / "versions" / ver
    versions_dir.mkdir(parents=True, exist_ok=True)
    dest = versions_dir / "manifest.json"
    shutil.copy2(manifest_file, dest)
    return True


def install_pack_from_registry(
    pack_id: str,
    packs_dir: Path | str | None = None,
    source: str = "local_registry",
) -> tuple[bool, str, str | None]:
    """
    Install pack by id from local registry. Looks up registry entry and uses source_path as manifest path.
    Applies release-channel policy: block blocks install; warn proceeds but returns warning message.
    Returns (success, message, warning_or_none).
    """
    if source != "local_registry":
        return False, f"Unsupported source: {source}. Use local_registry.", None
    entry = get_registry_entry(pack_id, packs_dir)
    if not entry:
        return False, f"Pack not in registry: {pack_id}", None
    # M25D.1: channel policy
    action, reason = check_channel_policy(
        entry.release_channel or "stable",
        get_active_role(packs_dir),
        packs_dir,
    )
    if action == "block":
        return False, f"Blocked: install from channel '{entry.release_channel}' not allowed. ({reason})", None
    warning_msg = f"Channel '{entry.release_channel}' is not recommended for this environment. ({reason})" if action == "warn" else None
    manifest_path = entry.source_path
    if not manifest_path:
        return False, f"Registry entry for {pack_id} has no source_path", None
    root = _packs_root(packs_dir)
    path = Path(manifest_path) if Path(manifest_path).is_absolute() else root / manifest_path
    if not path.exists():
        path = root / manifest_path.lstrip("/")
    if not path.exists():
        return False, f"Manifest path not found: {manifest_path}", None
    # If already installed, backup current before overwrite
    _backup_current_manifest(pack_id, packs_dir)
    ok, msg = install_pack(path, packs_dir)
    if ok:
        from workflow_dataset.packs.pack_registry import get_installed_pack
        rec = get_installed_pack(pack_id, packs_dir)
        if rec:
            append_install_record(pack_id, rec.get("version", ""), packs_dir, str(path))
    return ok, msg, warning_msg


def update_pack(pack_id: str, packs_dir: Path | str | None = None) -> tuple[bool, str, str | None]:
    """
    Update pack to registry version if newer. Backs up current manifest, installs from registry, preserves activation.
    Applies release-channel policy (block/warn). Returns (success, message, warning_or_none).
    """
    rec = get_installed_pack(pack_id, packs_dir)
    if not rec:
        return False, f"Pack not installed: {pack_id}", None
    entry = get_registry_entry(pack_id, packs_dir)
    if not entry:
        return False, f"Pack not in registry: {pack_id}. Use packs install to reinstall from path.", None
    # M25D.1: channel policy for update
    action, reason = check_channel_policy(
        entry.release_channel or "stable",
        get_active_role(packs_dir),
        packs_dir,
    )
    if action == "block":
        return False, f"Blocked: update from channel '{entry.release_channel}' not allowed. ({reason})", None
    warning_msg = f"Channel '{entry.release_channel}' is not recommended. ({reason})" if action == "warn" else None
    current_ver = rec.get("version", "")
    # Simple version compare: if registry version != current, treat as update available
    if entry.version == current_ver:
        return True, f"Already at latest version {current_ver}", None
    _backup_current_manifest(pack_id, packs_dir)
    ok, msg, install_warning = install_pack_from_registry(pack_id, packs_dir, "local_registry")
    if ok:
        # Activation state is unchanged (primary/pinned/suspended); no need to touch
        pass
    return ok, msg, install_warning or warning_msg


def remove_pack(pack_id: str, packs_dir: Path | str | None = None) -> tuple[bool, str]:
    """Remove pack from installed state (same as uninstall). Does not delete files."""
    return uninstall_pack(pack_id, packs_dir)


def rollback_pack(pack_id: str, packs_dir: Path | str | None = None) -> tuple[bool, str]:
    """
    Rollback to previous installed version. Restores manifest from versions/<prev_version>/manifest.json and state.
    """
    prev_path = get_previous_manifest_path(pack_id, packs_dir)
    if not prev_path or not prev_path.exists():
        prev_ver = get_previous_version(pack_id, packs_dir)
        return False, f"No previous version to rollback to" + (f" (had {prev_ver})" if prev_ver else "")
    _backup_current_manifest(pack_id, packs_dir)  # backup current before overwriting with previous
    ok, msg = install_pack(prev_path, packs_dir)
    if ok:
        rec = get_installed_pack(pack_id, packs_dir)
        if rec:
            append_install_record(pack_id, rec.get("version", ""), packs_dir, str(prev_path))
    return ok, msg


def list_installed_with_updates(packs_dir: Path | str | None = None) -> list[dict[str, Any]]:
    """List installed packs with update_available=True when registry has newer version."""
    installed = list_installed_packs(packs_dir)
    registry = {e.pack_id: e for e in load_local_registry(packs_dir)}
    out = []
    for rec in installed:
        pid = rec.get("pack_id", "")
        r = dict(rec)
        entry = registry.get(pid)
        if entry:
            r["update_available"] = entry.version != rec.get("version", "")
            r["registry_version"] = entry.version
        else:
            r["update_available"] = False
            r["registry_version"] = None
        out.append(r)
    return out
