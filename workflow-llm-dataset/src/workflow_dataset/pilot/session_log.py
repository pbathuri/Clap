"""
M21: Pilot session tracking — start/end session, persist locally, list sessions.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from workflow_dataset.pilot.session_models import PilotSessionRecord
from workflow_dataset.utils.dates import utc_now_iso

DEFAULT_PILOT_DIR = Path("data/local/pilot")
SESSIONS_SUBDIR = "sessions"
CURRENT_SESSION_FILE = "current_session.json"


def _sessions_dir(pilot_dir: Path | str | None = None) -> Path:
    root = Path(pilot_dir) if pilot_dir else DEFAULT_PILOT_DIR
    d = root / SESSIONS_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _current_session_path(pilot_dir: Path | str | None = None) -> Path:
    root = Path(pilot_dir) if pilot_dir else DEFAULT_PILOT_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root / CURRENT_SESSION_FILE


def start_session(
    operator: str = "",
    pilot_scope: str = "ops",
    task_type: str = "",
    config_path: str = "configs/settings.yaml",
    release_config_path: str = "configs/release_narrow.yaml",
    adapter_mode: str = "adapter",
    degraded_mode: bool = False,
    pilot_dir: Path | str | None = None,
) -> PilotSessionRecord:
    """Create and persist a new pilot session; set as current. Returns the session record."""
    session_id = f"pilot_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    record = PilotSessionRecord(
        session_id=session_id,
        timestamp_start=utc_now_iso(),
        timestamp_end="",
        operator=operator,
        pilot_scope=pilot_scope,
        task_type=task_type,
        config_path=config_path,
        release_config_path=release_config_path,
        adapter_mode=adapter_mode,
        degraded_mode=degraded_mode,
    )
    sessions_dir = _sessions_dir(pilot_dir)
    path = sessions_dir / f"{session_id}.json"
    path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
    current_path = _current_session_path(pilot_dir)
    current_path.write_text(json.dumps({"session_id": session_id}, indent=2), encoding="utf-8")
    return record


def get_current_session_id(pilot_dir: Path | str | None = None) -> str:
    """Return current session id or empty."""
    path = _current_session_path(pilot_dir)
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("session_id", "")
    except Exception:
        return ""


def load_session(session_id: str, pilot_dir: Path | str | None = None) -> PilotSessionRecord | None:
    """Load a session record by id."""
    sessions_dir = _sessions_dir(pilot_dir)
    path = sessions_dir / f"{session_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return PilotSessionRecord.from_dict(data)
    except Exception:
        return None


def save_session(record: PilotSessionRecord, pilot_dir: Path | str | None = None) -> Path:
    """Persist session record. Returns path to session file."""
    sessions_dir = _sessions_dir(pilot_dir)
    path = sessions_dir / f"{record.session_id}.json"
    path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
    return path


def end_session(
    session_id: str | None = None,
    operator_notes: str = "",
    disposition: str = "",
    pilot_dir: Path | str | None = None,
) -> PilotSessionRecord | None:
    """Finalize session: set timestamp_end, notes, disposition; clear current."""
    sid = session_id or get_current_session_id(pilot_dir)
    if not sid:
        return None
    record = load_session(sid, pilot_dir)
    if not record:
        return None
    record.timestamp_end = utc_now_iso()
    if operator_notes:
        record.operator_notes = operator_notes
    if disposition:
        record.disposition = disposition
    save_session(record, pilot_dir)
    current_path = _current_session_path(pilot_dir)
    if current_path.exists():
        try:
            data = json.loads(current_path.read_text(encoding="utf-8"))
            if data.get("session_id") == sid:
                current_path.unlink()
        except Exception:
            pass
    return record


def append_session_commands(session_id: str | None, commands: list[str], pilot_dir: Path | str | None = None) -> None:
    """Append commands run to session (e.g. release run, pilot verify)."""
    sid = session_id or get_current_session_id(pilot_dir)
    if not sid:
        return
    record = load_session(sid, pilot_dir)
    if not record:
        return
    for c in commands:
        if c and c not in record.commands_run:
            record.commands_run.append(c)
    save_session(record, pilot_dir)


def append_session_blocking(session_id: str | None, issues: list[str], pilot_dir: Path | str | None = None) -> None:
    """Append blocking issues encountered."""
    sid = session_id or get_current_session_id(pilot_dir)
    if not sid:
        return
    record = load_session(sid, pilot_dir)
    if not record:
        return
    for i in issues:
        if i and i not in record.blocking_issues:
            record.blocking_issues.append(i)
    save_session(record, pilot_dir)


def append_session_warnings(session_id: str | None, warnings: list[str], pilot_dir: Path | str | None = None) -> None:
    """Append warnings encountered."""
    sid = session_id or get_current_session_id(pilot_dir)
    if not sid:
        return
    record = load_session(sid, pilot_dir)
    if not record:
        return
    for w in warnings:
        if w and w not in record.warnings:
            record.warnings.append(w)
    save_session(record, pilot_dir)


def list_sessions(pilot_dir: Path | str | None = None, limit: int = 50) -> list[PilotSessionRecord]:
    """List recent sessions (newest first)."""
    sessions_dir = _sessions_dir(pilot_dir)
    paths = sorted(sessions_dir.glob("pilot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[PilotSessionRecord] = []
    for p in paths[:limit]:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append(PilotSessionRecord.from_dict(data))
        except Exception:
            continue
    return out


def get_latest_session(pilot_dir: Path | str | None = None) -> PilotSessionRecord | None:
    """Return the most recent session by mtime."""
    sessions = list_sessions(pilot_dir, limit=1)
    return sessions[0] if sessions else None


def record_workflow_artifact(
    workflow_type: str,
    dir_path: Path | str,
    pilot_dir: Path | str | None = None,
    template_id: str | None = None,
) -> None:
    """
    Record a workflow artifact (saved run dir) in the current pilot session.
    Appends dir path to artifacts_produced; if template_id is set, stores in session extra.
    No-op if no current session.
    """
    sid = get_current_session_id(pilot_dir)
    if not sid:
        return
    record = load_session(sid, pilot_dir)
    if not record:
        return
    path_str = str(Path(dir_path).resolve())
    if path_str not in record.artifacts_produced:
        record.artifacts_produced.append(path_str)
    if template_id and str(template_id).strip():
        if not isinstance(record.extra, dict):
            record.extra = {}
        record.extra["template_id"] = str(template_id).strip()
    save_session(record, pilot_dir)
