"""
M23K: Reminders / schedule proposals. Explicit, local, no auto-run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.copilot.config import get_reminders_path


def _load_reminders(repo_root: Path | str | None) -> list[dict[str, Any]]:
    path = get_reminders_path(repo_root)
    if not path.exists() or not path.is_file():
        return []
    raw = path.read_text(encoding="utf-8")
    try:
        if yaml:
            data = yaml.safe_load(raw) or {}
        else:
            import json
            data = json.loads(raw) or {}
    except Exception:
        return []
    return list(data.get("reminders", data) if isinstance(data, dict) else data)


def _save_reminders(reminders: list[dict[str, Any]], repo_root: Path | str | None) -> Path:
    path = get_reminders_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"reminders": reminders}
    if yaml:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        import json
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def list_reminders(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List all reminders (no filtering by due)."""
    return _load_reminders(repo_root)


def add_reminder(
    routine_id: str | None = None,
    job_pack_id: str | None = None,
    due_at: str = "",
    title: str = "",
    one_off: bool = True,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Add a reminder. Either routine_id or job_pack_id. due_at is ISO or descriptive (e.g. morning). No auto-run."""
    reminders = _load_reminders(repo_root)
    rid = f"rem_{len(reminders)}_{utc_now_iso()}"[:30].replace(":", "-")
    entry = {
        "reminder_id": rid,
        "routine_id": routine_id or "",
        "job_pack_id": job_pack_id or "",
        "due_at": due_at or utc_now_iso(),
        "title": title or (routine_id or job_pack_id or "reminder"),
        "one_off": one_off,
        "created_at": utc_now_iso(),
    }
    reminders.append(entry)
    _save_reminders(reminders, repo_root)
    return entry


def reminders_due(repo_root: Path | str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Return reminders that are 'due' — for now we treat all as due (no real scheduling). Operator can use list and run manually."""
    all_r = list_reminders(repo_root)
    return all_r[:limit]
