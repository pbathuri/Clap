"""
Safe sandbox workspace manager for materialized outputs.

Creates per-session and per-request workspaces under local-only paths.
Never writes to the user's real directories.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _resolve_root(workspace_root: str | Path) -> Path:
    """Resolve workspace root. Use explicit path when given; default to data/local/workspaces for relative."""
    p = Path(workspace_root)
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    root = p.resolve()
    parts = root.parts
    # Safety: if relative input resolved outside any known safe base, use default
    if not Path(workspace_root).is_absolute() and "data" not in parts and "local" not in parts and "workspaces" not in parts:
        root = (Path.cwd() / "data/local/workspaces").resolve()
    return root


def create_workspace(
    workspace_root: str | Path,
    session_id: str = "",
    request_id: str = "",
    project_id: str = "",
) -> Path:
    """
    Create a sandbox workspace directory. Prefer per-request when request_id is set.
    Returns the absolute path to the workspace (only under workspace_root).
    """
    root = _resolve_root(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    if request_id:
        # Per-request: data/local/workspaces/materialized/<request_id>/
        sub = root / "materialized" / request_id
    else:
        # Per-session: data/local/workspaces/<session_id>/ or by project
        sid = session_id or stable_id("session", utc_now_iso(), prefix="ws")
        sub = root / sid
        if project_id:
            sub = sub / "projects" / project_id.replace("/", "_").replace("\\", "_")[:64]
    sub.mkdir(parents=True, exist_ok=True)
    return sub


def get_workspace_path(
    workspace_root: str | Path,
    session_id: str = "",
    request_id: str = "",
) -> Path:
    """Return the path that would be used for this session/request (may not exist yet)."""
    root = _resolve_root(workspace_root)
    if request_id:
        return root / "materialized" / request_id
    sid = session_id or "default"
    return root / sid


def list_workspaces(
    workspace_root: str | Path,
    session_id: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    List workspace directories (by mtime desc). If session_id given, list that session + materialized.
    Returns list of dicts with path, name, mtime_iso.
    """
    root = _resolve_root(workspace_root)
    if not root.exists():
        return []
    out: list[dict[str, Any]] = []
    try:
        if session_id:
            session_dir = root / session_id
            if session_dir.exists():
                out.append({"path": str(session_dir), "name": session_dir.name, "mtime_iso": utc_now_iso()})
            materialized = root / "materialized"
            if materialized.exists():
                for p in sorted(materialized.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                    if p.is_dir():
                        out.append({"path": str(p), "name": p.name, "mtime_iso": utc_now_iso()})
                        if len(out) >= limit:
                            break
        else:
            for d in sorted(root.iterdir(), key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True):
                if d.is_dir():
                    out.append({"path": str(d), "name": d.name, "mtime_iso": utc_now_iso()})
                if len(out) >= limit:
                    break
            materialized = root / "materialized"
            if materialized.exists() and len(out) < limit:
                for p in sorted(materialized.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                    if p.is_dir():
                        out.append({"path": str(p), "name": p.name, "mtime_iso": utc_now_iso()})
                    if len(out) >= limit:
                        break
    except Exception:
        pass
    return out[:limit]


def ensure_workspace_dir(workspace_path: Path | str, *subdirs: str) -> Path:
    """Ensure a subdirectory exists inside the workspace; return its path."""
    base = Path(workspace_path)
    for part in subdirs:
        base = base / part.replace("..", "").strip("/").replace("/", "_")
    base.mkdir(parents=True, exist_ok=True)
    return base


def cleanup_workspace(workspace_path: Path | str) -> bool:
    """Remove a workspace directory and its contents. Returns True if removed."""
    path = Path(workspace_path)
    if not path.exists() or not path.is_dir():
        return False
    resolved = path.resolve()
    root = _resolve_root(path.parent)
    # Only allow deleting dirs under our root
    try:
        resolved.relative_to(root)
    except ValueError:
        return False
    shutil.rmtree(resolved, ignore_errors=True)
    return True
