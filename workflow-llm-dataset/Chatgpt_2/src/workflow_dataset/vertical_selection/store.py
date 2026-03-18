"""
M39: Active vertical persistence. data/local/vertical_selection/active_vertical.txt
"""

from __future__ import annotations

from pathlib import Path

DIR_NAME = "data/local/vertical_selection"
FILE_NAME = "active_vertical.txt"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _path(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / DIR_NAME / FILE_NAME


def get_active_vertical_id(repo_root: Path | str | None = None) -> str:
    """Return active vertical id (scope lock); empty if unset."""
    p = _path(repo_root)
    if not p.exists() or not p.is_file():
        return ""
    try:
        return p.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def set_active_vertical_id(vertical_id: str, repo_root: Path | str | None = None) -> Path:
    """Persist active vertical id. Creates dir if needed."""
    p = _path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text((vertical_id or "").strip(), encoding="utf-8")
    return p
