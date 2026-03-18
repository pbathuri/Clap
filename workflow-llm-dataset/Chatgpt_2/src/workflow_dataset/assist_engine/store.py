"""
M32E–M32H: Persist and load assist suggestions. Local-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.assist_engine.models import AssistSuggestion
from workflow_dataset.utils.dates import utc_now_iso


ASSIST_ENGINE_DIR = Path("data/local/assist_engine")
QUEUE_FILE = "queue.json"
MAX_QUEUE_SIZE = 100


def _assist_root(repo_root: Path | str | None) -> Path:
    return get_assist_engine_root(repo_root)


def get_assist_engine_root(repo_root: Path | str | None = None) -> Path:
    """Root directory for assist engine data (queue, policy)."""
    if repo_root is not None:
        return Path(repo_root).resolve() / ASSIST_ENGINE_DIR
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve() / ASSIST_ENGINE_DIR
    except Exception:
        return Path.cwd().resolve() / ASSIST_ENGINE_DIR


def _load_all(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    root = _assist_root(repo_root)
    path = root / QUEUE_FILE
    if not path.exists():
        return []
    try:
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw) if raw.strip() else []
    except Exception:
        return []


def _save_all(items: list[dict[str, Any]], repo_root: Path | str | None = None) -> None:
    root = _assist_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / QUEUE_FILE
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")


def save_suggestion(suggestion: AssistSuggestion, repo_root: Path | str | None = None) -> None:
    """Append or replace suggestion by id; trim queue if over MAX_QUEUE_SIZE."""
    items = _load_all(repo_root)
    now = utc_now_iso()
    d = suggestion.to_dict()
    d["updated_utc"] = now
    existing = [i for i in items if i.get("suggestion_id") == suggestion.suggestion_id]
    if existing:
        items = [i for i in items if i.get("suggestion_id") != suggestion.suggestion_id]
    items.append(d)
    if len(items) > MAX_QUEUE_SIZE:
        # Keep most recent by updated_utc
        items.sort(key=lambda x: x.get("updated_utc", x.get("created_utc", "")), reverse=True)
        items = items[:MAX_QUEUE_SIZE]
    _save_all(items, repo_root)


def load_suggestion(suggestion_id: str, repo_root: Path | str | None = None) -> AssistSuggestion | None:
    """Load one suggestion by id."""
    for d in _load_all(repo_root):
        if d.get("suggestion_id") == suggestion_id:
            return AssistSuggestion.from_dict(d)
    return None


def list_suggestions(
    repo_root: Path | str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[AssistSuggestion]:
    """List suggestions; optional filter by status (pending, snoozed, accepted, dismissed)."""
    items = _load_all(repo_root)
    if status_filter:
        items = [i for i in items if i.get("status") == status_filter]
    out: list[AssistSuggestion] = []
    for d in items[:limit]:
        try:
            out.append(AssistSuggestion.from_dict(d))
        except Exception:
            continue
    return out


def update_status(
    suggestion_id: str,
    status: str,
    repo_root: Path | str | None = None,
    snoozed_until_utc: str | None = None,
) -> bool:
    """Update suggestion status; return True if found and updated."""
    items = _load_all(repo_root)
    for i in items:
        if i.get("suggestion_id") == suggestion_id:
            i["status"] = status
            i["updated_utc"] = utc_now_iso()
            if snoozed_until_utc is not None:
                i["snoozed_until_utc"] = snoozed_until_utc
            _save_all(items, repo_root)
            return True
    return False


def list_dismissed_patterns(
    repo_root: Path | str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Recent dismissed suggestions for repeat suppression: [{suggestion_type, reason_title, dismissed_utc}]."""
    items = [i for i in _load_all(repo_root) if i.get("status") == "dismissed"]
    items.sort(key=lambda x: x.get("updated_utc", ""), reverse=True)
    out = []
    for i in items[:limit]:
        reason = i.get("reason") or {}
        if isinstance(reason, dict):
            title = reason.get("title", "")
        else:
            title = getattr(reason, "title", "")
        out.append({
            "suggestion_type": i.get("suggestion_type", ""),
            "reason_title": title,
            "dismissed_utc": i.get("updated_utc", i.get("created_utc", "")),
        })
    return out
