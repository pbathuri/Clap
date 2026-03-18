"""
M40E–M40H: Bundle packaging — build and write bundle manifest for production cut.
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

from workflow_dataset.deploy_bundle.registry import get_deployment_bundle
from workflow_dataset.deploy_bundle.store import get_deploy_bundle_dir

MANIFEST_FILE = "manifest.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_bundle_manifest(
    bundle_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Build bundle manifest dict from registry bundle; add repo_root and generated_at."""
    bundle = get_deployment_bundle(bundle_id)
    if not bundle:
        return {"error": f"Bundle not found: {bundle_id}", "bundle_id": bundle_id}
    root = _repo_root(repo_root)
    manifest = bundle.to_dict()
    manifest["repo_root"] = str(root)
    manifest["generated_at"] = utc_now_iso()
    return manifest


def write_bundle_manifest(
    bundle_id: str,
    repo_root: Path | str | None = None,
) -> Path:
    """Write bundle manifest to data/local/deploy_bundle/manifest.json. Returns path written."""
    manifest = build_bundle_manifest(bundle_id, repo_root)
    if manifest.get("error"):
        raise ValueError(manifest["error"])
    root = get_deploy_bundle_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / MANIFEST_FILE
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path
