"""
M19: Current trial session id and alias (local file).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _session_path(store_path: Path | str | None) -> Path:
    base = Path(store_path) if store_path else Path("data/local/trials")
    base.mkdir(parents=True, exist_ok=True)
    return base / "current_session.json"


def get_current_session(store_path: Path | str | None = None) -> dict[str, str]:
    """Return current session dict: session_id, user_alias, started_utc. Empty if none."""
    path = _session_path(store_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def set_current_session(
    session_id: str | None = None,
    user_alias: str = "",
    store_path: Path | str | None = None,
) -> dict[str, str]:
    """Set current trial session; generate session_id if not provided. Returns session dict."""
    sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
    data = {
        "session_id": sid,
        "user_alias": user_alias or "",
        "started_utc": datetime.now(timezone.utc).isoformat(),
    }
    path = _session_path(store_path)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def clear_current_session(store_path: Path | str | None = None) -> None:
    """Clear current session file."""
    path = _session_path(store_path)
    if path.exists():
        path.unlink()
