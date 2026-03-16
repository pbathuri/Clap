"""
M23D-F1: Approval registry. Approved paths, approved app names, approved action scopes. Local file only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class ApprovalRegistry:
    """Explicit local approvals: paths, apps, action scopes."""
    approved_paths: list[str] = field(default_factory=list)
    approved_apps: list[str] = field(default_factory=list)
    approved_action_scopes: list[dict[str, Any]] = field(default_factory=list)
    # Each scope: {adapter_id: str, action_id: str, executable: bool}


DEFAULT_REGISTRY_DIR = Path("data/local/capability_discovery")
APPROVALS_FILENAME = "approvals.yaml"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_registry_path(repo_root: Path | str | None = None) -> Path:
    """Path to approvals file. Does not create it."""
    return _repo_root(repo_root) / DEFAULT_REGISTRY_DIR / APPROVALS_FILENAME


def load_approval_registry(repo_root: Path | str | None = None) -> ApprovalRegistry:
    """Load approval registry from data/local/capability_discovery/approvals.yaml. Returns empty registry if missing."""
    path = get_registry_path(repo_root)
    if not path.exists() or not path.is_file():
        return ApprovalRegistry()
    if yaml is None:
        return ApprovalRegistry()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return ApprovalRegistry(
            approved_paths=list(raw.get("approved_paths") or []),
            approved_apps=list(raw.get("approved_apps") or []),
            approved_action_scopes=list(raw.get("approved_action_scopes") or []),
        )
    except Exception:
        return ApprovalRegistry()


def save_approval_registry(registry: ApprovalRegistry, repo_root: Path | str | None = None) -> Path:
    """Save approval registry to data/local/capability_discovery/approvals.yaml. Creates parent dirs."""
    path = get_registry_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "approved_paths": registry.approved_paths,
        "approved_apps": registry.approved_apps,
        "approved_action_scopes": registry.approved_action_scopes,
    }
    if yaml is None:
        import json
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    return path
