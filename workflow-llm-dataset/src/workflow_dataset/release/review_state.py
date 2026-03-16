"""
M21T: Per-workspace review state (approved / needs_revision / excluded).
Stored under data/local/review/<workflow>/<run_id>.json. Local-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REVIEW_STATE_ROOT = "data/local/review"
VALID_STATES = ("approved", "needs_revision", "excluded")

# M22C: Role-based review lanes (local-only; no cloud sync)
LANES = ("operator", "reviewer", "stakeholder-prep", "approver")


def _review_path(workspace_path: str | Path, repo_root: Path | None = None) -> Path:
    """Path to review state file for this workspace. Keyed by parent/name (workflow/run_id)."""
    ws = Path(workspace_path).resolve()
    if repo_root is None:
        from workflow_dataset.path_utils import get_repo_root
        repo_root = get_repo_root()
    root = Path(repo_root) / REVIEW_STATE_ROOT
    # workspace_path is .../workspaces/<workflow>/<run_id>
    workflow = ws.parent.name
    run_id = ws.name
    root = root / workflow
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{run_id}.json"


def load_review_state(workspace_path: str | Path, repo_root: Path | None = None) -> dict[str, Any]:
    """Load review state for workspace. Returns dict with artifacts, last_package_path, updated_at, lane."""
    path = _review_path(workspace_path, repo_root)
    if not path.exists():
        return {"artifacts": {}, "last_package_path": None, "updated_at": None, "lane": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "artifacts": data.get("artifacts") or {},
            "last_package_path": data.get("last_package_path"),
            "updated_at": data.get("updated_at"),
            "lane": data.get("lane") if data.get("lane") in LANES else None,
        }
    except Exception:
        return {"artifacts": {}, "last_package_path": None, "updated_at": None, "lane": None}


def save_review_state(
    workspace_path: str | Path,
    artifacts: dict[str, dict[str, Any]],
    last_package_path: str | None = None,
    updated_at: str | None = None,
    lane: str | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Save review state. artifacts: { artifact_name: { state, note?, reviewed_at? } }.
    lane: optional role lane (operator|reviewer|stakeholder-prep|approver). Returns path to state file."""
    from workflow_dataset.utils.dates import utc_now_iso
    path = _review_path(workspace_path, repo_root)
    existing: dict[str, Any] = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    resolved_lane = lane if lane in LANES else (existing.get("lane") if existing.get("lane") in LANES else None)
    payload: dict[str, Any] = {
        "workspace_path": str(Path(workspace_path).resolve()),
        "artifacts": artifacts,
        "last_package_path": last_package_path,
        "updated_at": updated_at or utc_now_iso(),
    }
    if resolved_lane is not None:
        payload["lane"] = resolved_lane
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def set_artifact_state(
    workspace_path: str | Path,
    artifact_name: str,
    state: str,
    note: str = "",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Set one artifact's review state. state must be approved | needs_revision | excluded. Returns updated full state."""
    from workflow_dataset.utils.dates import utc_now_iso
    if state not in VALID_STATES:
        raise ValueError(f"state must be one of {VALID_STATES}")
    current = load_review_state(workspace_path, repo_root)
    artifacts = dict(current.get("artifacts") or {})
    artifacts[artifact_name] = {
        "state": state,
        "note": (note or "").strip(),
        "reviewed_at": utc_now_iso(),
    }
    save_review_state(
        workspace_path,
        artifacts,
        last_package_path=current.get("last_package_path"),
        updated_at=utc_now_iso(),
        repo_root=repo_root,
    )
    return load_review_state(workspace_path, repo_root)


def get_approved_artifacts(workspace_path: str | Path, repo_root: Path | None = None) -> list[str]:
    """Return list of artifact names currently marked approved."""
    state = load_review_state(workspace_path, repo_root)
    artifacts = state.get("artifacts") or {}
    return [name for name, meta in artifacts.items() if (meta or {}).get("state") == "approved"]


def set_workspace_lane(
    workspace_path: str | Path,
    lane: str,
    repo_root: Path | None = None,
) -> Path:
    """Set the role lane for a workspace. lane must be one of LANES. Returns path to state file."""
    if lane not in LANES:
        raise ValueError(f"lane must be one of {LANES}")
    current = load_review_state(workspace_path, repo_root)
    return save_review_state(
        workspace_path,
        current.get("artifacts") or {},
        last_package_path=current.get("last_package_path"),
        updated_at=current.get("updated_at"),
        lane=lane,
        repo_root=repo_root,
    )
