"""
M22C: Role-based review lane views. Local-only; file-based.
Lane summary, pending by lane, list workspaces/packages by lane.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.release.reporting_workspaces import (
    get_workspace_inventory,
    list_reporting_workspaces,
)
from workflow_dataset.release.review_state import (
    LANES,
    get_approved_artifacts,
    load_review_state,
)


def _repo_root(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    from workflow_dataset.path_utils import get_repo_root
    return Path(get_repo_root())


def _workspace_status(inv: dict[str, Any], state: dict[str, Any]) -> str:
    """Derive simple status: review_pending | package_pending | package_ready."""
    artifacts = inv.get("artifacts") or []
    artifacts_state = state.get("artifacts") or {}
    approved = get_approved_artifacts(inv["workspace_path"], repo_root=None)
    has_any_review = any(artifacts_state.get(a) for a in artifacts)
    if not has_any_review and artifacts:
        return "review_pending"
    if approved and not state.get("last_package_path"):
        return "package_pending"
    if state.get("last_package_path"):
        return "package_ready"
    return "review_pending"


def _has_needs_revision(state: dict[str, Any]) -> bool:
    artifacts = state.get("artifacts") or {}
    return any((m or {}).get("state") == "needs_revision" for m in artifacts.values())


def list_workspaces_in_lane(
    lane: str,
    repo_root: Path | str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List workspaces in the given lane. Returns list of { workspace_path, workflow, lane, status, ... }."""
    if lane not in LANES:
        return []
    root = _repo_root(repo_root)
    ws_root = root / "data/local/workspaces"
    if not ws_root.exists():
        return []
    workspaces = list_reporting_workspaces(ws_root, limit=limit * 2)
    out: list[dict[str, Any]] = []
    for inv in workspaces:
        wp = inv.get("workspace_path")
        if not wp:
            continue
        state = load_review_state(wp, repo_root=root)
        if (state.get("lane") or "").strip() != lane:
            continue
        status = _workspace_status(inv, state)
        out.append({
            "workspace_path": wp,
            "workflow": inv.get("workflow", "?"),
            "run_id": inv.get("run_id"),
            "lane": lane,
            "status": status,
            "artifact_count": len(inv.get("artifacts") or []),
            "approved_count": len(get_approved_artifacts(wp, repo_root=root)),
            "last_package_path": state.get("last_package_path"),
            "needs_revision": _has_needs_revision(state),
        })
        if len(out) >= limit:
            break
    return out


def _load_package_manifest(package_dir: Path) -> dict[str, Any] | None:
    p = package_dir / "package_manifest.json"
    if not p.exists() or not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_packages_in_lane(
    lane: str,
    repo_root: Path | str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List packages in the given lane (from package_manifest.lane)."""
    if lane not in LANES:
        return []
    root = _repo_root(repo_root)
    pkg_root = root / "data/local/packages"
    if not pkg_root.exists():
        return []
    out: list[dict[str, Any]] = []
    for d in sorted(pkg_root.iterdir(), key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True):
        if not d.is_dir():
            continue
        manifest = _load_package_manifest(d)
        if not manifest:
            continue
        if (manifest.get("lane") or "").strip() != lane:
            continue
        out.append({
            "package_path": str(d.resolve()),
            "package_dir": d.name,
            "workflow": manifest.get("workflow", "?"),
            "source_workspace": manifest.get("source_workspace"),
            "lane": lane,
            "artifact_count": manifest.get("artifact_count", 0),
            "created_utc": manifest.get("created_utc"),
        })
        if len(out) >= limit:
            break
    return out


def get_lane_summary(repo_root: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Per-lane summary: count_workspaces, count_packages, pending_count, needs_revision_count."""
    root = _repo_root(repo_root)
    ws_root = root / "data/local/workspaces"
    pkg_root = root / "data/local/packages"
    result: dict[str, dict[str, Any]] = {lane: {"count_workspaces": 0, "count_packages": 0, "pending_count": 0, "needs_revision_count": 0} for lane in LANES}
    result["_unlane"] = {"count_workspaces": 0, "count_packages": 0, "pending_count": 0, "needs_revision_count": 0}

    if ws_root.exists():
        for inv in list_reporting_workspaces(ws_root, limit=500):
            wp = inv.get("workspace_path")
            if not wp:
                continue
            state = load_review_state(wp, repo_root=root)
            lane = (state.get("lane") or "").strip() or "_unlane"
            if lane not in result:
                result[lane] = {"count_workspaces": 0, "count_packages": 0, "pending_count": 0, "needs_revision_count": 0}
            result[lane]["count_workspaces"] = result[lane].get("count_workspaces", 0) + 1
            status = _workspace_status(inv, state)
            if status in ("review_pending", "package_pending"):
                result[lane]["pending_count"] = result[lane].get("pending_count", 0) + 1
            if _has_needs_revision(state):
                result[lane]["needs_revision_count"] = result[lane].get("needs_revision_count", 0) + 1

    if pkg_root.exists():
        for d in pkg_root.iterdir():
            if not d.is_dir():
                continue
            manifest = _load_package_manifest(d)
            if not manifest:
                continue
            lane = (manifest.get("lane") or "").strip() or "_unlane"
            if lane not in result:
                result[lane] = {"count_workspaces": 0, "count_packages": 0, "pending_count": 0, "needs_revision_count": 0}
            result[lane]["count_packages"] = result[lane].get("count_packages", 0) + 1

    return result


def get_lane_status(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Full lane status: summary per lane, pending items by lane, latest workspace/package per lane."""
    root = _repo_root(repo_root)
    summary = get_lane_summary(root)
    out: dict[str, Any] = {
        "summary_by_lane": {k: v for k, v in summary.items() if k != "_unlane"},
        "unlane": summary.get("_unlane", {}),
        "pending_by_lane": {},
        "latest_workspace_by_lane": {},
        "latest_package_by_lane": {},
    }
    for lane in LANES:
        workspaces = list_workspaces_in_lane(lane, repo_root=root, limit=100)
        packages = list_packages_in_lane(lane, repo_root=root, limit=100)
        out["pending_by_lane"][lane] = {
            "workspaces": [w for w in workspaces if w.get("status") in ("review_pending", "package_pending")],
            "needs_revision": [w for w in workspaces if w.get("needs_revision")],
        }
        out["latest_workspace_by_lane"][lane] = workspaces[0] if workspaces else None
        out["latest_package_by_lane"][lane] = packages[0] if packages else None
    return out


def set_package_lane(package_path: str | Path, lane: str, repo_root: Path | str | None = None) -> Path:
    """Set the role lane on a package by updating package_manifest.json. lane must be one of LANES. Returns manifest path."""
    if lane not in LANES:
        raise ValueError(f"lane must be one of {LANES}")
    pkg_dir = Path(package_path).resolve()
    manifest_path = pkg_dir / "package_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Package manifest not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["lane"] = lane
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return manifest_path
