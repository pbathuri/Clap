"""
Local operator readiness: machine + operator surfaces (not generic trust cockpit).
Always returns structured dicts — never {} for missing data.
"""

from __future__ import annotations

import platform
import shutil
from pathlib import Path
from typing import Any

from workflow_dataset.capability_discovery.approval_registry import (
    get_registry_path,
    load_approval_registry,
    normalize_approved_paths,
)
from workflow_dataset.local_operator.state_store import get_operator_state_path, load_operator_state


def _repo(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def count_active_approved_folders(repo_root: Path | str | None = None) -> int:
    reg_path = get_registry_path(repo_root)
    if not reg_path.exists():
        return 0
    reg = load_approval_registry(repo_root)
    entries = normalize_approved_paths(
        reg.approved_paths, exclude_template_paths=True
    )
    return sum(1 for e in entries if e.get("revocation_state") == "active")


def build_machine_readiness(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Platform, automation CLI, approval registry presence, active folder count."""
    root = _repo(repo_root)
    reg_path = get_registry_path(root)
    registry_exists = reg_path.is_file()
    n_active = count_active_approved_folders(root)
    osascript = shutil.which("osascript")
    plat = platform.system()
    is_macos = plat == "Darwin"

    parts = [
        f"platform={plat}",
        f"active_approved_folders={n_active}",
        f"registry={'yes' if registry_exists else 'no'}",
        f"osascript={'yes' if osascript else 'no'}",
    ]
    return {
        "platform": plat,
        "is_macos": is_macos,
        "automation_cli_available": bool(osascript),
        "approval_registry_path": str(reg_path),
        "approval_registry_exists": registry_exists,
        "active_approved_folder_count": n_active,
        "summary": "; ".join(parts),
    }


def build_operator_readiness(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Derived from persisted operator state + registry (no fake paths)."""
    root = _repo(repo_root)
    state = load_operator_state(root)
    state_path = get_operator_state_path(root)
    wf = len(state.get("workflow_tree") or [])
    tools = len(state.get("tool_registry") or [])
    proposals = len(state.get("action_proposals") or [])
    n_active = count_active_approved_folders(root)
    last_ex = state.get("last_execution")

    can_ingest = n_active > 0
    has_ingested = wf > 0
    has_tools = tools > 0
    has_proposals = proposals > 0

    steps = []
    if n_active == 0:
        steps.append("add approved folder: workflow-dataset local approved-folders add --path <dir>")
    elif not has_ingested:
        steps.append("run: workflow-dataset local ingest")
    elif not has_tools:
        steps.append("run: workflow-dataset local discover-tools")
    elif not has_proposals:
        steps.append("run: workflow-dataset local propose-actions")
    else:
        steps.append("ready to execute with --action-id and --approved")

    return {
        "operator_state_file": str(state_path),
        "operator_state_exists": state_path.exists(),
        "active_approved_folder_count": n_active,
        "workflow_node_count": wf,
        "tool_registry_count": tools,
        "action_proposals_count": proposals,
        "can_run_ingest": can_ingest,
        "has_ingested_workflow": has_ingested,
        "has_tool_registry": has_tools,
        "has_action_proposals": has_proposals,
        "last_execution": last_ex if isinstance(last_ex, dict) else None,
        "updated_at": state.get("updated_at") or "",
        "next_steps": steps,
        "summary": f"nodes={wf} tools={tools} proposals={proposals} | " + (" | ".join(steps[:2]) if steps else "ok"),
    }
