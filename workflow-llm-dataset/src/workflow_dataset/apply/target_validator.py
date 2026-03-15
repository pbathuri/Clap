"""
Validate target path for apply: exists or parent exists, allowed by policy, no dangerous roots.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def validate_target(
    target_root: str | Path,
    allowed_roots: list[str] | None = None,
    deny_roots: list[str] | None = None,
    must_exist: bool = False,
) -> tuple[bool, str]:
    """
    Validate target path. Returns (valid, message).
    - target_root: directory to copy into
    - allowed_roots: if set, target must be under one of these
    - deny_roots: never allow under these
    - must_exist: if True, target_root must exist
    """
    from workflow_dataset.apply.policy_checks import target_root_allowed

    target = Path(target_root).resolve()
    ok, msg = target_root_allowed(target, allowed_roots=allowed_roots, deny_roots=deny_roots)
    if not ok:
        return False, msg
    if must_exist and not target.exists():
        return False, f"Target path does not exist: {target}"
    if target.exists() and not target.is_dir():
        return False, f"Target path is not a directory: {target}"
    if not target.exists():
        # Some ancestor directory must exist so we can create target
        p = target.parent
        while p != p.parent:
            if p.exists():
                if not p.is_dir():
                    return False, f"Ancestor is not a directory: {p}"
                break
            p = p.parent
        else:
            return False, f"No existing ancestor directory for: {target}"
    return True, "OK"
