"""
Approved folders helper functions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.capability_discovery.approval_registry import (
    load_approval_registry,
    save_approval_registry,
    normalize_approved_paths,
)


def list_approved_folders(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    reg = load_approval_registry(repo_root)
    return normalize_approved_paths(reg.approved_paths)


def add_approved_folder(
    path: str,
    ops: list[str] | None = None,
    recursive: bool = True,
    inherit_mode: str = "inherit",
    sensitivity_tag: str = "unspecified",
    approval_source: str = "explicit_user",
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    reg = load_approval_registry(repo_root)
    entries = normalize_approved_paths(reg.approved_paths)
    entry = {
        "path": path,
        "allowed_operations": list(ops or []),
        "recursive": bool(recursive),
        "inherit_mode": inherit_mode,
        "sensitivity_tag": sensitivity_tag,
        "approval_source": approval_source,
        "revocation_state": "active",
        "approved_at": "",
        "reviewed_at": "",
        "expires_at": "",
    }
    existing = next((e for e in entries if e.get("path") == path), None)
    if existing:
        existing.update(entry)
    else:
        entries.append(entry)
    reg.approved_paths = entries
    save_approval_registry(reg, repo_root)
    return entries


def revoke_approved_folder(path: str, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    reg = load_approval_registry(repo_root)
    entries = normalize_approved_paths(reg.approved_paths)
    existing = next((e for e in entries if e.get("path") == path), None)
    if existing:
        existing["revocation_state"] = "revoked"
    else:
        entries.append({
            "path": path,
            "allowed_operations": [],
            "recursive": True,
            "inherit_mode": "inherit",
            "sensitivity_tag": "unspecified",
            "approval_source": "explicit_user",
            "revocation_state": "revoked",
            "approved_at": "",
            "reviewed_at": "",
            "expires_at": "",
        })
    reg.approved_paths = entries
    save_approval_registry(reg, repo_root)
    return entries
