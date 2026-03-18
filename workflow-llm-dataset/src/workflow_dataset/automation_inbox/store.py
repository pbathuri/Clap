"""
M34I–M34L: Persist automation inbox decisions and optional item snapshot. Local only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = "data/local/automation_inbox"
DECISIONS_FILE = "decisions.json"
NOTES_FILE = "operator_notes.json"
DIGESTS_SUBDIR = "digests"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_automation_inbox_root(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / ROOT_DIR


def _load_json_list(path: Path, key: str = "items", default: list[Any] | None = None) -> list[Any]:
    if default is None:
        default = []
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        out = data.get(key, default)
        return list(out) if isinstance(out, list) else default
    except Exception:
        return default


def _save_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def save_decision(
    item_id: str,
    decision: str,  # accepted | archived | dismissed | escalated
    note: str = "",
    repo_root: Path | str | None = None,
) -> Path:
    """Record a decision for an automation inbox item (accept/archive/dismiss/escalate)."""
    try:
        from workflow_dataset.utils.dates import utc_now_iso
    except Exception:
        from datetime import datetime, timezone
        def utc_now_iso() -> str:
            return datetime.now(timezone.utc).isoformat()

    root = get_automation_inbox_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / DECISIONS_FILE
    entries: list[dict[str, Any]] = _load_json_list(path, "decisions", [])
    entries.insert(0, {
        "item_id": item_id,
        "decision": decision,
        "note": note,
        "decided_at": utc_now_iso(),
    })
    _save_json(path, {"decisions": entries[:500]})
    return path


def list_decisions(
    item_id: str | None = None,
    limit: int = 50,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List decisions, optionally filtered by item_id."""
    root = get_automation_inbox_root(repo_root)
    path = root / DECISIONS_FILE
    entries = _load_json_list(path, "decisions", [])
    if item_id:
        entries = [e for e in entries if isinstance(e, dict) and e.get("item_id") == item_id]
    return entries[:limit]


def get_latest_decision(item_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Get the most recent decision for an item, if any."""
    entries = list_decisions(item_id=item_id, limit=1, repo_root=repo_root)
    return entries[0] if entries else None


def save_operator_note(item_id: str, note: str, repo_root: Path | str | None = None) -> Path:
    """Store operator note for an automation inbox item."""
    root = get_automation_inbox_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / NOTES_FILE
    notes: dict[str, str] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            notes = dict(data.get("notes", {}))
        except Exception:
            pass
    notes[item_id] = note
    _save_json(path, {"notes": notes})
    return path


def load_operator_notes(repo_root: Path | str | None = None) -> dict[str, str]:
    """Load all operator notes for automation inbox items."""
    path = get_automation_inbox_root(repo_root) / NOTES_FILE
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return dict(data.get("notes", {}))
    except Exception:
        return {}


def save_digest_snapshot(digest: Any, repo_root: Path | str | None = None) -> Path:
    """Save a recurring digest snapshot for latest/compare."""
    root = get_automation_inbox_root(repo_root) / DIGESTS_SUBDIR
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{getattr(digest, 'digest_id', None) or 'latest'}.json"
    _save_json(path, digest.to_dict() if hasattr(digest, "to_dict") else digest)
    return path


def load_digest_snapshot(digest_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load a digest snapshot by id (e.g. 'latest')."""
    path = get_automation_inbox_root(repo_root) / DIGESTS_SUBDIR / f"{digest_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# M34L.1 Briefs and continuity cards
BRIEFS_SUBDIR = "briefs"


def save_brief_snapshot(brief: Any, repo_root: Path | str | None = None) -> Path:
    """Save morning brief or continuity card snapshot (e.g. latest)."""
    root = get_automation_inbox_root(repo_root) / BRIEFS_SUBDIR
    root.mkdir(parents=True, exist_ok=True)
    key = getattr(brief, "brief_id", None) or getattr(brief, "card_id", None) or "latest"
    path = root / f"{key}.json"
    _save_json(path, brief.to_dict() if hasattr(brief, "to_dict") else brief)
    return path


def load_brief_snapshot(key: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load brief/card snapshot by key (e.g. 'latest', brief_id, card_id)."""
    path = get_automation_inbox_root(repo_root) / BRIEFS_SUBDIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
