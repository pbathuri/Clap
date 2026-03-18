"""
M39E–M39H: Persist active curated pack and first-value path progress.
Data: data/local/vertical_packs/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VERTICAL_PACKS_DIR = "data/local/vertical_packs"
ACTIVE_FILE = "active.json"
PROGRESS_FILE = "progress.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_vertical_packs_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / VERTICAL_PACKS_DIR


def get_active_pack(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return active pack state: active_curated_pack_id, applied_at_utc (optional)."""
    path = get_vertical_packs_dir(repo_root) / ACTIVE_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def set_active_pack(curated_pack_id: str, repo_root: Path | str | None = None) -> Path:
    """Persist active curated pack id. Returns path written."""
    from datetime import datetime, timezone
    root = get_vertical_packs_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ACTIVE_FILE
    data = {
        "active_curated_pack_id": curated_pack_id,
        "applied_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def clear_active_pack(repo_root: Path | str | None = None) -> bool:
    """Remove active pack file. Returns True if file existed."""
    path = get_vertical_packs_dir(repo_root) / ACTIVE_FILE
    if path.exists():
        path.unlink()
        return True
    return False


def get_path_progress(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return path progress: pack_id, path_id, reached_milestone_ids[], next_milestone_id, blocked_step_index (0 if none)."""
    path = get_vertical_packs_dir(repo_root) / PROGRESS_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def set_path_progress(
    pack_id: str,
    path_id: str,
    reached_milestone_ids: list[str],
    next_milestone_id: str = "",
    blocked_step_index: int = 0,
    repo_root: Path | str | None = None,
) -> Path:
    """Persist first-value path progress. Returns path written."""
    root = get_vertical_packs_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / PROGRESS_FILE
    from datetime import datetime, timezone
    data = {
        "pack_id": pack_id,
        "path_id": path_id,
        "reached_milestone_ids": list(reached_milestone_ids),
        "next_milestone_id": next_milestone_id,
        "blocked_step_index": blocked_step_index,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def set_milestone_reached(
    pack_id: str,
    path_id: str,
    milestone_id: str,
    repo_root: Path | str | None = None,
) -> Path:
    """Append milestone to reached list and update next_milestone_id from path. Returns path written."""
    progress = get_path_progress(repo_root)
    reached = list(progress.get("reached_milestone_ids", []))
    if milestone_id not in reached:
        reached.append(milestone_id)
    from workflow_dataset.vertical_packs.registry import get_curated_pack
    pack = get_curated_pack(pack_id)
    next_id = ""
    if pack and pack.first_value_path:
        milestone_ids = [m.milestone_id for m in pack.first_value_path.milestones]
        for mid in milestone_ids:
            if mid not in reached:
                next_id = mid
                break
    return set_path_progress(pack_id, path_id, reached, next_milestone_id=next_id, blocked_step_index=0, repo_root=repo_root)
