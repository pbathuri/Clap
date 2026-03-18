"""
M37I–M37L: Optional store for durable state snapshot (fast path / last-known-good).
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.state_durability.models import DurableStateSnapshot, StartupReadiness, ResumeTarget


STATE_DURABILITY_DIR = "data/local/state_durability"
SNAPSHOT_FILE = "last_snapshot.json"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_state_durability_dir(repo_root: Path | str | None = None) -> Path:
    return _root(repo_root) / STATE_DURABILITY_DIR


def save_snapshot(snapshot: DurableStateSnapshot, repo_root: Path | str | None = None) -> Path:
    """Persist snapshot for fast path; creates dir if needed."""
    d = get_state_durability_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / SNAPSHOT_FILE
    path.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")
    return path


def load_snapshot(repo_root: Path | str | None = None) -> DurableStateSnapshot | None:
    """Load last saved snapshot; return None if missing or invalid. Nested readiness/partial_state not fully reconstructed."""
    path = get_state_durability_dir(repo_root) / SNAPSHOT_FILE
    if not path.exists() or not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        resume = None
        if raw.get("resume_target"):
            rt = raw["resume_target"]
            resume = ResumeTarget(
                label=rt.get("label", ""),
                command=rt.get("command", ""),
                quality=rt.get("quality", ""),
                rationale=rt.get("rationale", []),
                project_id=rt.get("project_id", ""),
                day_id=rt.get("day_id", ""),
            )
        return DurableStateSnapshot(
            snapshot_id=raw.get("snapshot_id", ""),
            generated_at_utc=raw.get("generated_at_utc", ""),
            readiness=None,
            resume_target=resume,
            partial_state=None,
            summary_lines=raw.get("summary_lines", []),
        )
    except Exception:
        return None
