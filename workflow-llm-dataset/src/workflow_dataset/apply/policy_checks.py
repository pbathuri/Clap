"""
Policy checks for apply-to-project: feature enabled, confirmation, safe roots, overwrite/backup.
Defaults remain conservative and safe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def apply_policy_ok(config: Any) -> bool:
    """True if apply feature is enabled in config."""
    if config is None:
        return False
    return getattr(config, "apply_enabled", False)


def require_confirm(config: Any) -> bool:
    """True if explicit user confirmation is required (default True)."""
    if config is None:
        return True
    return getattr(config, "apply_require_confirm", True)


def target_root_allowed(
    target_root: str | Path,
    allowed_roots: list[str] | None = None,
    deny_roots: list[str] | None = None,
) -> tuple[bool, str]:
    """
    Check if target_root is allowed. Returns (ok, message).
    If allowed_roots is non-empty, target must be under one of them.
    deny_roots: never allow under these (e.g. /, /etc, $HOME).
    """
    target = Path(target_root).resolve()
    deny_roots = deny_roots or []
    for d in deny_roots:
        try:
            target.relative_to(Path(d).resolve())
            return False, f"Target path is under denied root: {d}"
        except ValueError:
            continue
    # Dangerous roots: avoid copying to filesystem root or system dirs
    parts = target.parts
    if parts and parts[0] == "/" and len(parts) <= 2:
        return False, "Target cannot be root or top-level system directory"
    if any(p in parts for p in ("etc", "usr", "bin", "sbin", "System", "Library")) and len(parts) <= 4:
        return False, "Target cannot be a system directory"
    if allowed_roots:
        allowed = [Path(r).resolve() for r in allowed_roots if r]
        if not allowed:
            return True, "No allowlist; target accepted"
        for root in allowed:
            try:
                target.relative_to(root)
                return True, "Target under allowed root"
            except ValueError:
                continue
        return False, f"Target not under any allowed root: {allowed_roots}"
    return True, "Target accepted"


def overwrite_allowed(config: Any) -> bool:
    """True if overwriting existing files is allowed (default False without explicit confirm)."""
    if config is None:
        return False
    return getattr(config, "apply_allow_overwrite", False)


def create_backups(config: Any) -> bool:
    """True if backups should be created when overwriting (default True)."""
    if config is None:
        return True
    return getattr(config, "apply_create_backups", True)


def rollback_enabled(config: Any) -> bool:
    """True if rollback is enabled (default True)."""
    if config is None:
        return True
    return getattr(config, "apply_rollback_enabled", True)
