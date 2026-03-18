"""
M40E–M40H: Active deployment bundle store. data/local/deploy_bundle/active.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DIR_NAME = "data/local/deploy_bundle"
ACTIVE_FILE = "active.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_deploy_bundle_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / DIR_NAME


def get_active_bundle(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return active deployment bundle state: active_bundle_id, applied_at_utc, deployment_profile_id, maintenance_mode_id (M40H.1)."""
    path = get_deploy_bundle_dir(repo_root) / ACTIVE_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def set_active_bundle(bundle_id: str, repo_root: Path | str | None = None) -> Path:
    """Persist active deployment bundle id. Preserves deployment_profile_id and maintenance_mode_id if present."""
    from datetime import datetime, timezone
    root = get_deploy_bundle_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ACTIVE_FILE
    existing = get_active_bundle(repo_root=root)
    data = {
        "active_bundle_id": bundle_id,
        "applied_at_utc": datetime.now(timezone.utc).isoformat(),
        "deployment_profile_id": existing.get("deployment_profile_id", ""),
        "maintenance_mode_id": existing.get("maintenance_mode_id", ""),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def set_deployment_profile(profile_id: str, repo_root: Path | str | None = None) -> Path:
    """Set active deployment profile id (M40H.1). Merges into active.json."""
    from datetime import datetime, timezone
    root = get_deploy_bundle_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ACTIVE_FILE
    existing = get_active_bundle(repo_root=root)
    data = {
        "active_bundle_id": existing.get("active_bundle_id", ""),
        "applied_at_utc": existing.get("applied_at_utc", datetime.now(timezone.utc).isoformat()),
        "deployment_profile_id": profile_id,
        "maintenance_mode_id": existing.get("maintenance_mode_id", ""),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def set_maintenance_mode(mode_id: str, repo_root: Path | str | None = None) -> Path:
    """Set active maintenance mode id (M40H.1). Use empty string to clear. Merges into active.json."""
    from datetime import datetime, timezone
    root = get_deploy_bundle_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ACTIVE_FILE
    existing = get_active_bundle(repo_root=root)
    data = {
        "active_bundle_id": existing.get("active_bundle_id", ""),
        "applied_at_utc": existing.get("applied_at_utc", datetime.now(timezone.utc).isoformat()),
        "deployment_profile_id": existing.get("deployment_profile_id", ""),
        "maintenance_mode_id": mode_id,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path
