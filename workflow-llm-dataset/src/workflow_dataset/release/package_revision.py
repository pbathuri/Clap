"""
M21T-F2: Revision lineage and package status (approved, needs_revision, superseded, archived).
Stored as revision_meta.json inside each package dir. Local-only; no apply.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso

REVISION_META_FILE = "revision_meta.json"
PACKAGE_STATUSES = ("approved", "needs_revision", "superseded", "archived")


def _revision_meta_path(package_path: str | Path) -> Path:
    return Path(package_path).resolve() / REVISION_META_FILE


def load_revision_meta(package_path: str | Path) -> dict[str, Any]:
    """
    Load revision metadata for a package. Returns dict with status, supersedes, superseded_by,
    revision_reason, revision_note, updated_at. Missing file returns defaults (status approved).
    """
    path = _revision_meta_path(package_path)
    if not path.exists():
        return {
            "status": "approved",
            "supersedes": None,
            "superseded_by": None,
            "revision_reason": "",
            "revision_note": "",
            "updated_at": None,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        status = data.get("status")
        if status not in PACKAGE_STATUSES:
            status = "approved"
        return {
            "status": status,
            "supersedes": data.get("supersedes"),
            "superseded_by": data.get("superseded_by"),
            "revision_reason": data.get("revision_reason") or "",
            "revision_note": data.get("revision_note") or "",
            "updated_at": data.get("updated_at"),
        }
    except Exception:
        return {
            "status": "approved",
            "supersedes": None,
            "superseded_by": None,
            "revision_reason": "",
            "revision_note": "",
            "updated_at": None,
        }


def save_revision_meta(
    package_path: str | Path,
    status: str | None = None,
    supersedes: str | None = None,
    superseded_by: str | None = None,
    revision_reason: str = "",
    revision_note: str = "",
    updated_at: str | None = None,
) -> Path:
    """
    Save revision metadata. Merges with existing; pass None for fields to keep unchanged.
    status must be in PACKAGE_STATUSES. Returns path to revision_meta.json.
    """
    path = _revision_meta_path(package_path)
    pkg_dir = path.parent
    if not pkg_dir.exists() or not pkg_dir.is_dir():
        raise FileNotFoundError(f"Package directory not found: {pkg_dir}")
    current = load_revision_meta(package_path)
    if status is not None:
        if status not in PACKAGE_STATUSES:
            raise ValueError(f"status must be one of {PACKAGE_STATUSES}")
        current["status"] = status
    if supersedes is not None:
        current["supersedes"] = supersedes
    if superseded_by is not None:
        current["superseded_by"] = superseded_by
    if revision_reason is not None:
        current["revision_reason"] = (revision_reason or "").strip()
    if revision_note is not None:
        current["revision_note"] = (revision_note or "").strip()
    current["updated_at"] = updated_at or utc_now_iso()
    path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return path


def set_supersedes(
    package_b_path: str | Path,
    package_a_path: str | Path,
    reason: str = "",
    note: str = "",
    repo_root: Path | None = None,
) -> None:
    """
    Record that package B supersedes package A. Writes revision_meta in both dirs:
    - B: supersedes = A path, status unchanged (or approved), revision_reason, revision_note
    - A: superseded_by = B path, status = superseded
    Does not mutate package contents; only revision_meta.json.
    """
    pa = Path(package_a_path).resolve()
    pb = Path(package_b_path).resolve()
    if not pa.is_dir() or not pb.is_dir():
        raise FileNotFoundError(f"Package dir not found: {pa} or {pb}")
    a_path_str = str(pa)
    b_path_str = str(pb)
    now = utc_now_iso()
    save_revision_meta(
        pb,
        supersedes=a_path_str,
        revision_reason=reason,
        revision_note=note,
        updated_at=now,
    )
    save_revision_meta(
        pa,
        status="superseded",
        superseded_by=b_path_str,
        revision_reason=reason,
        revision_note=note,
        updated_at=now,
    )


def set_package_status(
    package_path: str | Path,
    status: str,
    note: str = "",
    repo_root: Path | None = None,
) -> Path:
    """Set package revision status (approved, needs_revision, superseded, archived). Returns revision_meta path."""
    return save_revision_meta(
        package_path,
        status=status,
        revision_note=note,
    )


def get_lineage(package_path: str | Path) -> dict[str, Any]:
    """
    Return lineage info for a package: revision_meta plus package dir name and path.
    Keys: path, name, status, supersedes, superseded_by, revision_reason, revision_note, updated_at.
    """
    p = Path(package_path).resolve()
    meta = load_revision_meta(p)
    return {
        "path": str(p),
        "name": p.name,
        "status": meta["status"],
        "supersedes": meta["supersedes"],
        "superseded_by": meta["superseded_by"],
        "revision_reason": meta["revision_reason"],
        "revision_note": meta["revision_note"],
        "updated_at": meta["updated_at"],
    }
