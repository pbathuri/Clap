"""
M29I–M29L: Review studio — get item, inspect, accept/reject/defer, link to entity.
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

from workflow_dataset.review_studio.models import InterventionItem, ITEM_APPROVAL_QUEUE, ITEM_BLOCKED_RUN, ITEM_SKILL_CANDIDATE, ITEM_REPLAN_RECOMMENDATION, ITEM_STALLED_INTERVENTION, ITEM_POLICY_EXCEPTION
from workflow_dataset.review_studio.inbox import build_inbox
from workflow_dataset.review_studio.store import save_operator_note, load_operator_notes


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_item(item_id: str, repo_root: Path | str | None = None) -> InterventionItem | None:
    """Find inbox item by id (from current inbox build)."""
    root = _repo_root(repo_root)
    items = build_inbox(root, status="", limit=200)
    for i in items:
        if i.item_id == item_id:
            return i
    return None


def inspect_item(item_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return why this item matters and link commands (project, session, plan, run, lane, pack)."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Inbox item not found: {item_id}"}
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "item_id": item.item_id,
        "kind": item.kind,
        "status": item.status,
        "summary": item.summary,
        "priority": item.priority,
        "source_ref": item.source_ref,
        "entity_refs": dict(item.entity_refs),
        "operator_notes": item.operator_notes,
        "why_matters": "",
        "link_commands": [],
    }
    if item.kind == ITEM_APPROVAL_QUEUE:
        out["why_matters"] = "Proposed agent action awaiting approval; approve/reject/defer to advance or block."
        out["link_commands"] = [f"workflow-dataset agent-loop queue", f"workflow-dataset agent-loop approve --id {item.source_ref}"]
    elif item.kind == ITEM_BLOCKED_RUN:
        out["why_matters"] = "Executor run is blocked at a checkpoint; resume with retry/skip/substitute."
        out["link_commands"] = [f"workflow-dataset executor resume-from-blocked --run {item.source_ref} --decision retry"]
    elif item.kind == ITEM_SKILL_CANDIDATE:
        out["why_matters"] = "Draft skill from teaching; accept or reject to promote or discard."
        out["link_commands"] = [f"workflow-dataset teaching accept-skill {item.source_ref}", f"workflow-dataset teaching reject-skill {item.source_ref}"]
    elif item.kind == ITEM_REPLAN_RECOMMENDATION:
        out["why_matters"] = "Replan suggested for project; run replan recommend and accept/diff to update plan."
        project_id = item.entity_refs.get("project_id", "")
        out["link_commands"] = [f"workflow-dataset replan recommend --project {project_id}", f"workflow-dataset progress board"]
    elif item.kind == ITEM_STALLED_INTERVENTION:
        out["why_matters"] = "Project stalled; review recovery playbook and unblock or replan."
        out["link_commands"] = [f"workflow-dataset progress recovery --project {item.source_ref}", f"workflow-dataset progress board"]
    elif item.kind == ITEM_POLICY_EXCEPTION:
        out["why_matters"] = "Active policy override; review and revoke if no longer needed."
        out["link_commands"] = [f"workflow-dataset policy board", f"workflow-dataset policy revoke --id {item.source_ref}"]
    else:
        out["why_matters"] = "Review and take action as appropriate."
    return out


def accept_item(item_id: str, note: str = "", repo_root: Path | str | None = None) -> dict[str, Any]:
    """Accept/resolve item; delegates to agent-loop approve, teaching accept_skill, or records note."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Inbox item not found: {item_id}"}
    root = _repo_root(repo_root)
    if note:
        save_operator_note(item_id, note, root)

    if item.kind == ITEM_APPROVAL_QUEUE:
        try:
            from workflow_dataset.supervised_loop.cli import cmd_approve
            result = cmd_approve(queue_id=item.source_ref, note=note, repo_root=str(root), run_after=True)
            return {"ok": True, "kind": item.kind, "source_ref": item.source_ref, "result": result}
        except Exception as e:
            return {"error": str(e), "kind": item.kind}
    if item.kind == ITEM_SKILL_CANDIDATE:
        try:
            from workflow_dataset.teaching.review import accept_skill
            skill = accept_skill(item.source_ref, operator_notes=note, repo_root=root)
            return {"ok": True, "kind": item.kind, "source_ref": item.source_ref, "skill": skill.skill_id if skill else ""}
        except Exception as e:
            return {"error": str(e), "kind": item.kind}
    return {"ok": True, "kind": item.kind, "note": "Recorded; no automatic accept action for this kind."}


def reject_item(item_id: str, note: str = "", repo_root: Path | str | None = None) -> dict[str, Any]:
    """Reject item; delegates to agent-loop reject or teaching reject_skill."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Inbox item not found: {item_id}"}
    root = _repo_root(repo_root)
    if note:
        save_operator_note(item_id, note, root)

    if item.kind == ITEM_APPROVAL_QUEUE:
        try:
            from workflow_dataset.supervised_loop.cli import cmd_reject
            cmd_reject(queue_id=item.source_ref, note=note, repo_root=str(root))
            return {"ok": True, "kind": item.kind, "source_ref": item.source_ref}
        except Exception as e:
            return {"error": str(e), "kind": item.kind}
    if item.kind == ITEM_SKILL_CANDIDATE:
        try:
            from workflow_dataset.teaching.review import reject_skill
            skill = reject_skill(item.source_ref, operator_notes=note, repo_root=root)
            return {"ok": True, "kind": item.kind, "source_ref": item.source_ref}
        except Exception as e:
            return {"error": str(e), "kind": item.kind}
    return {"ok": True, "kind": item.kind, "note": "Recorded; no automatic reject action for this kind."}


def defer_item(item_id: str, note: str = "", revisit_after: str = "", repo_root: Path | str | None = None) -> dict[str, Any]:
    """Defer item; delegates to agent-loop defer when applicable."""
    item = get_item(item_id, repo_root)
    if not item:
        return {"error": f"Inbox item not found: {item_id}"}
    root = _repo_root(repo_root)
    if note:
        save_operator_note(item_id, note, root)

    if item.kind == ITEM_APPROVAL_QUEUE:
        try:
            from workflow_dataset.supervised_loop.cli import cmd_defer
            cmd_defer(queue_id=item.source_ref, note=note, defer_reason=note, revisit_after=revisit_after, repo_root=str(root))
            return {"ok": True, "kind": item.kind, "source_ref": item.source_ref, "revisit_after": revisit_after}
        except Exception as e:
            return {"error": str(e), "kind": item.kind}
    return {"ok": True, "kind": item.kind, "note": "Recorded; no automatic defer action for this kind.", "revisit_after": revisit_after}
