"""
M24J–M24M: Session artifact hub — persist session-scoped artifacts, notes, outputs, handoff.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.session.storage import get_sessions_dir

ARTIFACTS_FILE = "artifacts.json"
NOTES_FILE = "notes.json"
HANDOFF_FILE = "handoff.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _session_artifacts_dir(session_id: str, repo_root: Path | str | None = None) -> Path:
    """data/local/session/<session_id>/"""
    return get_sessions_dir(repo_root) / session_id


def _load_json_list(path: Path, default: list[Any]) -> list[Any]:
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else default
    except Exception:
        return default


def _save_json_list(path: Path, items: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")


def add_artifact(
    session_id: str,
    path_or_label: str,
    kind: str = "file",
    repo_root: Path | str | None = None,
) -> None:
    """Append an artifact (path or label) to the session's artifact list."""
    root = _repo_root(repo_root)
    dir_path = _session_artifacts_dir(session_id, root)
    path = dir_path / ARTIFACTS_FILE
    items = _load_json_list(path, [])
    items.append({"path_or_label": path_or_label, "kind": kind})
    _save_json_list(path, items)


def list_artifacts(
    session_id: str,
    repo_root: Path | str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Return session artifacts (path_or_label, kind). Most recent last; return last `limit`."""
    root = _repo_root(repo_root)
    path = _session_artifacts_dir(session_id, root) / ARTIFACTS_FILE
    items = _load_json_list(path, [])
    return items[-limit:] if len(items) > limit else items


def add_note(session_id: str, note: str, repo_root: Path | str | None = None) -> None:
    """Append a note to the session."""
    root = _repo_root(repo_root)
    dir_path = _session_artifacts_dir(session_id, root)
    path = dir_path / NOTES_FILE
    items = _load_json_list(path, [])
    items.append({"note": note})
    _save_json_list(path, items)


def get_notes(
    session_id: str,
    repo_root: Path | str | None = None,
    limit: int = 50,
) -> list[str]:
    """Return session notes (plain strings). Most recent last."""
    root = _repo_root(repo_root)
    path = _session_artifacts_dir(session_id, root) / NOTES_FILE
    items = _load_json_list(path, [])
    notes = [x.get("note", "") for x in items if isinstance(x, dict) and "note" in x]
    return notes[-limit:] if len(notes) > limit else notes


def add_output(
    session_id: str,
    label: str,
    path_or_content: str,
    repo_root: Path | str | None = None,
) -> None:
    """Record a generated output (label + path or content snippet) for the session."""
    root = _repo_root(repo_root)
    dir_path = _session_artifacts_dir(session_id, root)
    path = dir_path / ARTIFACTS_FILE
    items = _load_json_list(path, [])
    items.append({"path_or_label": path_or_content, "kind": "output", "label": label})
    _save_json_list(path, items)


def get_handoff(session_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Return handoff info for the session: summary, next_steps.
    Reads from data/local/session/<session_id>/handoff.json if present; else returns defaults.
    """
    root = _repo_root(repo_root)
    path = _session_artifacts_dir(session_id, root) / HANDOFF_FILE
    if not path.exists():
        return {"summary": "", "next_steps": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "summary": data.get("summary", ""),
            "next_steps": list(data.get("next_steps", [])),
        }
    except Exception:
        return {"summary": "", "next_steps": []}


def set_handoff(
    session_id: str,
    summary: str = "",
    next_steps: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> None:
    """Write handoff summary and next_steps for the session."""
    root = _repo_root(repo_root)
    dir_path = _session_artifacts_dir(session_id, root)
    path = dir_path / HANDOFF_FILE
    dir_path.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"summary": summary or "", "next_steps": next_steps or []}, indent=2),
        encoding="utf-8",
    )
