"""
Local action proposal generation from approved folders and workflow tree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.capability_discovery.approval_registry import load_approval_registry, normalize_approved_paths
from workflow_dataset.local_operator.state_store import load_operator_state, save_operator_state
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def propose_local_actions(repo_root: Path | str | None = None) -> dict[str, Any]:
    registry = load_approval_registry(repo_root)
    approved_entries = normalize_approved_paths(
        registry.approved_paths, exclude_template_paths=True
    )
    active_entries = [e for e in approved_entries if e.get("revocation_state") == "active"]

    proposals: list[dict[str, Any]] = []
    ts = utc_now_iso()
    for entry in active_entries:
        path = str(entry.get("path") or "")
        if not path:
            continue
        action_id = stable_id("act", path, ts, prefix="act")
        proposals.append({
            "action_id": action_id,
            "title": f"Inspect {Path(path).name}",
            "label": f"Inspect {Path(path).name}",
            "adapter_id": "file_ops",
            "action_type": "inspect_path",
            "params": {"path": path},
            "risk_tier": "low",
            "destructive": False,
            "reversible": True,
            "approval_requirement": "explicit",
            "execution_scope": {"paths": [path]},
            "required_adapter": "file_ops",
            "required_permissions": ["Files/Folders"],
            "scope_origin": "approved_folder",
            "rationale": "Baseline inspection of approved folder contents.",
            "rollback_feasible": True,
            "rollback_method": "none",
        })
        finder_id = stable_id("act", "finder", path, ts, prefix="act")
        proposals.append({
            "action_id": finder_id,
            "title": f"Open {Path(path).name} in Finder",
            "label": f"Open {Path(path).name} in Finder",
            "adapter_id": "finder_open",
            "action_type": "open_folder",
            "params": {"path": path},
            "risk_tier": "low",
            "destructive": False,
            "reversible": True,
            "approval_requirement": "explicit",
            "execution_scope": {"paths": [path]},
            "required_adapter": "finder_open",
            "required_permissions": ["Automation"],
            "scope_origin": "approved_folder",
            "rationale": "Open approved folder in Finder for supervised navigation.",
            "rollback_feasible": True,
            "rollback_method": "none",
        })

    state = load_operator_state(repo_root)
    state["action_proposals"] = proposals
    state["updated_at"] = ts
    save_operator_state(state, repo_root)
    return state
