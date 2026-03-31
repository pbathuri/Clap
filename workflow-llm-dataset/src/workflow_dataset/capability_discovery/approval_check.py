"""
M23H: Check execution against approval registry. Used to gate run_execute.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.capability_discovery.approval_registry import (
    ApprovalRegistry,
    get_registry_path,
    load_approval_registry,
    normalize_approved_paths,
)


def _required_operation(adapter_id: str, action_id: str) -> str:
    """Return required operation label for action (read/write/etc)."""
    if adapter_id == "file_ops":
        if action_id in {"inspect_path", "list_directory", "read_file", "list_dir", "read_text", "summarize_text_for_workflow", "propose_status_from_notes", "snapshot_to_sandbox"}:
            return "read"
        if action_id in {"write_file"}:
            return "write"
    if adapter_id == "finder_open":
        if action_id in {"open_folder"}:
            return "read"
    if adapter_id == "notes_document":
        if action_id in {"read_text", "summarize_text_for_workflow", "propose_status_from_notes"}:
            return "read"
        if action_id in {"create_note", "append_to_note"}:
            return "write"
    return ""


def _path_under_approved(
    path_value: str,
    approved_paths: list[dict],
    repo_root: Path | None,
    required_op: str = "",
) -> bool:
    """True if path_value (resolved) is under one of the approved_paths entries."""
    if not path_value or not approved_paths:
        return len(approved_paths) == 0
    try:
        p = Path(path_value).expanduser().resolve()
        for entry in approved_paths:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("revocation_state")) and entry.get("revocation_state") != "active":
                continue
            allowed_ops = list(entry.get("allowed_operations") or [])
            if required_op and allowed_ops and required_op not in allowed_ops:
                continue
            raw_path = str(entry.get("path") or "")
            if not raw_path:
                continue
            allowed_path = Path(raw_path).expanduser()
            if repo_root is not None and not allowed_path.is_absolute():
                allowed_path = (Path(repo_root) / allowed_path).resolve()
            else:
                allowed_path = allowed_path.resolve()
            recursive = bool(entry.get("recursive", True))
            inherit_mode = str(entry.get("inherit_mode") or "inherit")
            if not recursive or inherit_mode == "none":
                if p == allowed_path:
                    return True
                continue
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

    approved_paths = normalize_approved_paths(getattr(registry, "approved_paths", []) or [])
    approved_action_scopes = getattr(registry, "approved_action_scopes", []) or []
    path_value = (params or {}).get("path", "").strip()
    path_using_actions = {
        "inspect_path",
        "list_directory",
        "snapshot_to_sandbox",
        "read_text",
        "summarize_text_for_workflow",
        "propose_status_from_notes",
        "write_file",
        "open_folder",
    }

    if approved_action_scopes and not _scope_allowed(adapter_id, action_id, approved_action_scopes):
        return False, (
            f"Action {adapter_id}.{action_id} not in approved_action_scopes with executable=true. "
            "Add it to data/local/capability_discovery/approvals.yaml approved_action_scopes or remove the registry file."
        )
    if action_id in path_using_actions and path_value:
        required_op = _required_operation(adapter_id, action_id)
        if approved_paths and not _path_under_approved(path_value, approved_paths, root, required_op=required_op):
            return False, (
                f"Path not approved for required operation ({required_op or 'unknown'}). Add path to "
                "data/local/capability_discovery/approvals.yaml approved_paths "
                "or clear approved_paths to allow all paths."
            )

    return True, ""
