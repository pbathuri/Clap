"""
M29I–M29L: Review studio store — inbox snapshot, operator notes. Optional persistence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REVIEW_STUDIO_DIR = "data/local/review_studio"
SNAPSHOT_FILE = "inbox_snapshot.json"
NOTES_FILE = "operator_notes.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_review_studio_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / REVIEW_STUDIO_DIR


def save_inbox_snapshot(
    inbox_count: int,
    oldest_item_id: str = "",
    next_recommended_id: str = "",
    repo_root: Path | str | None = None,
) -> Path:
    """Save lightweight snapshot for 'oldest unresolved' / next recommended."""
    d = get_review_studio_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / SNAPSHOT_FILE
    path.write_text(json.dumps({
        "inbox_count": inbox_count,
        "oldest_item_id": oldest_item_id,
        "next_recommended_id": next_recommended_id,
    }, indent=2), encoding="utf-8")
    return path


def load_inbox_snapshot(repo_root: Path | str | None = None) -> dict[str, Any]:
    path = get_review_studio_dir(repo_root) / SNAPSHOT_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_operator_note(item_id: str, note: str, repo_root: Path | str | None = None) -> Path:
    """Store operator note for an inbox item (by item_id)."""
    d = get_review_studio_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / NOTES_FILE
    notes: dict[str, str] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            notes = dict(data.get("notes", {}))
        except Exception:
            pass
    notes[item_id] = note
    path.write_text(json.dumps({"notes": notes}, indent=2), encoding="utf-8")
    return path


def load_operator_notes(repo_root: Path | str | None = None) -> dict[str, str]:
    path = get_review_studio_dir(repo_root) / NOTES_FILE
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return dict(data.get("notes", {}))
    except Exception:
        return {}
