"""
M23K: Copilot paths. data/local/copilot.
"""

from __future__ import annotations

from pathlib import Path

COPILOT_ROOT = "data/local/copilot"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_copilot_root(repo_root: Path | str | None = None) -> Path:
    out = _repo_root(repo_root) / COPILOT_ROOT
    out.mkdir(parents=True, exist_ok=True)
    return out


def get_routines_dir(repo_root: Path | str | None = None) -> Path:
    d = get_copilot_root(repo_root) / "routines"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_runs_dir(repo_root: Path | str | None = None) -> Path:
    d = get_copilot_root(repo_root) / "runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_reminders_path(repo_root: Path | str | None = None) -> Path:
    return get_copilot_root(repo_root) / "reminders.yaml"
