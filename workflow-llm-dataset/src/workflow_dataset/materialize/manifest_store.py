"""
Persist and load materialization manifests in the workspace.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.materialize.materialize_models import MaterializationManifest, MaterializedArtifact


def save_manifest(manifest: MaterializationManifest, workspace_path: Path | str) -> Path:
    """Write manifest to workspace_path/MANIFEST.json. Returns path to file."""
    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    path = workspace_path / "MANIFEST.json"
    data = manifest.model_dump()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_manifest(workspace_path: Path | str, manifest_filename: str = "MANIFEST.json") -> MaterializationManifest | None:
    """Load manifest from workspace. Returns None if not found."""
    path = Path(workspace_path) / manifest_filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return MaterializationManifest.model_validate(data)


def list_manifests(workspace_root: Path | str, limit: int = 100) -> list[tuple[Path, MaterializationManifest]]:
    """Find all MANIFEST.json under workspace_root and load them. Returns (path, manifest) list."""
    root = Path(workspace_root)
    if not root.exists():
        return []
    out: list[tuple[Path, MaterializationManifest]] = []
    for p in root.rglob("MANIFEST.json"):
        if not p.is_file():
            continue
        m = load_manifest(p.parent, p.name)
        if m:
            out.append((p, m))
        if len(out) >= limit:
            break
    return out
