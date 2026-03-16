"""
M23C-F2: Execute read-only and sandbox-only adapter actions. No mutation of originals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.desktop_adapters.registry import get_adapter
from workflow_dataset.desktop_adapters.file_runner import (
    run_inspect_path,
    run_list_directory,
    run_snapshot_to_sandbox,
)
from workflow_dataset.desktop_adapters.notes_runner import (
    run_read_text,
    run_summarize_text_for_workflow,
    run_propose_status_from_notes,
)
from workflow_dataset.desktop_adapters.sandbox_config import get_sandbox_root
from workflow_dataset.capability_discovery.approval_check import check_execution_allowed


def _utc_iso() -> str:
    try:
        from workflow_dataset.utils.dates import utc_now_iso
        return utc_now_iso()
    except Exception:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


@dataclass
class ProvenanceEntry:
    adapter_id: str
    action_id: str
    path_or_param: str
    timestamp_iso: str
    outcome: str  # ok | error
    detail: str = ""


@dataclass
class ExecuteResult:
    success: bool
    adapter_id: str
    action_id: str
    message: str
    output: dict[str, Any] = field(default_factory=dict)
    provenance: list[ProvenanceEntry] = field(default_factory=list)


def run_execute(
    adapter_id: str,
    action_id: str,
    params: dict[str, Any],
    sandbox_root: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> ExecuteResult:
    """
    Execute adapter action for file_ops and notes_document (read-only or sandbox copy only).
    When approval registry exists, enforces approved_paths and approved_action_scopes (M23H).
    Returns ExecuteResult with output and provenance. Unknown adapter/action returns success=False.
    """
    params = params or {}
    adapter = get_adapter(adapter_id)
    if not adapter:
        return ExecuteResult(
            success=False,
            adapter_id=adapter_id,
            action_id=action_id,
            message=f"Adapter not found: {adapter_id}",
        )
    action_spec = next((a for a in adapter.supported_actions if a.action_id == action_id), None)
    if not action_spec:
        return ExecuteResult(
            success=False,
            adapter_id=adapter_id,
            action_id=action_id,
            message=f"Action '{action_id}' not found for adapter '{adapter_id}'.",
        )
    if not action_spec.supports_real:
        return ExecuteResult(
            success=False,
            adapter_id=adapter_id,
            action_id=action_id,
            message=f"Real execution not supported for action '{action_id}'.",
        )

    allowed, refusal_msg = check_execution_allowed(
        adapter_id, action_id, params, repo_root=repo_root
    )
    if not allowed:
        return ExecuteResult(
            success=False,
            adapter_id=adapter_id,
            action_id=action_id,
            message=refusal_msg or "Execution not approved.",
        )

    path = (params.get("path") or "").strip()
    ts = _utc_iso()

    if adapter_id == "file_ops":
        if action_id == "inspect_path":
            res = run_inspect_path(path)
            if res.error:
                return ExecuteResult(
                    success=False,
                    adapter_id=adapter_id,
                    action_id=action_id,
                    message=res.error,
                    provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "error", res.error)],
                )
            out = {
                "exists": res.exists,
                "is_file": res.is_file,
                "is_dir": res.is_dir,
                "size_bytes": res.size_bytes,
                "mtime_iso": res.mtime_iso,
            }
            return ExecuteResult(
                success=True,
                adapter_id=adapter_id,
                action_id=action_id,
                message="ok",
                output=out,
                provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "ok", "inspect_path")],
            )
        if action_id == "list_directory":
            res = run_list_directory(path)
            if res.error:
                return ExecuteResult(
                    success=False,
                    adapter_id=adapter_id,
                    action_id=action_id,
                    message=res.error,
                    provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "error", res.error)],
                )
            return ExecuteResult(
                success=True,
                adapter_id=adapter_id,
                action_id=action_id,
                message="ok",
                output={"entries": res.entries},
                provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "ok", f"{len(res.entries)} entries")],
            )
        if action_id == "snapshot_to_sandbox":
            root = Path(sandbox_root) if sandbox_root is not None else get_sandbox_root()
            subdir = (params.get("subdir") or "").strip() or None
            res = run_snapshot_to_sandbox(path, root, subdir)
            if res.error:
                return ExecuteResult(
                    success=False,
                    adapter_id=adapter_id,
                    action_id=action_id,
                    message=res.error,
                    provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "error", res.error)],
                )
            return ExecuteResult(
                success=True,
                adapter_id=adapter_id,
                action_id=action_id,
                message="ok",
                output={"sandbox_path": res.sandbox_path, "copied_count": res.copied_count},
                provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "ok", res.sandbox_path)],
            )

    if adapter_id == "notes_document":
        if action_id == "read_text":
            res = run_read_text(path)
            if res.error:
                return ExecuteResult(
                    success=False,
                    adapter_id=adapter_id,
                    action_id=action_id,
                    message=res.error,
                    provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "error", res.error)],
                )
            return ExecuteResult(
                success=True,
                adapter_id=adapter_id,
                action_id=action_id,
                message="ok",
                output={"content": res.content},
                provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "ok", f"{len(res.content)} chars")],
            )
        if action_id == "summarize_text_for_workflow":
            res = run_summarize_text_for_workflow(path)
            if res.error:
                return ExecuteResult(
                    success=False,
                    adapter_id=adapter_id,
                    action_id=action_id,
                    message=res.error,
                    provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "error", res.error)],
                )
            return ExecuteResult(
                success=True,
                adapter_id=adapter_id,
                action_id=action_id,
                message="ok",
                output={"summary": res.summary},
                provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "ok", "summarized")],
            )
        if action_id == "propose_status_from_notes":
            res = run_propose_status_from_notes(path)
            if res.error:
                return ExecuteResult(
                    success=False,
                    adapter_id=adapter_id,
                    action_id=action_id,
                    message=res.error,
                    provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "error", res.error)],
                )
            return ExecuteResult(
                success=True,
                adapter_id=adapter_id,
                action_id=action_id,
                message="ok",
                output={"suggested_lines": res.suggested_lines},
                provenance=[ProvenanceEntry(adapter_id, action_id, path, ts, "ok", f"{len(res.suggested_lines)} lines")],
            )

    return ExecuteResult(
        success=False,
        adapter_id=adapter_id,
        action_id=action_id,
        message=f"Execute not implemented for {adapter_id}/{action_id}",
    )
