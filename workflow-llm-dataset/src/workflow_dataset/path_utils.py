"""
Repo-local path resolution so config paths work from any cwd.
Used by CLI and pilot/health; no cloud or absolute path guessing.
"""

from __future__ import annotations

from pathlib import Path


def get_repo_root() -> Path:
    """Project root (directory containing configs/settings.yaml). Resolves from package location."""
    start = Path(__file__).resolve().parent
    for _ in range(5):
        if (start / "configs" / "settings.yaml").exists():
            return start
        parent = start.parent
        if parent == start:
            break
        start = parent
    return Path.cwd()


def resolve_config_path(path: str) -> Path | None:
    """Resolve relative path against project root. Returns None if path is empty."""
    if not path or not path.strip():
        return None
    p = Path(path)
    if p.is_absolute():
        return p
    return get_repo_root() / path
