"""
M21V: Apply-plan staging board — local state between package approval and explicit apply.
Tracks staged packages/artifacts, builds apply-plan preview only (no apply).
State: data/local/staging/staging_board.json; last preview: data/local/staging/last_apply_plan_preview.md.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.path_utils import get_repo_root
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

STAGING_DIR = "data/local/staging"
BOARD_FILENAME = "staging_board.json"
PREVIEW_FILENAME = "last_apply_plan_preview.md"


def _staging_root(repo_root: Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else Path(get_repo_root())
    return (root / STAGING_DIR).resolve()


def _board_path(repo_root: Path | None = None) -> Path:
    return _staging_root(repo_root) / BOARD_FILENAME


def load_staging_board(repo_root: Path | None = None) -> dict[str, Any]:
    """Load staging board state. Returns dict with items (list) and last_apply_plan_preview_path."""
    path = _board_path(repo_root)
    if not path.exists():
        return {"items": [], "last_apply_plan_preview_path": None, "updated_at": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "items": data.get("items") or [],
            "last_apply_plan_preview_path": data.get("last_apply_plan_preview_path"),
            "updated_at": data.get("updated_at"),
        }
    except Exception:
        return {"items": [], "last_apply_plan_preview_path": None, "updated_at": None}


def _save_board(board: dict[str, Any], repo_root: Path | None = None) -> Path:
    path = _board_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(board, indent=2), encoding="utf-8")
    return path


def get_last_apply_plan_preview_path(repo_root: Path | None = None) -> str | None:
    """Return path to last apply-plan preview file, or None."""
    board = load_staging_board(repo_root)
    return board.get("last_apply_plan_preview_path")


def add_staged_package(
    package_path: str | Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """
    Add a built package to the staging board.
    Returns staged item dict: staged_id, source_type, source_path, workflow, artifact_paths, staged_at, provenance_snapshot.
    """
    pkg = Path(package_path).resolve()
    if not pkg.exists() or not pkg.is_dir():
        raise FileNotFoundError(f"Package directory not found: {pkg}")

    # Artifact paths: files in package (prefer manifest approved_artifacts if present)
    artifact_paths: list[str] = []
    manifest_path = pkg / "package_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            approved = manifest.get("approved_artifacts") or manifest.get("profile_included_artifacts")
            if approved:
                for name in approved:
                    if (pkg / name).exists():
                        artifact_paths.append(name)
        except Exception:
            pass
    if not artifact_paths:
        for f in sorted(pkg.iterdir()):
            if f.is_file():
                artifact_paths.append(f.name)

    workflow = "unknown"
    provenance: dict[str, Any] = {"source_path": str(pkg), "source_type": "package"}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            workflow = manifest.get("workflow") or workflow
            provenance["workflow"] = workflow
            provenance["source_workspace"] = manifest.get("source_workspace")
            provenance["created_utc"] = manifest.get("created_utc")
        except Exception:
            pass

    staged_id = stable_id("staged", str(pkg), utc_now_iso(), prefix="stg_")[:16]
    item: dict[str, Any] = {
        "staged_id": staged_id,
        "source_type": "package",
        "source_path": str(pkg),
        "workflow": workflow,
        "artifact_paths": artifact_paths,
        "staged_at": utc_now_iso(),
        "provenance_snapshot": provenance,
    }

    root = Path(repo_root) if repo_root is not None else Path(get_repo_root())
    board = load_staging_board(root)
    items = list(board.get("items") or [])
    items.append(item)
    board["items"] = items
    board["updated_at"] = utc_now_iso()
    _save_board(board, root)
    return item


def add_staged_artifact(
    workspace_path: str | Path,
    artifact_name: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """
    Add one artifact from a workspace to the staging board.
    Returns staged item dict. Raises ValueError if artifact not in workspace.
    """
    ws = Path(workspace_path).resolve()
    if not ws.exists() or not ws.is_dir():
        raise FileNotFoundError(f"Workspace not found: {ws}")
    art_path = ws / artifact_name
    if not art_path.exists() or not art_path.is_file():
        raise ValueError(f"Artifact not found in workspace: {artifact_name}")

    from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
    inv = get_workspace_inventory(ws)
    workflow = (inv.get("workflow") or "unknown") if inv else "unknown"
    provenance: dict[str, Any] = {
        "source_path": str(ws),
        "source_type": "artifact",
        "artifact": artifact_name,
        "workflow": workflow,
        "grounding": inv.get("grounding") if inv else None,
        "timestamp": inv.get("timestamp") if inv else None,
    }

    staged_id = stable_id("staged", str(ws), artifact_name, utc_now_iso(), prefix="stg_")[:16]
    item: dict[str, Any] = {
        "staged_id": staged_id,
        "source_type": "artifact",
        "source_path": str(ws),
        "workflow": workflow,
        "artifact_paths": [artifact_name],
        "staged_at": utc_now_iso(),
        "provenance_snapshot": provenance,
    }

    root = Path(repo_root) if repo_root is not None else Path(get_repo_root())
    board = load_staging_board(root)
    items = list(board.get("items") or [])
    items.append(item)
    board["items"] = items
    board["updated_at"] = utc_now_iso()
    _save_board(board, root)
    return item


def list_staged_items(repo_root: Path | None = None) -> list[dict[str, Any]]:
    """Return list of staged items (each with staged_id, source_type, source_path, workflow, artifact_paths, staged_at)."""
    board = load_staging_board(repo_root)
    return list(board.get("items") or [])


def remove_staged_item(staged_id: str, repo_root: Path | None = None) -> bool:
    """Remove one item by staged_id. Returns True if removed."""
    root = Path(repo_root) if repo_root is not None else Path(get_repo_root())
    board = load_staging_board(root)
    items = [i for i in (board.get("items") or []) if (i.get("staged_id") or "") != staged_id]
    if len(items) == len(board.get("items") or []):
        return False
    board["items"] = items
    board["updated_at"] = utc_now_iso()
    _save_board(board, root)
    return True


def clear_staging(repo_root: Path | None = None) -> None:
    """Clear all items from the staging board. Does not delete the preview file."""
    root = Path(repo_root) if repo_root is not None else Path(get_repo_root())
    board = load_staging_board(root)
    board["items"] = []
    board["updated_at"] = utc_now_iso()
    # Keep last_apply_plan_preview_path so operator can still view last preview
    _save_board(board, root)


def build_apply_plan_from_staging(
    target_path: str | Path,
    item_id: str | None = None,
    save_preview: bool = False,
    repo_root: Path | None = None,
) -> tuple[Any, str]:
    """
    Build apply-plan preview from staging board (one item: by item_id or first).
    No apply is performed. Returns (ApplyPlan | None, error_message).
    If save_preview True, writes preview to data/local/staging/last_apply_plan_preview.md and updates board.
    """
    from workflow_dataset.apply.copy_planner import build_apply_plan
    from workflow_dataset.apply.diff_preview import render_diff_preview

    root = Path(repo_root) if repo_root is not None else Path(get_repo_root())
    board = load_staging_board(root)
    items = board.get("items") or []
    if not items:
        return None, "Staging board is empty; stage a package or artifact first."

    item = None
    if item_id:
        for i in items:
            if (i.get("staged_id") or "") == item_id:
                item = i
                break
        if not item:
            return None, f"No staged item with id: {item_id}"
    else:
        item = items[0]

    source_path = Path(item.get("source_path") or "")
    if not source_path.exists() or not source_path.is_dir():
        return None, f"Source path no longer exists: {source_path}"
    target = Path(target_path).resolve()
    artifact_paths = item.get("artifact_paths") or []

    plan, err = build_apply_plan(
        source_path,
        target,
        selected_paths=artifact_paths if artifact_paths else None,
        allow_overwrite=False,
        dry_run=True,
    )
    if err and not plan:
        return None, err
    if not plan:
        return None, "No plan generated"

    if save_preview:
        preview_text = render_diff_preview(plan)
        # Prepend provenance and "no apply occurred" banner
        provenance = item.get("provenance_snapshot") or {}
        header = [
            "# Apply plan preview (no apply performed)",
            "",
            "**Source:** " + item.get("source_path", ""),
            "**Workflow:** " + str(provenance.get("workflow", "")),
            "**Staged at:** " + str(item.get("staged_at", "")),
            "",
            "---",
            "",
        ]
        preview_text = "\n".join(header) + preview_text
        preview_path = _staging_root(root) / PREVIEW_FILENAME
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        preview_path.write_text(preview_text, encoding="utf-8")
        board["last_apply_plan_preview_path"] = str(preview_path.resolve())
        board["updated_at"] = utc_now_iso()
        _save_board(board, root)

    return plan, ""
