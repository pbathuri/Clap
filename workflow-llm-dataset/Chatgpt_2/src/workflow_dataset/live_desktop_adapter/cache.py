"""
M52: Disk cache for last-good edge desktop snapshot (prefetch / timeout merge).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CACHE_DIR = "data/local/live_desktop"
CACHE_FILE = "last_good_snapshot.json"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def cache_path(repo_root: Path | str | None = None) -> Path:
    d = _root(repo_root) / CACHE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d / CACHE_FILE


def load_last_good_snapshot(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    p = cache_path(repo_root)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_last_good_snapshot(snapshot: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    """Persist full snapshot (including adapter_meta) for prefetch and merge."""
    p = cache_path(repo_root)
    p.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
    return p
