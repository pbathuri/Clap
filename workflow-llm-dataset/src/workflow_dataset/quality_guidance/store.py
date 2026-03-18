"""
M47I–M47L: Persist guidance items for explain --id (optional; latest set only).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.quality_guidance.models import GuidanceItem


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _guidance_dir(root: Path) -> Path:
    return root / "data/local/quality_guidance"


def _latest_path(root: Path) -> Path:
    return _guidance_dir(root) / "latest_guidance.json"


def save_latest_guidance(items: list[GuidanceItem], repo_root: Path | str | None = None) -> Path:
    """Persist latest guidance items (by kind) for explain --id lookup."""
    root = _repo_root(repo_root)
    d = _guidance_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    path = _latest_path(root)
    data = [g.to_dict() for g in items]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def get_guidance_by_id(guide_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Return a guidance item by id from latest_guidance.json."""
    root = _repo_root(repo_root)
    path = _latest_path(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return None
        for g in data:
            if g.get("guide_id") == guide_id:
                return g
    except Exception:
        pass
    return None


def list_latest_guide_ids(repo_root: Path | str | None = None) -> list[str]:
    """List guide_ids from latest_guidance.json."""
    root = _repo_root(repo_root)
    path = _latest_path(root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return [g.get("guide_id", "") for g in data if g.get("guide_id")]
    except Exception:
        return []
