"""
Supervised execution for local operator actions.
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from workflow_dataset.agent.audit_log import ActionLogRecord, append_log
from workflow_dataset.desktop_adapters.execute import run_execute
from workflow_dataset.local_operator.state_store import load_operator_state, save_operator_state
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _record_last_execution(
    repo_root: Path | str | None,
    *,
    action_id: str,
    success: bool,
    message: str,
    adapter_id: str = "",
    action_type: str = "",
    outcome: str = "",
) -> None:
    try:
        st = load_operator_state(repo_root)
        st["last_execution"] = {
            "action_id": action_id,
            "success": success,
            "message": (message or "")[:500],
            "adapter_id": adapter_id,
            "action_type": action_type,
            "outcome": outcome or ("ok" if success else "failed"),
            "at": utc_now_iso(),
        }
        save_operator_state(st, repo_root)
    except Exception:
        pass


def _rollback_info(action: dict[str, Any]) -> tuple[bool, str, str, str]:
    destructive = bool(action.get("destructive"))
    if destructive:
        return (False, "none", "", "destructive action; rollback not guaranteed")
    return (True, "none", "", "non-destructive action")


def execute_action_proposal(
    action: dict[str, Any],
    repo_root: Path | str | None = None,
    approved: bool = False,
) -> dict[str, Any]:
    """Execute a proposed local action after approval checks."""
    approval_requirement = action.get("approval_requirement", "explicit")
    if approval_requirement == "explicit" and not approved:
        return {"success": False, "message": "Approval required", "log_record": {}}

    state = load_operator_state(repo_root)
    adapter_id = action.get("required_adapter") or action.get("adapter_id") or ""
    aid = str(action.get("action_id") or "")
    capability_entries = state.get("capability_trust") or []
    blocked = next((c for c in capability_entries if c.get("capability_id") == adapter_id and not c.get("ready")), None)
    if blocked:
        _record_last_execution(
            repo_root,
            action_id=aid,
            success=False,
            message="Capability not ready",
            adapter_id=adapter_id,
            action_type=str(action.get("action_type") or ""),
            outcome="blocked",
        )
        return {"success": False, "message": "Capability not ready", "log_record": {}}

    action_id = action.get("action_type") or ""
    params = action.get("params") or {}
    result = run_execute(adapter_id, action_id, params, repo_root=repo_root)

    rollback_feasible, rollback_method, rollback_token, rollback_limitations = _rollback_info(action)
    log = ActionLogRecord(
        log_id=stable_id("log", action.get("action_id", ""), utc_now_iso(), prefix="log"),
        timestamp_utc=utc_now_iso(),
        mode="assist",
        action_type=action_id,
        intent=action.get("label", ""),
        target=params.get("path") or params or "",
        outcome="executed" if result.success else "failed",
        rollback_feasible=rollback_feasible,
        rollback_method=rollback_method,
        rollback_token=rollback_token,
        rollback_limitations=rollback_limitations,
        details={"message": result.message, "output": result.output},
    )
    append_log(repo_root, log)
    _record_last_execution(
        repo_root,
        action_id=aid,
        success=result.success,
        message=result.message,
        adapter_id=adapter_id,
        action_type=action_id,
        outcome="executed" if result.success else "failed",
    )
    return {
        "success": result.success,
        "message": result.message,
        "output": result.output,
        "log_record": log.model_dump(),
    }
