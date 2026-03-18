"""
M26H.1: Cross-app action bundles — reusable named sequences of job_run and adapter_action steps.
Safety-first: bundles are explicit, stored under data/local/executor/bundles.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.executor.hub import get_executor_runs_dir

BUNDLES_FILE = "bundles.json"


def _bundles_path(repo_root: Path | str | None) -> Path:
    """Path to data/local/executor/bundles.json."""
    root = get_executor_runs_dir(repo_root).parent
    return root / BUNDLES_FILE


@dataclass
class BundleStep:
    """Single step in a bundle: job_run or adapter_action."""

    action_type: str  # job_run | adapter_action
    action_ref: str   # job_pack_id or "adapter_id:action_id"
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"action_type": self.action_type, "action_ref": self.action_ref, "label": self.label or self.action_ref}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BundleStep":
        return cls(
            action_type=str(d.get("action_type", "job_run")),
            action_ref=str(d.get("action_ref", "")),
            label=str(d.get("label", "")),
        )


@dataclass
class ActionBundle:
    """Named cross-app action bundle: id, title, description, ordered steps."""

    bundle_id: str
    title: str
    description: str = ""
    steps: list[BundleStep] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)  # e.g. recovery, manual_fix, cross_app

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "title": self.title,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ActionBundle":
        steps = [BundleStep.from_dict(s) for s in d.get("steps", [])]
        return cls(
            bundle_id=str(d.get("bundle_id", "")),
            title=str(d.get("title", "")),
            description=str(d.get("description", "")),
            steps=steps,
            tags=list(d.get("tags", [])),
        )


def load_bundles_registry(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Load bundles registry from data/local/executor/bundles.json. Returns {bundles: [{...}]}."""
    path = _bundles_path(repo_root)
    if not path.exists():
        return {"bundles": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"bundles": []}


def save_bundles_registry(data: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    """Write bundles registry. data must have 'bundles' list."""
    path = _bundles_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def list_bundles(repo_root: Path | str | None = None) -> list[ActionBundle]:
    """List all registered action bundles."""
    reg = load_bundles_registry(repo_root)
    return [ActionBundle.from_dict(b) for b in reg.get("bundles", [])]


def get_bundle(bundle_id: str, repo_root: Path | str | None = None) -> ActionBundle | None:
    """Get bundle by id."""
    for b in list_bundles(repo_root):
        if b.bundle_id == bundle_id:
            return b
    return None


def save_bundle(bundle: ActionBundle, repo_root: Path | str | None = None) -> Path:
    """Add or overwrite bundle in registry."""
    reg = load_bundles_registry(repo_root)
    bundles = [ActionBundle.from_dict(b) for b in reg.get("bundles", [])]
    bundles = [b for b in bundles if b.bundle_id != bundle.bundle_id]
    bundles.append(bundle)
    reg["bundles"] = [b.to_dict() for b in bundles]
    return save_bundles_registry(reg, repo_root)


def delete_bundle(bundle_id: str, repo_root: Path | str | None = None) -> bool:
    """Remove bundle by id. Returns True if removed."""
    reg = load_bundles_registry(repo_root)
    bundles = [b for b in reg.get("bundles", []) if b.get("bundle_id") != bundle_id]
    if len(bundles) == len(reg.get("bundles", [])):
        return False
    reg["bundles"] = bundles
    save_bundles_registry(reg, repo_root)
    return True
