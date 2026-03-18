"""
M23I: Trusted real-action subset. Explicit list of actions approved for real execution.
Requires approvals to be present; refuse clearly if missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.desktop_adapters import list_adapters
from workflow_dataset.capability_discovery.approval_registry import (
    get_registry_path,
    load_approval_registry,
)

# Narrow safe subset: read-only or sandbox-only. No browser/app real.
TRUSTED_ADAPTER_ACTIONS: list[tuple[str, str]] = [
    ("file_ops", "inspect_path"),
    ("file_ops", "list_directory"),
    ("file_ops", "snapshot_to_sandbox"),
    ("notes_document", "read_text"),
    ("notes_document", "summarize_text_for_workflow"),
    ("notes_document", "propose_status_from_notes"),
]


def get_trusted_real_actions(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Return currently trusted real actions: those in TRUSTED_ADAPTER_ACTIONS that are
    (1) supported by adapter contract (supports_real) and (2) when registry exists, listed in approved_action_scopes with executable=true.
    """
    root = Path(repo_root).resolve() if repo_root else None
    reg_path = get_registry_path(root)
    registry = load_approval_registry(root) if reg_path.exists() and reg_path.is_file() else None
    approved_scopes = list(registry.approved_action_scopes) if registry else []
    adapter_ids = {a.adapter_id for a in list_adapters()}

    result: list[dict[str, Any]] = []
    for adapter_id, action_id in TRUSTED_ADAPTER_ACTIONS:
        if adapter_id not in adapter_ids:
            continue
        # Contract supports real?
        adapter = next((a for a in list_adapters() if a.adapter_id == adapter_id), None)
        if not adapter:
            continue
        action_spec = next((a for a in adapter.supported_actions if a.action_id == action_id), None)
        if not action_spec or not action_spec.supports_real:
            continue
        # If registry exists and has scopes, must be in approved scopes with executable=true
        if approved_scopes:
            in_scope = any(
                str(s.get("adapter_id")) == adapter_id and str(s.get("action_id")) == action_id and s.get("executable") is True
                for s in approved_scopes
            )
            if not in_scope:
                continue
        result.append({"adapter_id": adapter_id, "action_id": action_id})

    return {
        "registry_path": str(reg_path),
        "registry_exists": reg_path.exists() and reg_path.is_file(),
        "approved_paths_count": len(registry.approved_paths) if registry else 0,
        "approved_scopes_count": len(approved_scopes),
        "trusted_actions": result,
        "ready_for_real": len(result) > 0,
    }


def list_trusted_actions_report(repo_root: Path | str | None = None) -> str:
    """Human-readable report of trusted real actions and approval status."""
    d = get_trusted_real_actions(repo_root)
    lines = [
        "Trusted real actions (narrow safe subset)",
        "  registry: " + d["registry_path"],
        "  registry_exists: " + str(d["registry_exists"]),
        "  approved_paths: " + str(d["approved_paths_count"]),
        "  approved_action_scopes: " + str(d["approved_scopes_count"]),
        "  ready_for_real: " + str(d["ready_for_real"]),
        "  trusted_actions:",
    ]
    for a in d["trusted_actions"]:
        lines.append(f"    - {a['adapter_id']}.{a['action_id']}")
    if not d["trusted_actions"]:
        lines.append("    (none — add approvals or create registry)")
    return "\n".join(lines)
