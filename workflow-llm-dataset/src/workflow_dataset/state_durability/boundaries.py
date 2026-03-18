"""
M37I–M37L: Persistence boundaries by subsystem — path, health check, last write.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.state_durability.models import (
    PersistenceBoundary,
    StaleStateMarker,
    CorruptedStateNote,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _mtime_iso(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        m = path.stat().st_mtime
        from datetime import datetime, timezone
        return datetime.fromtimestamp(m, tz=timezone.utc).isoformat()
    except Exception:
        return ""


def _check_json_read(path: Path) -> tuple[bool, str]:
    """Return (ok, error_summary)."""
    if not path.exists():
        return False, "missing"
    if not path.is_file():
        return False, "not_a_file"
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"invalid_json:{e.msg}"
    except Exception as e:
        return False, str(e)[:80]


SUBSYSTEM_BOUNDARIES: list[dict[str, Any]] = [
    {"id": "workday", "path": "data/local/workday/state.json", "critical": True},
    {"id": "continuity_shutdown", "path": "data/local/continuity_engine/last_shutdown.json", "critical": False},
    {"id": "continuity_carry_forward", "path": "data/local/continuity_engine/carry_forward.json", "critical": False},
    {"id": "continuity_next_session", "path": "data/local/continuity_engine/next_session.json", "critical": False},
    {"id": "project_current", "path": "data/local/project_case/current_project_id.json", "critical": False},
    {"id": "background_queue", "path": "data/local/background_run/queue.json", "critical": False},
    {"id": "workday_preset", "path": "data/local/workday/active_preset.txt", "critical": False},
]


def check_boundary(
    subsystem_id: str,
    path: Path,
    critical: bool,
    repo_root: Path | str | None,
) -> PersistenceBoundary:
    """Check one persistence boundary; return PersistenceBoundary with status."""
    root = _root(repo_root)
    full = root / path if not path.is_absolute() else path
    rel_path = str(path)
    last_write = _mtime_iso(full)

    if full.suffix == ".json":
        ok, err = _check_json_read(full)
        if ok:
            return PersistenceBoundary(
                subsystem_id=subsystem_id,
                path=rel_path,
                status="ok",
                last_write_utc=last_write,
                critical_for_startup=critical,
            )
        if not full.exists():
            return PersistenceBoundary(
                subsystem_id=subsystem_id,
                path=rel_path,
                status="missing",
                last_write_utc="",
                note="File not found",
                critical_for_startup=critical,
            )
        return PersistenceBoundary(
            subsystem_id=subsystem_id,
            path=rel_path,
            status="corrupt",
            last_write_utc=last_write,
            note=err or "load failed",
            critical_for_startup=critical,
        )

    # Plain file (e.g. .txt)
    if full.exists() and full.is_file():
        return PersistenceBoundary(
            subsystem_id=subsystem_id,
            path=rel_path,
            status="ok",
            last_write_utc=_mtime_iso(full),
            critical_for_startup=critical,
        )
    return PersistenceBoundary(
        subsystem_id=subsystem_id,
        path=rel_path,
        status="missing",
        note="File not found",
        critical_for_startup=critical,
    )


def collect_all_boundaries(repo_root: Path | str | None = None) -> list[PersistenceBoundary]:
    """Run health check for all registered subsystems; return list of PersistenceBoundary."""
    root = _root(repo_root)
    out: list[PersistenceBoundary] = []
    for b in SUBSYSTEM_BOUNDARIES:
        path = Path(b["path"])
        out.append(check_boundary(
            b["id"],
            path,
            b.get("critical", True),
            root,
        ))
    return out


def collect_stale_markers(
    repo_root: Path | str | None = None,
    stale_hours: float = 24.0,
) -> list[StaleStateMarker]:
    """Mark boundaries whose last_write is older than stale_hours."""
    boundaries = collect_all_boundaries(repo_root)
    root = _root(repo_root)
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=stale_hours)
    out: list[StaleStateMarker] = []
    for b in boundaries:
        if b.status != "ok" or not b.last_write_utc:
            continue
        try:
            ts = datetime.fromisoformat(b.last_write_utc.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < cutoff:
                out.append(StaleStateMarker(
                    subsystem_id=b.subsystem_id,
                    path=b.path,
                    last_write_utc=b.last_write_utc,
                    stale_threshold_hours=stale_hours,
                    recommended_action=f"Optional: refresh {b.subsystem_id} state or run continuity shutdown",
                ))
        except Exception:
            pass
    return out


def collect_corrupt_notes(
    repo_root: Path | str | None = None,
) -> list[CorruptedStateNote]:
    """Collect notes for boundaries that are corrupt or incomplete."""
    boundaries = collect_all_boundaries(repo_root)
    out: list[CorruptedStateNote] = []
    for b in boundaries:
        if b.status == "corrupt":
            out.append(CorruptedStateNote(
                subsystem_id=b.subsystem_id,
                path=b.path,
                error_summary=b.note or "load failed",
                recommended_action=f"Check {b.path}; restore from backup or re-run day start/continuity shutdown",
            ))
    return out
