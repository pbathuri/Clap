"""
M23C-F1: Simulate-first action runner. Dry-run only; no real execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_dataset.desktop_adapters.registry import get_adapter


@dataclass
class SimulateResult:
    """Result of a simulate/dry-run action. No real execution."""
    success: bool
    adapter_id: str
    action_id: str
    message: str
    preview: str = ""
    params_used: dict[str, Any] = field(default_factory=dict)
    real_execution_supported: bool = False


def run_simulate(adapter_id: str, action_id: str, params: dict[str, Any] | None = None) -> SimulateResult:
    """
    Run an adapter action in simulate mode. Dry-run only; no OS/file/browser changes.
    Returns SimulateResult with preview and message. If adapter or action unknown, success=False.
    """
    params = params or {}
    adapter = get_adapter(adapter_id)
    if not adapter:
        return SimulateResult(
            success=False,
            adapter_id=adapter_id,
            action_id=action_id,
            message=f"Adapter not found: {adapter_id}",
        )
    action_spec = next((a for a in adapter.supported_actions if a.action_id == action_id), None)
    if not action_spec:
        return SimulateResult(
            success=False,
            adapter_id=adapter_id,
            action_id=action_id,
            message=f"Action '{action_id}' not found for adapter '{adapter_id}'. Supported: {[a.action_id for a in adapter.supported_actions]}",
        )

    # Dry-run preview only; no real execution
    preview_parts: list[str] = []
    preview_parts.append(f"[Simulate] adapter={adapter_id} action={action_id}")
    for k, v in params.items():
        preview_parts.append(f"  {k}={v}")

    if adapter_id == "browser_open" and action_id == "open_url":
        from workflow_dataset.desktop_adapters.url_validation import validate_local_or_allowed_url
        url = params.get("url", "")
        preview_parts.append(f"  URL: {url}")
        v = validate_local_or_allowed_url(url)
        if v.valid:
            preview_parts.append(f"  Validation: ok (category={v.category})")
            preview_parts.append("  Would open URL in browser (simulate only; F3).")
        else:
            preview_parts.append(f"  Validation: invalid — {v.reason}")
            preview_parts.append("  Would not open; fix URL and retry.")
    elif adapter_id == "file_ops":
        path = params.get("path", "")
        preview_parts.append(f"  Target path: {path}")
        if action_id == "read_file":
            preview_parts.append("  Would read file contents.")
        elif action_id == "list_dir":
            preview_parts.append("  Would list directory.")
        elif action_id == "write_file":
            preview_parts.append("  Would write content (preview only).")
        elif action_id == "inspect_path":
            preview_parts.append("  Would inspect path metadata (exists, is_file, is_dir, size, mtime).")
        elif action_id == "list_directory":
            preview_parts.append("  Would list directory entries.")
        elif action_id == "snapshot_to_sandbox":
            subdir = params.get("subdir", "")
            preview_parts.append(f"  Would copy to sandbox (subdir={subdir or '(none)'}).")
        else:
            preview_parts.append("  (Preview for this action.)")
        if action_id in ("read_file", "list_dir", "write_file"):
            preview_parts.append("  Real execution not implemented in F1.")
    elif adapter_id == "notes_document":
        path = params.get("path", "")
        preview_parts.append(f"  Target path: {path}")
        if action_id in ("create_note", "append_to_note"):
            preview_parts.append("  Would create/append note.")
            preview_parts.append("  Real execution not implemented in F1.")
        elif action_id == "read_text":
            preview_parts.append("  Would read text content.")
        elif action_id == "summarize_text_for_workflow":
            preview_parts.append("  Would summarize text for workflow.")
        elif action_id == "propose_status_from_notes":
            preview_parts.append("  Would propose status lines from notes.")
        else:
            preview_parts.append("  Would create/append note.")
    elif adapter_id == "app_launch":
        from workflow_dataset.desktop_adapters.app_allowlist import resolve_app_display_name
        app = params.get("app_name_or_path", "")
        resolved = resolve_app_display_name(app)
        preview_parts.append(f"  App: {app}")
        if resolved:
            preview_parts.append(f"  Resolved (approved): {resolved}")
        else:
            preview_parts.append("  Resolved: not in approved list (preview only).")
        preview_parts.append("  Would launch app (simulate only; F3).")
    else:
        preview_parts.append("  (No custom preview for this adapter/action.)")

    return SimulateResult(
        success=True,
        adapter_id=adapter_id,
        action_id=action_id,
        message="Simulate completed (dry-run; no changes made).",
        preview="\n".join(preview_parts),
        params_used=dict(params),
        real_execution_supported=action_spec.supports_real,
    )
