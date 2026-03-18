"""
M23L: Context storage paths. data/local/context.
"""

from __future__ import annotations

from pathlib import Path

CONTEXT_ROOT = "data/local/context"
SNAPSHOTS_DIR_NAME = "snapshots"
LATEST_SNAPSHOT_NAME = "latest.json"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_context_root(repo_root: Path | str | None = None) -> Path:
    out = _repo_root(repo_root) / CONTEXT_ROOT
    out.mkdir(parents=True, exist_ok=True)
    return out


def get_snapshots_dir(repo_root: Path | str | None = None) -> Path:
    d = get_context_root(repo_root) / SNAPSHOTS_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_latest_snapshot_path(repo_root: Path | str | None = None) -> Path:
    return get_context_root(repo_root) / LATEST_SNAPSHOT_NAME


def get_previous_snapshot_path(repo_root: Path | str | None = None) -> Path:
    """Path where we copy 'previous' for compare. Optional."""
    return get_context_root(repo_root) / "previous.json"
