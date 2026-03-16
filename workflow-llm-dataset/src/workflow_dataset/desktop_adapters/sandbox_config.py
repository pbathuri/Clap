"""
M23C-F2: Sandbox root for desktop adapter snapshot and read-only outputs.
All writes go under this root; no writes to originals.
"""

from __future__ import annotations

from pathlib import Path


DESKTOP_ADAPTERS_SANDBOX = Path("data/local/desktop_adapters/sandbox")


def get_sandbox_root(repo_root: Path | str | None = None) -> Path:
    """Return sandbox root for adapter snapshots; ensure it exists. Writes only under this path."""
    if repo_root is not None:
        base = Path(repo_root).resolve()
    else:
        try:
            from workflow_dataset.path_utils import get_repo_root
            base = Path(get_repo_root()).resolve()
        except Exception:
            base = Path.cwd().resolve()
    root = base / DESKTOP_ADAPTERS_SANDBOX
    root.mkdir(parents=True, exist_ok=True)
    return root
