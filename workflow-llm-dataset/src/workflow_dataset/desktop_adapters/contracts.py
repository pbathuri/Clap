"""
M23C-F1: Desktop action adapter contract schema.
Each adapter defines id, type, capability, supported actions, approvals, simulate/real flags, inputs/outputs, failure modes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActionSpec:
    """One action supported by an adapter."""
    action_id: str
    description: str
    expected_inputs: list[dict[str, str]]  # [{"name": "path", "type": "string", "required": "true"}]
    expected_outputs: list[str]
    supports_simulate: bool = True
    supports_real: bool = False


@dataclass
class AdapterContract:
    """Contract for a desktop action adapter. Local-first, simulate-first."""
    adapter_id: str
    adapter_type: str  # file_ops | notes_document | browser_open | app_launch
    capability_description: str
    supported_actions: list[ActionSpec] = field(default_factory=list)
    required_approvals: list[str] = field(default_factory=list)  # e.g. ["user_confirm"]
    supports_simulate: bool = True
    supports_real_execution: bool = False
    expected_inputs: list[dict[str, str]] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)


def _file_ops_contract() -> AdapterContract:
    return AdapterContract(
        adapter_id="file_ops",
        adapter_type="file_ops",
        capability_description="Local file and folder: inspect, list, read, snapshot to sandbox. F2: read-only + copy to sandbox only; no mutation of originals.",
        supported_actions=[
            ActionSpec("read_file", "Read file contents", [{"name": "path", "type": "string", "required": "true"}], ["content"], True, False),
            ActionSpec("list_dir", "List directory contents", [{"name": "path", "type": "string", "required": "true"}], ["entries"], True, False),
            ActionSpec("write_file", "Write content to file (simulate: preview only)", [{"name": "path", "type": "string", "required": "true"}, {"name": "content", "type": "string", "required": "false"}], ["path"], True, False),
            # F2: inspect/list/snapshot with real read-only or sandbox-only execution
            ActionSpec("inspect_path", "Inspect path metadata (exists, is_file, is_dir, size, mtime)", [{"name": "path", "type": "string", "required": "true"}], ["metadata"], True, True),
            ActionSpec("list_directory", "List directory entries (names and types)", [{"name": "path", "type": "string", "required": "true"}], ["entries"], True, True),
            ActionSpec("snapshot_to_sandbox", "Copy file or dir into sandbox; originals unchanged", [{"name": "path", "type": "string", "required": "true"}, {"name": "subdir", "type": "string", "required": "false"}], ["sandbox_path"], True, True),
        ],
        required_approvals=["user_confirm_for_write"],
        supports_simulate=True,
        supports_real_execution=True,
        failure_modes=["path_not_found", "permission_denied", "disk_full"],
    )


def _notes_document_contract() -> AdapterContract:
    return AdapterContract(
        adapter_id="notes_document",
        adapter_type="notes_document",
        capability_description="Notes and text: read, summarize, propose status. F2: read-only; no mutation of originals.",
        supported_actions=[
            ActionSpec("create_note", "Create a new note file", [{"name": "path", "type": "string", "required": "true"}, {"name": "title", "type": "string", "required": "false"}], ["path"], True, False),
            ActionSpec("append_to_note", "Append content to note (simulate: preview)", [{"name": "path", "type": "string", "required": "true"}, {"name": "content", "type": "string", "required": "true"}], ["path"], True, False),
            # F2: read-only text actions
            ActionSpec("read_text", "Read text file content (UTF-8)", [{"name": "path", "type": "string", "required": "true"}], ["content"], True, True),
            ActionSpec("summarize_text_for_workflow", "Summarize text for workflow context", [{"name": "path", "type": "string", "required": "true"}], ["summary"], True, True),
            ActionSpec("propose_status_from_notes", "Propose status lines from notes (suggested actions; no write)", [{"name": "path", "type": "string", "required": "true"}], ["suggested_lines"], True, True),
        ],
        required_approvals=["user_confirm_for_write"],
        supports_simulate=True,
        supports_real_execution=True,
        failure_modes=["path_not_found", "not_a_text_file"],
    )


def _browser_open_contract() -> AdapterContract:
    return AdapterContract(
        adapter_id="browser_open",
        adapter_type="browser_open",
        capability_description="Open URL in browser. F3: simulate only; validate local/allowed URL (http, https, file, localhost); preview what would be opened.",
        supported_actions=[
            ActionSpec("open_url", "Open URL in default browser (simulate: validate + preview)", [{"name": "url", "type": "string", "required": "true"}], ["opened"], True, False),
        ],
        required_approvals=["user_confirm_before_open"],
        supports_simulate=True,
        supports_real_execution=False,
        failure_modes=["invalid_url", "scheme_not_allowed", "browser_not_available"],
    )


def _app_launch_contract() -> AdapterContract:
    return AdapterContract(
        adapter_id="app_launch",
        adapter_type="app_launch",
        capability_description="Launch application. F3: simulate only; resolve approved app names; preview what would be launched.",
        supported_actions=[
            ActionSpec("launch_app", "Launch application (simulate: resolve + preview)", [{"name": "app_name_or_path", "type": "string", "required": "true"}, {"name": "args", "type": "string", "required": "false"}], ["launched"], True, False),
        ],
        required_approvals=["user_confirm_before_launch"],
        supports_simulate=True,
        supports_real_execution=False,
        failure_modes=["app_not_found", "app_not_approved", "launch_failed"],
    )


BUILTIN_ADAPTERS: list[AdapterContract] = [
    _file_ops_contract(),
    _notes_document_contract(),
    _browser_open_contract(),
    _app_launch_contract(),
]
