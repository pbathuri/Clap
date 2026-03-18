"""
M21T: Discover and inventory saved ops reporting workspaces.
Lists run dirs under data/local/workspaces/<workflow>/ and loads manifest/metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPORTING_WORKFLOWS = (
    "weekly_status",
    "status_action_bundle",
    "stakeholder_update_bundle",
    "meeting_brief_bundle",
    "ops_reporting_workspace",
)


def _load_manifest(workspace_path: Path) -> dict[str, Any] | None:
    """Load manifest.json or workspace_manifest.json from workspace dir. Returns None if missing."""
    for name in ("workspace_manifest.json", "manifest.json"):
        p = workspace_path / name
        if p.exists() and p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return None


def _artifact_list_from_manifest(manifest: dict[str, Any] | None, workspace_path: Path) -> list[str]:
    """Return list of artifact filenames (e.g. weekly_status.md) from manifest or dir listing."""
    if manifest:
        paths = manifest.get("saved_artifact_paths") or manifest.get("output_paths")
        if paths:
            return [p if isinstance(p, str) and "/" not in p else Path(p).name for p in paths]
    # Fallback: list .md and common names, skip manifest files
    out: list[str] = []
    for f in workspace_path.iterdir():
        if f.is_file() and f.suffix.lower() == ".md":
            out.append(f.name)
    for name in ("manifest.json", "workspace_manifest.json"):
        if name in out:
            out.remove(name)
    return sorted(out)


def get_workspace_inventory(workspace_path: str | Path) -> dict[str, Any] | None:
    """
    Return inventory for one reporting workspace dir: workflow, artifacts, timestamp, grounding.
    Returns None if path is not a dir or has no recognizable manifest.
    """
    ws = Path(workspace_path).resolve()
    if not ws.exists() or not ws.is_dir():
        return None
    manifest = _load_manifest(ws)
    workflow = None
    timestamp = None
    grounding = None
    if manifest:
        workflow = manifest.get("workflow") or manifest.get("artifact_type")
        timestamp = manifest.get("timestamp") or manifest.get("created_utc")
        grounding = manifest.get("grounding")
    if not workflow and ws.parent.name in REPORTING_WORKFLOWS:
        workflow = ws.parent.name
    artifacts = _artifact_list_from_manifest(manifest, ws)
    mtime = ws.stat().st_mtime if ws.exists() else 0
    template_id = manifest.get("template_id") if manifest else None
    template_version = manifest.get("template_version") if manifest else None
    return {
        "workspace_path": str(ws),
        "run_id": ws.name,
        "workflow": workflow or "unknown",
        "artifacts": artifacts,
        "timestamp": timestamp,
        "grounding": grounding,
        "manifest": manifest,
        "mtime": mtime,
        "template_id": template_id,
        "template_version": template_version,
    }


def list_reporting_workspaces(
    root: str | Path,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    List recent reporting workspace runs under root (e.g. data/local/workspaces).
    Returns list of inventory dicts, newest first by mtime.
    """
    root = Path(root).resolve()
    if not root.exists():
        return []
    collected: list[dict[str, Any]] = []
    for workflow in REPORTING_WORKFLOWS:
        parent = root / workflow
        if not parent.exists() or not parent.is_dir():
            continue
        for run_dir in parent.iterdir():
            if not run_dir.is_dir():
                continue
            inv = get_workspace_inventory(run_dir)
            if inv:
                collected.append(inv)
    collected.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return collected[:limit]
