"""
M22D: Intake registration and snapshot. Register local paths, snapshot into sandbox, never mutate originals.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

INTAKE_ROOT = "data/local/intake"
INPUT_TYPES = ("notes", "docs", "spreadsheets", "exported_repos", "meeting_fragments", "mixed")
ALLOWED_EXTENSIONS = (".md", ".txt", ".csv", ".json", ".yaml", ".yml")
MAX_SNAPSHOT_FILES = 200
MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MiB per file


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def _load_registry(repo_root: Path) -> dict[str, Any]:
    reg_path = repo_root / INTAKE_ROOT / "registry.json"
    if not reg_path.exists():
        return {"sets": {}, "version": 1}
    try:
        data = json.loads(reg_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and "sets" in data else {"sets": {}, "version": 1}
    except Exception:
        return {"sets": {}, "version": 1}


def _save_registry(repo_root: Path, data: dict[str, Any]) -> Path:
    reg_dir = repo_root / INTAKE_ROOT
    reg_dir.mkdir(parents=True, exist_ok=True)
    reg_path = reg_dir / "registry.json"
    reg_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return reg_path


def _safe_label(label: str) -> str:
    return "".join(c for c in (label or "").strip() if c.isalnum() or c in "_-").strip() or "unnamed"


def _copy_into_snapshot(
    source: Path,
    dest_dir: Path,
    recursive: bool = True,
) -> list[str]:
    """Copy allowed files from source (file or dir) into dest_dir. Returns list of relative paths copied."""
    copied: list[str] = []
    source = source.resolve()
    if not source.exists():
        return copied
    if source.is_file():
        if source.suffix.lower() in ALLOWED_EXTENSIONS and source.stat().st_size <= MAX_FILE_BYTES:
            dest = dest_dir / source.name
            shutil.copy2(source, dest)
            copied.append(source.name)
        return copied
    # Directory: walk files (recursive or flat)
    count = 0
    it = source.rglob("*") if recursive else source.iterdir()
    for p in sorted(it, key=lambda x: str(x)):
        if count >= MAX_SNAPSHOT_FILES:
            break
        if not p.is_file() or p.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        if p.stat().st_size > MAX_FILE_BYTES:
            continue
        try:
            rel = p.relative_to(source)
        except ValueError:
            continue
        dest = dest_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        copied.append(str(rel))
        count += 1
    return copied[:MAX_SNAPSHOT_FILES]


def add_intake(
    label: str,
    paths: list[str | Path],
    input_type: str = "mixed",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Register paths and snapshot them into data/local/intake/<label>/<ts_id>/.
    Never mutates originals. Returns the new registry entry.
    """
    root = _repo_root(repo_root)
    label = _safe_label(label)
    if not label:
        raise ValueError("label is required")
    if input_type not in INPUT_TYPES:
        input_type = "mixed"
    reg = _load_registry(root)
    sets = reg.get("sets") or {}
    intake_root = root / INTAKE_ROOT
    intake_root.mkdir(parents=True, exist_ok=True)
    label_dir = intake_root / label
    label_dir.mkdir(parents=True, exist_ok=True)
    from workflow_dataset.utils.dates import utc_now_iso
    from workflow_dataset.utils.hashes import stable_id
    ts = utc_now_iso()[:19].replace(":", "").replace("-", "")[:14]
    sid = stable_id("intake", label, ts, prefix="")[:8]
    snapshot_name = f"{ts}_{sid}"
    snapshot_path = label_dir / snapshot_name
    snapshot_path.mkdir(parents=True, exist_ok=True)
    source_paths_resolved: list[str] = []
    all_copied: list[str] = []
    for p in paths:
        pp = Path(p).resolve()
        if not pp.exists():
            continue
        source_paths_resolved.append(str(pp))
        copied = _copy_into_snapshot(pp, snapshot_path, recursive=True)
        for c in copied:
            if c not in all_copied:
                all_copied.append(c)
    entry: dict[str, Any] = {
        "label": label,
        "source_paths": source_paths_resolved,
        "snapshot_dir": f"{label}/{snapshot_name}",
        "snapshot_path": str(snapshot_path),
        "input_type": input_type,
        "created_at": utc_now_iso(),
        "file_count": len(all_copied),
        "files": all_copied[:50],
    }
    sets[label] = entry
    reg["sets"] = sets
    _save_registry(root, reg)
    return entry


def get_intake(label: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Return registry entry for label, or None."""
    root = _repo_root(repo_root)
    label = _safe_label(label)
    reg = _load_registry(root)
    return (reg.get("sets") or {}).get(label)


def list_intakes(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List all registered intake sets (label, input_type, snapshot_dir, file_count, created_at)."""
    root = _repo_root(repo_root)
    reg = _load_registry(root)
    sets = reg.get("sets") or {}
    return [
        {
            "label": v.get("label"),
            "input_type": v.get("input_type", "mixed"),
            "snapshot_dir": v.get("snapshot_dir"),
            "file_count": v.get("file_count", 0),
            "created_at": v.get("created_at"),
        }
        for v in sets.values()
    ]
