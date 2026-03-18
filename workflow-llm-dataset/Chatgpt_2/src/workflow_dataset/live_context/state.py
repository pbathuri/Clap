"""
Live context state persistence (M32).

Read/write current context and recent transitions under data/local/live_context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.live_context.models import ActiveWorkContext, SessionTransitionEvent


def _live_context_dir(base: Path | str | None = None) -> Path:
    if base is None:
        return Path("data/local/live_context")
    return Path(base) / "live_context"


def get_live_context_state_dir(repo_root: Path | str | None = None) -> Path:
    """Directory for live context state and transitions."""
    d = _live_context_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_live_context_state(repo_root: Path | str | None = None) -> ActiveWorkContext | None:
    """Load current context from data/local/live_context/current.json."""
    d = get_live_context_state_dir(repo_root)
    path = d / "current.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ActiveWorkContext.model_validate(data)
    except Exception:
        return None


def save_live_context_state(context: ActiveWorkContext, repo_root: Path | str | None = None) -> Path:
    """Save current context to current.json. Returns path written."""
    d = get_live_context_state_dir(repo_root)
    path = d / "current.json"
    path.write_text(context.model_dump_json(indent=2), encoding="utf-8")
    return path


def get_recent_transitions(repo_root: Path | str | None = None, limit: int = 20) -> list[SessionTransitionEvent]:
    """Load recent transitions from transitions.jsonl (newest first)."""
    d = get_live_context_state_dir(repo_root)
    path = d / "transitions.jsonl"
    if not path.exists():
        return []
    out: list[SessionTransitionEvent] = []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    for line in reversed(lines[-limit:]):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            out.append(SessionTransitionEvent.model_validate(data))
        except Exception:
            continue
    return out[:limit]


def append_transition(transition: SessionTransitionEvent, repo_root: Path | str | None = None) -> Path:
    """Append one transition to transitions.jsonl. Returns path written."""
    d = get_live_context_state_dir(repo_root)
    path = d / "transitions.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(transition.model_dump_json() + "\n")
    return path
