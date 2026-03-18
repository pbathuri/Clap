"""
M28E–M28H: Worker lane store — persist lanes under data/local/lanes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.lanes.models import WorkerLane

LANES_ROOT = "data/local/lanes"
LANES_SUBDIR = "lanes"
LANE_FILE = "lane.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_lanes_dir(repo_root: Path | str | None = None) -> Path:
    """Return data/local/lanes/lanes; ensure it exists."""
    root = _repo_root(repo_root)
    path = root / LANES_ROOT / LANES_SUBDIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_lane_dir(lane_id: str, repo_root: Path | str | None = None) -> Path:
    """Directory for one lane: data/local/lanes/lanes/<lane_id>/."""
    base = get_lanes_dir(repo_root)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in (lane_id or "").strip()) or "default"
    return base / safe_id


def save_lane(lane: WorkerLane, repo_root: Path | str | None = None) -> Path:
    """Persist WorkerLane to lanes/<lane_id>/lane.json."""
    base = get_lanes_dir(repo_root)
    lane_dir = base / lane.lane_id
    lane_dir.mkdir(parents=True, exist_ok=True)
    path = lane_dir / LANE_FILE
    path.write_text(json.dumps(lane.to_dict(), indent=2), encoding="utf-8")
    return path


def load_lane(lane_id: str, repo_root: Path | str | None = None) -> WorkerLane | None:
    """Load WorkerLane by lane_id."""
    base = get_lanes_dir(repo_root)
    lane_dir = base / lane_id
    path = lane_dir / LANE_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return WorkerLane.from_dict(data)
    except Exception:
        return None


def list_lanes(
    project_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List lanes (newest first). Optional filter by project_id or status."""
    base = get_lanes_dir(repo_root)
    if not base.exists():
        return []
    out: list[dict[str, Any]] = []
    for d in sorted(base.iterdir(), key=lambda x: x.stat().st_mtime if x.is_dir() else 0, reverse=True):
        if not d.is_dir():
            continue
        f = d / LANE_FILE
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if project_id and data.get("project_id") != project_id:
                continue
            if status and data.get("status") != status:
                continue
            out.append({
                "lane_id": data.get("lane_id", d.name),
                "project_id": data.get("project_id", ""),
                "goal_id": data.get("goal_id", ""),
                "status": data.get("status", ""),
                "scope_id": data.get("scope", {}).get("scope_id", ""),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
            })
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out
