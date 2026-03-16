"""
M23M: Persist and list correction events. data/local/corrections/events.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.corrections.config import get_events_dir
from workflow_dataset.corrections.schema import CorrectionEvent


def _event_path(correction_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in correction_id.strip())
    return get_events_dir(repo_root) / f"{safe}.json"


def save_correction(event: CorrectionEvent, repo_root: Path | str | None = None) -> Path:
    path = _event_path(event.correction_id, repo_root)
    path.write_text(json.dumps(event.to_dict(), indent=2), encoding="utf-8")
    return path


def get_correction(correction_id: str, repo_root: Path | str | None = None) -> CorrectionEvent | None:
    path = _event_path(correction_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return CorrectionEvent.from_dict(data)
    except Exception:
        return None


def list_corrections(
    limit: int = 50,
    repo_root: Path | str | None = None,
    source_type: str | None = None,
    category: str | None = None,
    eligible_only: bool = False,
) -> list[CorrectionEvent]:
    """List corrections newest first. Optional filter by source_type, category, eligible_for_memory_update."""
    events_dir = get_events_dir(repo_root)
    out: list[CorrectionEvent] = []
    for f in sorted(events_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.suffix != ".json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            ev = CorrectionEvent.from_dict(data)
            if source_type and ev.source_type != source_type:
                continue
            if category and ev.correction_category != category:
                continue
            if eligible_only and not ev.eligible_for_memory_update:
                continue
            out.append(ev)
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out
