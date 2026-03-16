"""
M23M: Corrections storage paths. data/local/corrections.
"""

from __future__ import annotations

from pathlib import Path

CORRECTIONS_ROOT = "data/local/corrections"
EVENTS_DIR_NAME = "events"
UPDATES_DIR_NAME = "updates"
PROPOSED_DIR_NAME = "proposed"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_corrections_root(repo_root: Path | str | None = None) -> Path:
    out = _repo_root(repo_root) / CORRECTIONS_ROOT
    out.mkdir(parents=True, exist_ok=True)
    return out


def get_events_dir(repo_root: Path | str | None = None) -> Path:
    d = get_corrections_root(repo_root) / EVENTS_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_updates_dir(repo_root: Path | str | None = None) -> Path:
    d = get_corrections_root(repo_root) / UPDATES_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_proposed_dir(repo_root: Path | str | None = None) -> Path:
    d = get_corrections_root(repo_root) / PROPOSED_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d
