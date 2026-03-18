"""
M38: Active cohort profile persistence. data/local/cohort/active_profile.txt
"""

from __future__ import annotations

from pathlib import Path

COHORT_DIR = "data/local/cohort"
ACTIVE_PROFILE_FILE = "active_profile.txt"

# When no file: no active cohort (default behavior: no cohort restrictions applied in first draft)
DEFAULT_ACTIVE_COHORT_ID = ""


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _dir_path(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / COHORT_DIR


def _active_profile_path(repo_root: Path | str | None = None) -> Path:
    return _dir_path(repo_root) / ACTIVE_PROFILE_FILE


def get_active_cohort_id(repo_root: Path | str | None = None) -> str:
    """Return active cohort profile id; empty if unset."""
    path = _active_profile_path(repo_root)
    if not path.exists() or not path.is_file():
        return DEFAULT_ACTIVE_COHORT_ID
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return DEFAULT_ACTIVE_COHORT_ID


def set_active_cohort_id(cohort_id: str, repo_root: Path | str | None = None) -> Path:
    """Persist active cohort id. Creates dir if needed."""
    path = _active_profile_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((cohort_id or "").strip(), encoding="utf-8")
    return path
