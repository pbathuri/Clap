"""
M34I–M34L: Review and follow-up flows — inspect, accept, archive, dismiss, escalate, attach note.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.automation_inbox.models import (
    AutomationInboxItem,
    ITEM_BLOCKED_AUTOMATION,
    ITEM_FAILED_SUPPRESSED,
    ITEM_AUTOMATION_RESULT,
    STATUS_ACCEPTED,
    STATUS_ARCHIVED,
    STATUS_DISMISSED,
    STATUS_ESCALATED,
)
from workflow_dataset.automation_inbox.collect import build_automation_inbox
from workflow_dataset.automation_inbox.store import (
    save_decision,
    save_operator_note,
    get_latest_decision,
    load_operator_notes,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_item(item_id: str, repo_root: Path | str | None = None) -> AutomationInboxItem | None:
    """Get automation inbox item by id from current inbox build."""
    root = _repo_root(repo_root)
    items = build_automation_inbox(repo_root=root, status="", limit=200)
    for i in items:
        if i.item_id == item_id:
            dec = get_latest_decision(item_id, root)
            if dec:
                i.status = dec.get("decision", i.status)
            notes = load_operator_notes(root)
            if i.item_id in notes:
                i.operator_notes = notes[i.item_id]
            return i
    return None


def inspect_item(item_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return why this item matters and link commands (planner, workspace, review)."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Automation inbox item not found: {item_id}"}
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "item_id": item.item_id,
        "kind": item.kind,
        "status": item.status,
        "summary": item.summary,
        "priority": item.priority,
        "run_id": item.run_id,
        "automation_id": item.automation_id,
        "plan_ref": item.plan_ref,
        "outcome_summary": item.outcome_summary,
        "failure_code": item.failure_code,
        "operator_notes": item.operator_notes,
        "why_matters": "",
        "link_commands": [],
    }
    if item.kind == ITEM_BLOCKED_AUTOMATION:
        out["why_matters"] = "Background run is blocked; review and retry, skip, or escalate to planner/workspace."
        out["link_commands"] = [
            "workflow-dataset automation-inbox escalate --id " + item_id,
            "workflow-dataset background run --run-id " + item.run_id if item.run_id else "",
        ]
    elif item.kind == ITEM_FAILED_SUPPRESSED:
        out["why_matters"] = "Automation failed or was suppressed by policy; inspect reason and decide to retry or dismiss."
        out["link_commands"] = [
            "workflow-dataset automation-inbox accept --id " + item_id,
            "workflow-dataset automation-inbox dismiss --id " + item_id,
        ]
    elif item.kind == ITEM_AUTOMATION_RESULT:
        out["why_matters"] = "Completed automation result; accept to archive or dismiss if not needed."
        out["link_commands"] = [
            "workflow-dataset automation-inbox accept --id " + item_id,
            "workflow-dataset automation-inbox archive --id " + item_id,
        ]
    else:
        out["why_matters"] = "Review and take action (accept, archive, dismiss, or escalate)."
        out["link_commands"] = [
            "workflow-dataset automation-inbox accept --id " + item_id,
            "workflow-dataset automation-inbox escalate --id " + item_id,
        ]
    return out


def accept_item(item_id: str, note: str = "", repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark item as accepted (reviewed and acknowledged)."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Automation inbox item not found: {item_id}"}
    root = _repo_root(repo_root)
    if note:
        save_operator_note(item_id, note, root)
    save_decision(item_id, STATUS_ACCEPTED, note=note, repo_root=root)
    return {"ok": True, "item_id": item_id, "decision": STATUS_ACCEPTED}


def archive_item(item_id: str, note: str = "", repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark item as archived (kept for record, no further action)."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Automation inbox item not found: {item_id}"}
    root = _repo_root(repo_root)
    if note:
        save_operator_note(item_id, note, root)
    save_decision(item_id, STATUS_ARCHIVED, note=note, repo_root=root)
    return {"ok": True, "item_id": item_id, "decision": STATUS_ARCHIVED}


def dismiss_item(item_id: str, note: str = "", repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark item as dismissed (no action needed)."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Automation inbox item not found: {item_id}"}
    root = _repo_root(repo_root)
    if note:
        save_operator_note(item_id, note, root)
    save_decision(item_id, STATUS_DISMISSED, note=note, repo_root=root)
    return {"ok": True, "item_id": item_id, "decision": STATUS_DISMISSED}


def escalate_item(item_id: str, note: str = "", repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark item as escalated (reopen into planner/workspace/review); record decision."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Automation inbox item not found: {item_id}"}
    root = _repo_root(repo_root)
    if note:
        save_operator_note(item_id, note, root)
    save_decision(item_id, STATUS_ESCALATED, note=note, repo_root=root)
    link_commands = [
        "workflow-dataset inbox list",
        "workflow-dataset live-workflow now --goal \"<goal>\"",
    ]
    if item.run_id:
        link_commands.append(f"workflow-dataset background run (run_id={item.run_id})")
    return {"ok": True, "item_id": item_id, "decision": STATUS_ESCALATED, "link_commands": link_commands}


def attach_operator_note(item_id: str, note: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Attach or update operator note for an item."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Automation inbox item not found: {item_id}"}
    save_operator_note(item_id, note, _repo_root(repo_root))
    return {"ok": True, "item_id": item_id}
