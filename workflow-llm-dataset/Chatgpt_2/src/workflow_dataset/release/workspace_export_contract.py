"""
A4: Workspace export contracts and downstream handoff spec.
Stable schema version, required/optional files, manifest compatibility checks.
Local-only; read-only validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

WORKSPACE_EXPORT_SCHEMA_VERSION = "1.0"

# Contract per workflow: manifest filename, required manifest keys, required files, optional files.
EXPORT_CONTRACTS: dict[str, dict[str, Any]] = {
    "ops_reporting_workspace": {
        "manifest_file": "workspace_manifest.json",
        "required_manifest_keys": ["workflow", "timestamp", "saved_artifact_paths"],
        "required_files": ["workspace_manifest.json", "source_snapshot.md"],
        "optional_files": [
            "weekly_status.md",
            "status_brief.md",
            "action_register.md",
            "stakeholder_update.md",
            "decision_requests.md",
        ],
        "description": "Multi-artifact ops reporting workspace (M21S/A2).",
    },
    "weekly_status": {
        "manifest_file": "manifest.json",
        "required_manifest_keys": ["artifact_type", "timestamp", "grounding"],
        "required_files": ["manifest.json", "weekly_status.md"],
        "optional_files": [],
        "description": "Single weekly status artifact.",
    },
    "status_action_bundle": {
        "manifest_file": "manifest.json",
        "required_manifest_keys": ["workflow", "timestamp", "grounding"],
        "required_files": ["manifest.json"],
        "optional_files": ["status_brief.md", "action_register.md"],
        "required_at_least_one_of": ["status_brief.md", "action_register.md"],
        "description": "Status brief + action register bundle.",
    },
    "stakeholder_update_bundle": {
        "manifest_file": "manifest.json",
        "required_manifest_keys": ["workflow", "timestamp", "grounding"],
        "required_files": ["manifest.json"],
        "optional_files": ["stakeholder_update.md", "decision_requests.md"],
        "required_at_least_one_of": ["stakeholder_update.md", "decision_requests.md"],
        "description": "Stakeholder update + decision requests bundle.",
    },
    "meeting_brief_bundle": {
        "manifest_file": "manifest.json",
        "required_manifest_keys": ["workflow", "timestamp", "grounding"],
        "required_files": ["manifest.json"],
        "optional_files": ["meeting_brief.md", "action_items.md"],
        "required_at_least_one_of": ["meeting_brief.md", "action_items.md"],
        "description": "Meeting brief + action items bundle.",
    },
}


def _load_manifest(workspace_path: Path) -> dict[str, Any] | None:
    for name in ("workspace_manifest.json", "manifest.json"):
        p = workspace_path / name
        if p.exists() and p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return None


def _infer_workflow(workspace_path: Path, manifest: dict[str, Any] | None) -> str | None:
    if manifest:
        w = manifest.get("workflow") or manifest.get("artifact_type")
        if w:
            return w
    parent_name = workspace_path.parent.name
    if parent_name in EXPORT_CONTRACTS:
        return parent_name
    return None


def get_export_contract(workflow: str) -> dict[str, Any] | None:
    """Return the export contract for a workflow, or None if unknown."""
    return EXPORT_CONTRACTS.get(workflow)


def validate_workspace_export(
    workspace_path: str | Path,
    *,
    schema_version: str = WORKSPACE_EXPORT_SCHEMA_VERSION,
) -> dict[str, Any]:
    """
    Validate a workspace directory against the export contract.
    Returns dict: valid (bool), errors (list), warnings (list), contract_version, workflow,
    missing_required (files), missing_manifest_keys, manifest_compatible (bool), contract (dict or None).
    Does not mutate the workspace.
    """
    ws = Path(workspace_path).resolve()
    result: dict[str, Any] = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "contract_version": schema_version,
        "workflow": None,
        "missing_required": [],
        "missing_manifest_keys": [],
        "manifest_compatible": False,
        "contract": None,
    }

    if not ws.exists():
        result["errors"].append("Workspace path does not exist")
        return result
    if not ws.is_dir():
        result["errors"].append("Workspace path is not a directory")
        return result

    manifest = _load_manifest(ws)
    if not manifest:
        result["errors"].append("No workspace_manifest.json or manifest.json found")
        return result

    workflow = _infer_workflow(ws, manifest)
    if not workflow:
        result["errors"].append("Could not infer workflow from manifest or path")
        return result
    result["workflow"] = workflow

    contract = get_export_contract(workflow)
    if not contract:
        result["warnings"].append(f"No export contract defined for workflow: {workflow}")
        result["contract"] = None
        # Minimal pass: has manifest and at least one .md
        md_files = [f.name for f in ws.iterdir() if f.is_file() and f.suffix.lower() == ".md"]
        if not md_files:
            result["errors"].append("No markdown artifact found")
        else:
            result["valid"] = True
            result["manifest_compatible"] = True
        return result

    result["contract"] = {
        "workflow": workflow,
        "manifest_file": contract.get("manifest_file"),
        "required_files": list(contract.get("required_files") or []),
        "optional_files": list(contract.get("optional_files") or []),
    }

    # Required manifest keys
    required_keys = contract.get("required_manifest_keys") or []
    for k in required_keys:
        if k not in manifest:
            result["missing_manifest_keys"].append(k)
    if result["missing_manifest_keys"]:
        result["errors"].append(f"Manifest missing keys: {result['missing_manifest_keys']}")

    # saved_artifact_paths or artifact_list must list files that exist
    listed = manifest.get("saved_artifact_paths") or manifest.get("artifact_list") or manifest.get("output_paths") or []
    if isinstance(listed, list):
        listed = [p if isinstance(p, str) and "/" not in p else Path(p).name for p in listed]
    else:
        listed = []

    # Required files must exist and be listed
    required_files = list(contract.get("required_files") or [])
    for f in required_files:
        if not (ws / f).is_file():
            result["missing_required"].append(f)
        if listed and f not in listed:
            result["warnings"].append(f"Required file {f} not in manifest saved_artifact_paths/artifact_list")

    # required_at_least_one_of (e.g. status_brief or action_register)
    at_least_one = contract.get("required_at_least_one_of") or []
    if at_least_one:
        found = [x for x in at_least_one if (ws / x).is_file()]
        if not found:
            result["errors"].append(f"At least one of {at_least_one} must be present")

    if result["missing_required"]:
        result["errors"].append(f"Missing required files: {result['missing_required']}")

    result["manifest_compatible"] = len(result["missing_manifest_keys"]) == 0
    result["valid"] = len(result["errors"]) == 0
    return result
