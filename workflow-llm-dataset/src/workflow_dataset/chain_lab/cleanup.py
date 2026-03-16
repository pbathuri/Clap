"""
M23A-F5: Chain run cleanup and archive — list old runs, archive by run_id, optional cleanup by age.
All operations local; never deletes chain definitions. Archive moves run dir to runs/archive/<run_id>/.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from workflow_dataset.chain_lab.config import get_runs_dir
from workflow_dataset.chain_lab.manifest import load_run_manifest, RUN_MANIFEST_FILENAME

ARCHIVE_SUBDIR = "archive"


def _parse_iso_to_utc(iso_str: str | None) -> datetime | None:
    """Parse started_at/ended_at ISO string to UTC datetime."""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def list_runs_with_meta(
    repo_root: Path | str | None = None,
    limit: int = 100,
    skip_archived: bool = True,
) -> list[dict[str, Any]]:
    """
    List runs with metadata: run_id, chain_id, status, started_at, mtime.
    Only includes direct children of runs_dir (skips archive/ if skip_archived).
    """
    runs_dir = get_runs_dir(repo_root)
    if not runs_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for p in runs_dir.iterdir():
        if not p.is_dir():
            continue
        if skip_archived and p.name == ARCHIVE_SUBDIR:
            continue
        manifest_path = p / RUN_MANIFEST_FILENAME
        if not manifest_path.exists():
            continue
        mtime = manifest_path.stat().st_mtime
        manifest = load_run_manifest(p.name, repo_root)
        if manifest:
            out.append({
                "run_id": p.name,
                "chain_id": manifest.get("chain_id", ""),
                "status": manifest.get("status", ""),
                "started_at": manifest.get("started_at"),
                "ended_at": manifest.get("ended_at"),
                "mtime": mtime,
            })
        else:
            out.append({"run_id": p.name, "chain_id": "", "status": "?", "started_at": None, "ended_at": None, "mtime": mtime})
    out.sort(key=lambda x: x.get("mtime") or 0, reverse=True)
    return out[:limit]


def list_runs_older_than(
    repo_root: Path | str | None = None,
    days: float = 30,
    limit: int = 200,
) -> list[str]:
    """
    Return run_ids of runs older than the given number of days.
    Age is based on started_at from manifest if present, else mtime of run_manifest.json.
    """
    runs = list_runs_with_meta(repo_root=repo_root, limit=limit)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out: list[str] = []
    for r in runs:
        started = _parse_iso_to_utc(r.get("started_at"))
        if started is not None:
            if started < cutoff:
                out.append(r["run_id"])
        else:
            mtime = r.get("mtime")
            if mtime:
                mt = datetime.fromtimestamp(mtime, tz=timezone.utc)
                if mt < cutoff:
                    out.append(r["run_id"])
    return out


def archive_run(run_id: str, repo_root: Path | str | None = None) -> Path:
    """
    Move run directory to runs/archive/<run_id>. Creates archive dir if needed.
    Returns path to archived run directory.
    """
    runs_dir = get_runs_dir(repo_root)
    run_dir = runs_dir / run_id
    if not run_dir.exists() or not run_dir.is_dir():
        raise FileNotFoundError(f"Run not found: {run_id}")
    archive_dir = runs_dir / ARCHIVE_SUBDIR
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / run_id
    if dest.exists():
        shutil.rmtree(dest)
    shutil.move(str(run_dir), str(dest))
    return dest


def cleanup_older_runs(
    repo_root: Path | str | None = None,
    older_than_days: float = 30,
    dry_run: bool = True,
    archive: bool = False,
) -> dict[str, Any]:
    """
    List runs older than N days; if not dry_run and archive=True, archive them.
    Returns {"run_ids": [...], "archived": [...], "dry_run": bool}.
    """
    run_ids = list_runs_older_than(repo_root=repo_root, days=older_than_days)
    result: dict[str, Any] = {"run_ids": run_ids, "archived": [], "dry_run": dry_run}
    if dry_run or not archive:
        return result
    for rid in run_ids:
        try:
            archive_run(rid, repo_root)
            result["archived"].append(rid)
        except Exception:
            continue
    return result
