"""
M23M: Update history: list applied, list reverted.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.corrections.config import get_updates_dir
from workflow_dataset.corrections.updates import UpdateRecord


def list_applied_updates(
    limit: int = 30,
    repo_root: Path | str | None = None,
) -> list[UpdateRecord]:
    """List updates that have been applied (not reverted), newest first."""
    updates_dir = get_updates_dir(repo_root)
    out: list[UpdateRecord] = []
    for f in sorted(updates_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.suffix != ".json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            rec = UpdateRecord.from_dict(data)
            if rec.reverted_at:
                continue
            out.append(rec)
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out


def list_reverted_updates(
    limit: int = 30,
    repo_root: Path | str | None = None,
) -> list[UpdateRecord]:
    """List updates that have been reverted."""
    updates_dir = get_updates_dir(repo_root)
    out: list[UpdateRecord] = []
    for f in sorted(updates_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.suffix != ".json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            rec = UpdateRecord.from_dict(data)
            if not rec.reverted_at:
                continue
            out.append(rec)
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out
