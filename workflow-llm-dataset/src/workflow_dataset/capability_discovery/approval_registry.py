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
    approved_paths: list[dict[str, Any]] = field(default_factory=list)
    approved_apps: list[str] = field(default_factory=list)
    approved_action_scopes: list[dict[str, Any]] = field(default_factory=list)
    # Each scope: {adapter_id: str, action_id: str, executable: bool}


DEFAULT_REGISTRY_DIR = Path("data/local/capability_discovery")
APPROVALS_FILENAME = "approvals.yaml"

# Doc/example paths that must not drive real ingest/proposals (local operator).
_DOCUMENTATION_PLACEHOLDER_PATHS = frozenset({
    "/path/to/folder",
    "path/to/folder",
    "/path/to/project",
    "path/to/project",
    "/path/to/workspace",
    "path/to/workspace",
    "/path/to/file",
    "path/to/file",
})


def is_documentation_placeholder_path(path: str) -> bool:
    """True for common template paths from docs/seeds (not real directories)."""
    p = (path or "").strip().replace("\\", "/")
    if not p:
        return True
    pl = p.lower().rstrip("/")
    return pl in {x.lower().rstrip("/") for x in _DOCUMENTATION_PLACEHOLDER_PATHS}


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
    try:
        raw: dict[str, Any]
        if yaml is not None:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        else:
            import json
            raw = json.loads(path.read_text(encoding="utf-8")) or {}
        return ApprovalRegistry(
            approved_paths=normalize_approved_paths(list(raw.get("approved_paths") or [])),
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
        "approved_paths": normalize_approved_paths(registry.approved_paths),
        "approved_apps": registry.approved_apps,
        "approved_action_scopes": registry.approved_action_scopes,
    }
    if yaml is None:
        import json
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    return path


def normalize_approved_paths(
    raw_paths: list[Any],
    *,
    exclude_template_paths: bool = False,
) -> list[dict[str, Any]]:
    """Ensure approved_paths entries are dicts with required metadata keys."""
    normalized: list[dict[str, Any]] = []
    for entry in raw_paths:
        if isinstance(entry, str):
            entry = {"path": entry}
        if not isinstance(entry, dict):
            continue
        path_str = str(entry.get("path") or "")
        if exclude_template_paths and is_documentation_placeholder_path(path_str):
            continue
        normalized.append({
            "path": path_str,
            "allowed_operations": list(entry.get("allowed_operations") or []),
            "recursive": bool(entry.get("recursive", True)),
            "inherit_mode": str(entry.get("inherit_mode") or "inherit"),
            "sensitivity_tag": str(entry.get("sensitivity_tag") or "unspecified"),
            "approval_source": str(entry.get("approval_source") or "explicit_user"),
            "revocation_state": str(entry.get("revocation_state") or "active"),
            "approved_at": entry.get("approved_at", ""),
            "reviewed_at": entry.get("reviewed_at", ""),
            "expires_at": entry.get("expires_at", ""),
        })
    return normalized
