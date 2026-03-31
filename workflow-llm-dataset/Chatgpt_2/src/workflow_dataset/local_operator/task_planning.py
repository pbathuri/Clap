"""
Prompt-to-plan generation for local operator workflows.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from workflow_dataset.local_operator.approved_folders import list_approved_folders
from workflow_dataset.local_operator.task_store import save_task_plan
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

WORKFLOW_PATTERNS = ("inspect_status_report", "inspect_project_brief", "inspect_finder_report")

UNSUPPORTED_USER_HINTS: dict[str, str] = {
    "no_approved_folders": (
        "No active approved folders with write scope were found. Add one (e.g. "
        "`workflow-dataset local approved-folders add --path <dir> --ops read --ops write`) "
        "then run `workflow-dataset local ingest`."
    ),
    "no_write_scope": (
        "Approved folders exist but none allow `write`. Task runs need write permission "
        "to create artifacts under the approved folder. Update registry ops to include `write`."
    ),
    "unsupported_prompt_intent": (
        "This prompt does not match a supported bounded workflow. Try explicit intent such as: "
        "inspect/summarize folder or structured status report; project brief; "
        "or open in Finder + report."
    ),
}


def _user_hint_for_reason(reason: str) -> str:
    return UNSUPPORTED_USER_HINTS.get(reason, "")


def _infer_workflow_pattern(prompt: str) -> str | None:
    """
    Infer one of the supported bounded workflow patterns.
    Return None when prompt intent is unsupported.
    """
    text = (prompt or "").lower()
    if any(k in text for k in ("open folder", "open in finder", "finder", "show folder")):
        return "inspect_finder_report"
    if any(k in text for k in ("project brief", "project", "work context", "context brief", "brief")):
        return "inspect_project_brief"
    if any(
        k in text
        for k in (
            "status report",
            "structured report",
            "structured status",
            "summarize folder",
            "summarize files",
            "inspect folder",
            "summary report",
        )
    ):
        return "inspect_status_report"
    return None


def _build_plan_steps(workflow_pattern: str, scope_path: str) -> list[dict[str, Any]]:
    if workflow_pattern == "inspect_status_report":
        return [
            {
                "step_id": "list_directory",
                "adapter_id": "file_ops",
                "action_id": "list_directory",
                "params": {"path": scope_path},
            },
            {
                "step_id": "identify_relevant_files",
                "adapter_id": "internal",
                "action_id": "identify_relevant_files",
                "params": {"path": scope_path},
            },
            {
                "step_id": "summarize_notes",
                "adapter_id": "notes_document",
                "action_id": "summarize_text_for_workflow",
                "params": {"path": "<auto>"},
                "optional": True,
            },
            {
                "step_id": "write_artifact",
                "adapter_id": "file_ops",
                "action_id": "write_file",
                "params": {"path": "<auto>", "content": "<auto>"},
            },
        ]
    if workflow_pattern == "inspect_project_brief":
        return [
            {
                "step_id": "list_directory",
                "adapter_id": "file_ops",
                "action_id": "list_directory",
                "params": {"path": scope_path},
            },
            {
                "step_id": "infer_project_context",
                "adapter_id": "internal",
                "action_id": "infer_project_context",
                "params": {"path": scope_path},
            },
            {
                "step_id": "summarize_notes",
                "adapter_id": "notes_document",
                "action_id": "summarize_text_for_workflow",
                "params": {"path": "<auto>"},
                "optional": True,
            },
            {
                "step_id": "write_artifact",
                "adapter_id": "file_ops",
                "action_id": "write_file",
                "params": {"path": "<auto>", "content": "<auto>"},
            },
        ]
    if workflow_pattern == "inspect_finder_report":
        return [
            {
                "step_id": "list_directory",
                "adapter_id": "file_ops",
                "action_id": "list_directory",
                "params": {"path": scope_path},
            },
            {
                "step_id": "open_finder",
                "adapter_id": "finder_open",
                "action_id": "open_folder",
                "params": {"path": scope_path},
                "optional": True,
            },
            {
                "step_id": "summarize_notes",
                "adapter_id": "notes_document",
                "action_id": "summarize_text_for_workflow",
                "params": {"path": "<auto>"},
                "optional": True,
            },
            {
                "step_id": "write_artifact",
                "adapter_id": "file_ops",
                "action_id": "write_file",
                "params": {"path": "<auto>", "content": "<auto>"},
            },
        ]
    return []


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _allows_write(entry: dict[str, Any]) -> bool:
    allowed = entry.get("allowed_operations")
    if allowed is None:
        return True
    if isinstance(allowed, list) and not allowed:
        return True
    return "write" in {str(op).lower() for op in (allowed or [])}


def _choose_scope(prompt: str, entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not entries:
        return None
    prompt_l = (prompt or "").lower()
    prompt_norm = _normalize(prompt or "")
    for entry in entries:
        path = str(entry.get("path") or "")
        name = Path(path).name.lower()
        name_norm = _normalize(name)
        if name and name in prompt_l:
            return entry
        if name_norm and name_norm in prompt_norm:
            return entry
        if path and path.lower() in prompt_l:
            return entry
    return entries[0]


def plan_task(prompt: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    active_entries = [
        entry
        for entry in list_approved_folders(repo_root)
        if entry.get("revocation_state") == "active"
    ]
    ts = utc_now_iso()
    plan_id = stable_id("plan", prompt, ts, prefix="plan")
    if not active_entries:
        reason = "no_approved_folders"
        plan = {
            "plan_id": plan_id,
            "prompt": prompt,
            "status": "unsupported",
            "reason": reason,
            "user_hint": _user_hint_for_reason(reason),
            "supported_workflow_patterns": list(WORKFLOW_PATTERNS),
            "approved": False,
            "created_at": ts,
            "approved_scope": {},
            "steps": [],
        }
        save_task_plan(plan, repo_root)
        return plan
    writable_entries = [entry for entry in active_entries if _allows_write(entry)]
    if not writable_entries:
        reason = "no_write_scope"
        plan = {
            "plan_id": plan_id,
            "prompt": prompt,
            "status": "unsupported",
            "reason": reason,
            "user_hint": _user_hint_for_reason(reason),
            "supported_workflow_patterns": list(WORKFLOW_PATTERNS),
            "approved": False,
            "created_at": ts,
            "approved_scope": {},
            "steps": [],
        }
        save_task_plan(plan, repo_root)
        return plan
    workflow_pattern = _infer_workflow_pattern(prompt)
    if workflow_pattern is None:
        reason = "unsupported_prompt_intent"
        plan = {
            "plan_id": plan_id,
            "prompt": prompt,
            "status": "unsupported",
            "reason": reason,
            "user_hint": _user_hint_for_reason(reason),
            "supported_workflow_patterns": list(WORKFLOW_PATTERNS),
            "approved": False,
            "created_at": ts,
            "approved_scope": {},
            "steps": [],
        }
        save_task_plan(plan, repo_root)
        return plan
    ordered_entries = sorted(writable_entries, key=lambda entry: str(entry.get("path") or ""))
    scope = _choose_scope(prompt, ordered_entries)
    path = str(scope.get("path") or "")
    steps = _build_plan_steps(workflow_pattern, path)
    plan = {
        "plan_id": plan_id,
        "prompt": prompt,
        "status": "planned",
        "reason": "",
        "approved": False,
        "created_at": ts,
        "workflow_pattern": workflow_pattern,
        "approved_scope": {"path": path},
        "steps": steps,
    }
    save_task_plan(plan, repo_root)
    return plan
