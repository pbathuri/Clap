"""
M24J–M24M: Session storage — persist and load sessions under data/local/session/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.session.models import Session

SESSION_ROOT = "data/local/session"
CURRENT_SESSION_FILE = "current_session_id.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_sessions_dir(repo_root: Path | str | None = None) -> Path:
    """Base directory for session state: data/local/session."""
    return _repo_root(repo_root) / SESSION_ROOT


def get_session_path(session_id: str, repo_root: Path | str | None = None) -> Path:
    """Path to session file: data/local/session/<session_id>.json."""
    return get_sessions_dir(repo_root) / f"{session_id}.json"


def get_current_session_id_path(repo_root: Path | str | None = None) -> Path:
    """Path to current session pointer: data/local/session/current_session_id.json."""
    return get_sessions_dir(repo_root) / CURRENT_SESSION_FILE


def save_session(session: Session, repo_root: Path | str | None = None) -> Path:
    """Persist session to data/local/session/<session_id>.json. Sets updated_at if open."""
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.utils.dates import utc_now_iso
    except Exception:
        from datetime import datetime, timezone
        def utc_now_iso() -> str:
            return datetime.now(timezone.utc).isoformat()
    if session.state == "open":
        session.updated_at = utc_now_iso()
    path = get_session_path(session.session_id, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
    return path


def load_session(session_id: str, repo_root: Path | str | None = None) -> Session | None:
    """Load session by id. Returns None if not found or invalid."""
    path = get_session_path(session_id, repo_root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Session.from_dict(data)
    except Exception:
        return None


def load_current_session_id(repo_root: Path | str | None = None) -> str | None:
    """Return current session id if set; else None."""
    path = get_current_session_id_path(repo_root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("session_id")
    except Exception:
        return None


def set_current_session_id(session_id: str | None, repo_root: Path | str | None = None) -> Path:
    """Set or clear current session pointer."""
    root = _repo_root(repo_root)
    path = get_current_session_id_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"session_id": session_id}, indent=2), encoding="utf-8")
    return path


def list_sessions(
    repo_root: Path | str | None = None,
    limit: int = 50,
    state_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    List sessions (metadata only). Most recent first.
    state_filter: optional 'open' | 'closed' | 'archived'.
    """
    root = _repo_root(repo_root)
    sessions_dir = get_sessions_dir(root)
    if not sessions_dir.exists():
        return []
    current_id = load_current_session_id(root)
    out = []
    for f in sorted(sessions_dir.iterdir(), key=lambda p: p.stat().st_mtime if p.is_file() else 0, reverse=True):
        if f.suffix != ".json" or f.name == CURRENT_SESSION_FILE:
            continue
        session_id = f.stem
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            state = data.get("state", "open")
            if state_filter and state != state_filter:
                continue
            out.append({
                "session_id": session_id,
                "value_pack_id": data.get("value_pack_id", ""),
                "state": state,
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "is_current": session_id == current_id,
            })
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out


def archive_session(session_id: str, repo_root: Path | str | None = None) -> bool:
    """Mark session as archived (state=archived). Returns True if session existed and was updated."""
    sess = load_session(session_id, repo_root)
    if not sess:
        return False
    sess.state = "archived"
    if not sess.closed_at:
        try:
            from workflow_dataset.utils.dates import utc_now_iso
        except Exception:
            from datetime import datetime, timezone
            def utc_now_iso() -> str:
                return datetime.now(timezone.utc).isoformat()
        sess.closed_at = utc_now_iso()
    save_session(sess, repo_root)
    if load_current_session_id(repo_root) == session_id:
        set_current_session_id(None, repo_root)
    return True
