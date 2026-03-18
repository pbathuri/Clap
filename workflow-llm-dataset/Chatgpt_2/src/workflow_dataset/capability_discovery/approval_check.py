"""
M23H: Check execution against approval registry. Used to gate run_execute.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.capability_discovery.approval_registry import (
    ApprovalRegistry,
    get_registry_path,
    load_approval_registry,
)


def _path_under_approved(path_value: str, approved_paths: list[str], repo_root: Path | None) -> bool:
    """True if path_value (resolved) is under one of the approved_paths (resolved)."""
    if not path_value or not approved_paths:
        return len(approved_paths) == 0
    try:
        p = Path(path_value).expanduser().resolve()
        for allowed in approved_paths:
            if not allowed.strip():
                continue
            allowed_path = Path(allowed).expanduser().resolve()
            if repo_root is not None:
                if not allowed_path.is_absolute():
                    allowed_path = (Path(repo_root) / allowed_path).resolve()
            try:
                p.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False


def _scope_allowed(adapter_id: str, action_id: str, approved_scopes: list[dict]) -> bool:
    """True if (adapter_id, action_id) is in approved_scopes with executable true."""
    if not approved_scopes:
        return True
    for s in approved_scopes:
        if str(s.get("adapter_id")) == adapter_id and str(s.get("action_id")) == action_id:
            return s.get("executable") is True
    return False


def check_execution_allowed(
    adapter_id: str,
    action_id: str,
    params: dict,
    repo_root: Path | str | None = None,
    registry: ApprovalRegistry | None = None,
) -> tuple[bool, str]:
    """
    Return (allowed, message). If not allowed, message explains what approval is missing.
    When registry file does not exist: allow (backward compatible).
    When registry exists: enforce approved_paths for path-using actions and approved_action_scopes if non-empty.
    """
    root = Path(repo_root).resolve() if repo_root else None
    reg_path = get_registry_path(root)
    if not reg_path.exists() or not reg_path.is_file():
        return True, ""

    if registry is None:
        registry = load_approval_registry(root)

    approved_paths = getattr(registry, "approved_paths", []) or []
    approved_action_scopes = getattr(registry, "approved_action_scopes", []) or []
    path_value = (params or {}).get("path", "").strip()
    path_using_actions = {
        "inspect_path",
        "list_directory",
        "snapshot_to_sandbox",
        "read_text",
        "summarize_text_for_workflow",
        "propose_status_from_notes",
    }

    if approved_action_scopes and not _scope_allowed(adapter_id, action_id, approved_action_scopes):
        return False, (
            f"Action {adapter_id}.{action_id} not in approved_action_scopes with executable=true. "
            "Add it to data/local/capability_discovery/approvals.yaml approved_action_scopes or remove the registry file."
        )
    if action_id in path_using_actions and path_value:
        if approved_paths and not _path_under_approved(path_value, approved_paths, root):
            return False, (
                f"Path not in approved_paths. Add path to data/local/capability_discovery/approvals.yaml approved_paths "
                "or clear approved_paths to allow all paths."
            )

    return True, ""
