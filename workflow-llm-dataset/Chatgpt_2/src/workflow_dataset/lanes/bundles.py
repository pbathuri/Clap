"""
M28H.1: Reusable lane bundles for common work types.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.lanes.models import LaneScope, LanePermissions, LANE_PERMISSION_SIMULATE_ONLY

LANES_ROOT = "data/local/lanes"
BUNDLES_SUBDIR = "bundles"
BUNDLE_FILE = "bundle.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_bundles_dir(repo_root: Path | str | None = None) -> Path:
    """Return data/local/lanes/bundles; ensure it exists."""
    root = _repo_root(repo_root)
    path = root / LANES_ROOT / BUNDLES_SUBDIR
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class LaneBundle:
    """Reusable lane bundle: scope, default permissions, stop conditions, optional step labels."""
    bundle_id: str
    label: str = ""
    description: str = ""
    scope: LaneScope = field(default_factory=lambda: LaneScope(scope_id="default"))
    default_permissions: LanePermissions = field(default_factory=LanePermissions)
    default_stop_conditions: list[str] = field(default_factory=list)
    step_labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "label": self.label,
            "description": self.description,
            "scope": self.scope.to_dict(),
            "default_permissions": self.default_permissions.to_dict(),
            "default_stop_conditions": list(self.default_stop_conditions),
            "step_labels": list(self.step_labels),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LaneBundle":
        scope_d = d.get("scope", {})
        scope = LaneScope.from_dict(scope_d) if scope_d else LaneScope(scope_id=d.get("bundle_id", "default"))
        perms_d = d.get("default_permissions", {})
        perms = LanePermissions.from_dict(perms_d) if perms_d else LanePermissions()
        return cls(
            bundle_id=d.get("bundle_id", ""),
            label=d.get("label", ""),
            description=d.get("description", ""),
            scope=scope,
            default_permissions=perms,
            default_stop_conditions=list(d.get("default_stop_conditions", [])),
            step_labels=list(d.get("step_labels", [])),
        )


def save_bundle(bundle: LaneBundle, repo_root: Path | str | None = None) -> Path:
    """Persist bundle to bundles/<bundle_id>/bundle.json."""
    base = get_bundles_dir(repo_root)
    bundle_dir = base / bundle.bundle_id
    bundle_dir.mkdir(parents=True, exist_ok=True)
    path = bundle_dir / BUNDLE_FILE
    path.write_text(json.dumps(bundle.to_dict(), indent=2), encoding="utf-8")
    return path


def load_bundle(bundle_id: str, repo_root: Path | str | None = None) -> LaneBundle | None:
    """Load bundle by bundle_id."""
    base = get_bundles_dir(repo_root)
    path = base / bundle_id / BUNDLE_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return LaneBundle.from_dict(data)
    except Exception:
        return None


def list_bundles(limit: int = 50, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List all bundles."""
    base = get_bundles_dir(repo_root)
    if not base.exists():
        return []
    out: list[dict[str, Any]] = []
    for d in sorted(base.iterdir(), key=lambda x: x.name):
        if not d.is_dir():
            continue
        path = d / BUNDLE_FILE
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            out.append({
                "bundle_id": data.get("bundle_id", d.name),
                "label": data.get("label", ""),
                "description": (data.get("description", ""))[:80],
            })
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out


def ensure_default_bundles(repo_root: Path | str | None = None) -> None:
    """Ensure built-in bundles exist: extract_only, summarize_only."""
    for bid, label, desc in [
        ("extract_only", "Extract only", "Lane scope: extract data only; no writes."),
        ("summarize_only", "Summarize only", "Lane scope: summarize content; no external actions."),
    ]:
        if load_bundle(bid, repo_root) is None:
            scope = LaneScope(scope_id=bid, label=label, description=desc, allowed_step_classes=["local_inspect", "reasoning_only"])
            perms = LanePermissions(permission=LANE_PERMISSION_SIMULATE_ONLY)
            save_bundle(LaneBundle(bundle_id=bid, label=label, description=desc, scope=scope, default_permissions=perms), repo_root)
