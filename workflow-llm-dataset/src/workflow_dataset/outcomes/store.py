"""
M24N–M24Q: Session memory store — persist session outcomes, task/artifact outcomes, outcome histories.
Data under data/local/outcomes/.
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

from workflow_dataset.outcomes.models import SessionOutcome, TaskOutcome

OUTCOMES_DIR = "data/local/outcomes"
SESSIONS_SUBDIR = "sessions"
HISTORY_FILE = "outcome_history.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_outcomes_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / OUTCOMES_DIR


def get_sessions_dir(repo_root: Path | str | None = None) -> Path:
    return get_outcomes_dir(repo_root) / SESSIONS_SUBDIR


def _session_path(session_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id.strip())
    return get_sessions_dir(repo_root) / f"{safe}.json"


def save_session_outcome(outcome: SessionOutcome, repo_root: Path | str | None = None) -> Path:
    """Persist a session outcome. Returns path to written file."""
    root = get_sessions_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = _session_path(outcome.session_id, repo_root)
    path.write_text(json.dumps(outcome.to_dict(), indent=2), encoding="utf-8")
    _append_to_history(outcome, repo_root)
    return path


def get_session_outcome(session_id: str, repo_root: Path | str | None = None) -> SessionOutcome | None:
    """Load a session outcome by session_id."""
    path = _session_path(session_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionOutcome.from_dict(data)
    except Exception:
        return None


def list_session_outcomes(
    limit: int = 50,
    repo_root: Path | str | None = None,
    pack_id: str | None = None,
) -> list[SessionOutcome]:
    """List session outcomes newest first. Optional filter by pack_id."""
    sessions_dir = get_sessions_dir(repo_root)
    if not sessions_dir.exists():
        return []
    out: list[SessionOutcome] = []
    for f in sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            so = SessionOutcome.from_dict(data)
            if pack_id and so.pack_id != pack_id:
                continue
            out.append(so)
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out


def _history_path(repo_root: Path | str | None) -> Path:
    return get_outcomes_dir(repo_root) / HISTORY_FILE


def _append_to_history(outcome: SessionOutcome, repo_root: Path | str | None) -> None:
    """Append a short summary to outcome_history.json for pattern/signal use."""
    root = get_outcomes_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = _history_path(repo_root)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = data.get("entries", [])
        except Exception:
            entries = []
    else:
        entries = []
    entry = {
        "session_id": outcome.session_id,
        "timestamp": outcome.timestamp_end or outcome.timestamp_start,
        "pack_id": outcome.pack_id,
        "disposition": outcome.disposition,
        "task_count": len(outcome.task_outcomes),
        "blocked_count": len(outcome.blocked_causes),
        "useful_count": len(outcome.usefulness_confirmations),
        "source_refs": list(dict.fromkeys([t.source_ref for t in outcome.task_outcomes if t.source_ref])),
        "blocked_causes": [b.cause_code for b in outcome.blocked_causes],
    }
    entries.append(entry)
    # Keep last 500
    data = {"entries": entries[-500:], "updated": utc_now_iso()}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_outcome_history(repo_root: Path | str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    """Load outcome history entries for pattern/signal generation."""
    path = _history_path(repo_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
        return entries[-limit:]
    except Exception:
        return []
