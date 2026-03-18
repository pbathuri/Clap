"""
M37A–M37D: Active default experience profile persistence. data/local/default_experience/active_profile.txt
"""

from __future__ import annotations

from pathlib import Path


DEFAULT_EXPERIENCE_DIR = "data/local/default_experience"
ACTIVE_PROFILE_FILE = "active_profile.txt"

DEFAULT_PROFILE_ID = "calm_default"  # when no file present


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _dir_path(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / DEFAULT_EXPERIENCE_DIR


def _active_profile_path(repo_root: Path | str | None = None) -> Path:
    return _dir_path(repo_root) / ACTIVE_PROFILE_FILE


def get_active_default_profile_id(repo_root: Path | str | None = None) -> str:
    """Return active profile id; calm_default if unset."""
    path = _active_profile_path(repo_root)
    if not path.exists() or not path.is_file():
        return DEFAULT_PROFILE_ID
    try:
        raw = path.read_text(encoding="utf-8").strip()
        return raw if raw else DEFAULT_PROFILE_ID
    except Exception:
        return DEFAULT_PROFILE_ID


def set_active_default_profile_id(profile_id: str, repo_root: Path | str | None = None) -> Path:
    """Persist active profile id. Creates dir if needed."""
    path = _active_profile_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile_id.strip(), encoding="utf-8")
    return path
