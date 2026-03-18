"""
M36A–M36D: Workday state and day summary persistence. Local-only; data/local/workday/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.workday.models import WorkdayStateRecord, DaySummarySnapshot


WORKDAY_DIR = "data/local/workday"
STATE_FILE = "state.json"
SUMMARIES_DIR = "summaries"
ACTIVE_PRESET_FILE = "active_preset.txt"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _workday_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / WORKDAY_DIR


def _state_path(repo_root: Path | str | None = None) -> Path:
    return _workday_dir(repo_root) / STATE_FILE


def load_workday_state(repo_root: Path | str | None = None) -> WorkdayStateRecord:
    """Load current workday state; return default record if missing."""
    path = _state_path(repo_root)
    if not path.exists() or not path.is_file():
        return WorkdayStateRecord()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return WorkdayStateRecord.from_dict(raw)
    except Exception:
        return WorkdayStateRecord()


def save_workday_state(record: WorkdayStateRecord, repo_root: Path | str | None = None) -> Path:
    """Persist workday state. Creates dir if needed."""
    path = _state_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
    return path


def load_day_summary(day_id: str, repo_root: Path | str | None = None) -> DaySummarySnapshot | None:
    """Load day summary by day_id (e.g. YYYY-MM-DD)."""
    root = _repo_root(repo_root)
    path = _workday_dir(root) / SUMMARIES_DIR / f"{day_id}.json"
    if not path.exists() or not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return DaySummarySnapshot.from_dict(raw)
    except Exception:
        return None


def save_day_summary(snapshot: DaySummarySnapshot, repo_root: Path | str | None = None) -> Path:
    """Persist day summary."""
    root = _repo_root(repo_root)
    path = _workday_dir(root) / SUMMARIES_DIR / f"{snapshot.day_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")
    return path


def day_id_from_iso(iso: str) -> str:
    """Extract YYYY-MM-DD from ISO timestamp."""
    if not iso or "T" not in iso:
        return ""
    return iso.split("T")[0]


def current_day_id() -> str:
    """Current date as day_id (YYYY-MM-DD)."""
    return day_id_from_iso(utc_now_iso())


def get_active_workday_preset_id(repo_root: Path | str | None = None) -> str | None:
    """Read active workday preset id from data/local/workday/active_preset.txt."""
    path = _workday_dir(repo_root) / ACTIVE_PRESET_FILE
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except Exception:
        return None


def set_active_workday_preset_id(preset_id: str, repo_root: Path | str | None = None) -> Path:
    """Write active workday preset id. Creates workday dir if needed."""
    path = _workday_dir(repo_root) / ACTIVE_PRESET_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(preset_id.strip(), encoding="utf-8")
    return path
