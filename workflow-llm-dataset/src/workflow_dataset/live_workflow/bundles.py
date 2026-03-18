"""
M33H.1: Reusable workflow bundles for common real-time workflows.

Bundles live under data/local/live_workflow/bundles/ (one YAML per bundle).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.live_workflow.models import WorkflowBundle

BUNDLES_DIR_NAME = "bundles"
BUNDLES_SUBDIR = "data/local/live_workflow/bundles"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _bundles_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / BUNDLES_SUBDIR


def list_bundle_ids(repo_root: Path | str | None = None) -> list[str]:
    """List bundle ids from bundles dir (YAML and JSON files, id = stem)."""
    d = _bundles_dir(repo_root)
    if not d.exists():
        return []
    ids = []
    for p in d.iterdir():
        if p.suffix.lower() in (".yaml", ".yml", ".json") and p.stem and not p.stem.startswith("."):
            ids.append(p.stem)
    return sorted(ids)


def get_bundle(bundle_id: str, repo_root: Path | str | None = None) -> WorkflowBundle | None:
    """Load a workflow bundle by id. Returns None if not found or invalid."""
    d = _bundles_dir(repo_root)
    for ext in (".yaml", ".yml", ".json"):
        path = d / f"{bundle_id}{ext}"
        if path.exists():
            return _load_bundle_file(path, bundle_id)
    return None


def _load_bundle_file(path: Path, bundle_id: str) -> WorkflowBundle | None:
    try:
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            import json
            data = json.loads(raw)
        else:
            import yaml
            data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return None
        data.setdefault("bundle_id", bundle_id)
        return WorkflowBundle.model_validate(data)
    except Exception:
        return None


def list_bundles(repo_root: Path | str | None = None) -> list[WorkflowBundle]:
    """List all workflow bundles."""
    ids = list_bundle_ids(repo_root)
    out = []
    for bid in ids:
        b = get_bundle(bid, repo_root)
        if b:
            out.append(b)
    return out


def save_bundle(bundle: WorkflowBundle, repo_root: Path | str | None = None) -> Path:
    """Save a workflow bundle as YAML. Creates bundles dir if needed. Returns path."""
    d = _bundles_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{bundle.bundle_id or 'bundle'}.yaml"
    import yaml
    data = bundle.model_dump()
    path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    return path
