"""
Resumable scan scheduling for setup inventory stage.

Yields batches of file paths from scan roots with checkpoints so long runs can resume.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from workflow_dataset.setup.setup_models import ScanScope


# Default exclusions aligned with observe/file_activity
DEFAULT_EXCLUDE = {".git", "__pycache__", "node_modules", ".venv", ".tox", "venv"}


def iter_scan_paths(
    scope: ScanScope,
    checkpoint_path: str | Path | None = None,
    batch_size: int = 500,
    max_files: int = 0,
) -> Iterator[list[Path]]:
    """
    Yield batches of file Paths under scope.root_paths. Respects exclude_dirs,
    max_file_size_bytes, allowed_extensions, max_files. When checkpoint_path is set,
    state is read for resume and written after each batch.
    """
    roots = [Path(p).resolve() for p in scope.root_paths if p]
    exclude = set(scope.exclude_dirs or DEFAULT_EXCLUDE)
    max_size = scope.max_file_size_bytes or (50 * 1024 * 1024)
    max_files_per_scan = max_files or scope.max_files_per_scan
    allowed_ext = set(e.lstrip(".").lower() for e in (scope.allowed_extensions or [])) if scope.allowed_extensions else None

    checkpoint: dict[str, str | int] = {}
    if checkpoint_path and Path(checkpoint_path).exists():
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
        except (json.JSONDecodeError, OSError):
            checkpoint = {}
    last_path = checkpoint.get("last_path", "")
    count_so_far = int(checkpoint.get("count", 0))
    if count_so_far >= max_files_per_scan and max_files_per_scan > 0:
        return

    batch: list[Path] = []
    seen: set[str] = set()

    def accept(p: Path) -> bool:
        if p.is_dir():
            return False
        if p.name in exclude:
            return False
        if last_path and str(p) <= last_path:
            return False
        try:
            if p.stat().st_size > max_size:
                return False
        except OSError:
            return False
        if allowed_ext is not None and allowed_ext:
            if p.suffix.lstrip(".").lower() not in allowed_ext:
                return False
        return True

    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        try:
            for entry in root.rglob("*"):
                if entry.is_dir():
                    if entry.name in exclude:
                        continue
                    continue
                if count_so_far >= max_files_per_scan and max_files_per_scan > 0:
                    if batch:
                        yield batch
                    return
                if str(entry) in seen:
                    continue
                if not accept(entry):
                    continue
                seen.add(str(entry))
                batch.append(entry)
                count_so_far += 1
                if len(batch) >= batch_size:
                    next_check = str(entry)
                    yield batch
                    batch = []
                    if checkpoint_path:
                        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(checkpoint_path, "w", encoding="utf-8") as f:
                            json.dump({"last_path": next_check, "count": count_so_far}, f)
        except OSError:
            continue
    if batch:
        yield batch
