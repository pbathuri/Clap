"""
M23C-F2: File/folder adapter execution. Read-only + copy to sandbox only; no mutation of originals.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class InspectResult:
    exists: bool
    is_file: bool
    is_dir: bool
    size_bytes: int | None = None
    mtime_iso: str | None = None
    error: str | None = None


@dataclass
class ListDirectoryResult:
    entries: list[dict[str, Any]]
    error: str | None = None


@dataclass
class SnapshotResult:
    sandbox_path: str
    copied_count: int
    error: str | None = None


def run_inspect_path(path: str | Path) -> InspectResult:
    """Inspect path metadata. Read-only; no writes."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return InspectResult(exists=False, is_file=False, is_dir=False, error="path_not_found")
    try:
        stat = p.stat()
        mtime_iso = None
        try:
            import datetime
            mtime_iso = datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat()
        except Exception:
            pass
        size = stat.st_size if p.is_file() else None
        return InspectResult(
            exists=True,
            is_file=p.is_file(),
            is_dir=p.is_dir(),
            size_bytes=size,
            mtime_iso=mtime_iso,
        )
    except OSError as e:
        return InspectResult(exists=True, is_file=False, is_dir=False, error=f"permission_denied: {e!s}")


def run_list_directory(path: str | Path) -> ListDirectoryResult:
    """List directory entries (name, type). Read-only."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return ListDirectoryResult(entries=[], error="path_not_found")
    if not p.is_dir():
        return ListDirectoryResult(entries=[], error="not_a_directory")
    try:
        entries: list[dict[str, Any]] = []
        for child in sorted(p.iterdir()):
            entries.append({
                "name": child.name,
                "is_file": child.is_file(),
                "is_dir": child.is_dir(),
            })
        return ListDirectoryResult(entries=entries)
    except OSError as e:
        return ListDirectoryResult(entries=[], error=f"permission_denied: {e!s}")


def run_snapshot_to_sandbox(
    source_path: str | Path,
    sandbox_root: Path,
    subdir: str | None = None,
) -> SnapshotResult:
    """Copy file or directory into sandbox. Originals unchanged. Writes only under sandbox_root."""
    src = Path(source_path).expanduser().resolve()
    if not src.exists():
        return SnapshotResult(sandbox_path="", copied_count=0, error="path_not_found")
    sandbox_root = Path(sandbox_root).resolve()
    try:
        dest_dir = sandbox_root
        if subdir:
            dest_dir = sandbox_root / subdir.strip().strip("/")
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        if src.is_file():
            shutil.copy2(src, dest)
            return SnapshotResult(sandbox_path=str(dest), copied_count=1)
        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=False)
            count = sum(1 for _ in dest.rglob("*") if _.is_file())
            return SnapshotResult(sandbox_path=str(dest), copied_count=count)
        return SnapshotResult(sandbox_path="", copied_count=0, error="unsupported_type")
    except OSError as e:
        return SnapshotResult(sandbox_path="", copied_count=0, error=f"copy_failed: {e!s}")
