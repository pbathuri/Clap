"""
M45H.1: Persist and load confidence policies (optional overlay over built-in).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DIR_NAME = "data/local/shadow_execution"
POLICIES_FILE = "policies.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def load_policies(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Load confidence policies from JSON; returns list of policy dicts. Empty if file missing."""
    root = _repo_root(repo_root)
    path = root / DIR_NAME / POLICIES_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("policies", []))
    except Exception:
        return []


def save_policies(policies: list[dict[str, Any]], repo_root: Path | str | None = None) -> Path:
    """Save confidence policies to JSON."""
    root = _repo_root(repo_root)
    root = root / DIR_NAME
    root.mkdir(parents=True, exist_ok=True)
    path = root / POLICIES_FILE
    path.write_text(json.dumps({"policies": policies}, indent=2), encoding="utf-8")
    return path
