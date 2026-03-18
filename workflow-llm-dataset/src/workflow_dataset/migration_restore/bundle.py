"""
M49E–M49H: Continuity bundle — manifest from state boundaries, list refs.
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

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]

from workflow_dataset.migration_restore.models import ContinuityBundleManifest
from workflow_dataset.state_durability.boundaries import SUBSYSTEM_BOUNDARIES


BUNDLES_DIR = "data/local/migration_restore/bundles"
LOCAL_ONLY_SUBSYSTEMS = ["background_queue"]   # e.g. machine-specific queue; exclude from portable bundle


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _product_version(repo_root: Path) -> str:
    try:
        from workflow_dataset.install_upgrade.version import get_current_version
        return get_current_version(repo_root) or "0.0.0"
    except Exception:
        return "0.0.0"


def get_bundle_manifest(
    bundle_ref: str,
    repo_root: Path | str | None = None,
) -> ContinuityBundleManifest | None:
    """
    Get manifest for a bundle. bundle_ref can be 'latest' (build from current state)
    or a bundle_id from data/local/migration_restore/bundles/.
    """
    root = _root(repo_root)
    if bundle_ref == "latest" or not bundle_ref:
        return _build_latest_manifest(root)
    # Load from saved bundle dir
    bundles_dir = root / BUNDLES_DIR
    manifest_path = bundles_dir / bundle_ref / "manifest.json"
    if manifest_path.exists():
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            return ContinuityBundleManifest.from_dict(raw)
        except Exception:
            pass
    return None


def _build_latest_manifest(root: Path) -> ContinuityBundleManifest:
    """Build manifest from current state boundaries (no copy of payload)."""
    now = utc_now_iso()
    bundle_id = stable_id("bundle", now[:16], prefix="bundle_")
    subsystem_ids: list[str] = []
    paths_in_bundle: list[str] = []
    local_only_excluded: list[str] = []
    for b in SUBSYSTEM_BOUNDARIES:
        sid = b.get("id", "")
        path = b.get("path", "")
        if sid in LOCAL_ONLY_SUBSYSTEMS:
            local_only_excluded.append(sid)
            continue
        subsystem_ids.append(sid)
        paths_in_bundle.append(path)
    return ContinuityBundleManifest(
        bundle_id=bundle_id,
        created_at_utc=now,
        product_version=_product_version(root),
        subsystem_ids=subsystem_ids,
        paths_in_bundle=paths_in_bundle,
        source_repo_root=str(root.resolve()),
        local_only_excluded=local_only_excluded,
    )


def list_bundle_refs(repo_root: Path | str | None = None) -> list[str]:
    """List available bundle refs: 'latest' plus any saved bundle_id in bundles dir."""
    refs = ["latest"]
    root = _root(repo_root)
    bundles_dir = root / BUNDLES_DIR
    if bundles_dir.is_dir():
        for p in bundles_dir.iterdir():
            if p.is_dir() and (p / "manifest.json").exists():
                refs.append(p.name)
    return refs
