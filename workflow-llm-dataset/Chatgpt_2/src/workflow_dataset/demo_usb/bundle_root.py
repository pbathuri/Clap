"""
M51C: Resolve demo bundle root (USB or folder copy).
"""

from __future__ import annotations

import os
from pathlib import Path


def _is_valid_demo_bundle(root: Path) -> bool:
    r = root.resolve()
    return (r / "configs" / "settings.yaml").is_file() and (r / "src" / "workflow_dataset").is_dir()


def resolve_demo_bundle_root(
    explicit: Path | str | None = None,
    *,
    allow_cwd: bool = True,
) -> Path:
    """
    Resolve product root for USB demo.
    Order: explicit path > WORKFLOW_DEMO_BUNDLE_ROOT > cwd (if valid bundle).
    """
    if explicit:
        p = Path(explicit).resolve()
        if not _is_valid_demo_bundle(p):
            raise ValueError(
                f"Not a valid demo bundle (need configs/settings.yaml + src/workflow_dataset): {p}"
            )
        return p
    env = os.environ.get("WORKFLOW_DEMO_BUNDLE_ROOT", "").strip()
    if env:
        p = Path(env).resolve()
        if not _is_valid_demo_bundle(p):
            raise ValueError(
                f"WORKFLOW_DEMO_BUNDLE_ROOT is not a valid bundle: {p}"
            )
        return p
    if allow_cwd:
        cwd = Path.cwd().resolve()
        if _is_valid_demo_bundle(cwd):
            return cwd
    raise ValueError(
        "Demo bundle root not found. Pass --bundle-root, set WORKFLOW_DEMO_BUNDLE_ROOT, "
        "or run from the product directory (configs/settings.yaml + src/workflow_dataset)."
    )


def bundle_resolution_source(explicit: Path | str | None) -> str:
    if explicit:
        return "explicit"
    if os.environ.get("WORKFLOW_DEMO_BUNDLE_ROOT", "").strip():
        return "env"
    cwd = Path.cwd().resolve()
    if (cwd / "configs" / "settings.yaml").is_file() and (cwd / "src" / "workflow_dataset").is_dir():
        return "cwd"
    return "unknown"
