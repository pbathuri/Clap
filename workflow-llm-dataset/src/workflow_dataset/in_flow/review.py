"""
M33I–M33L: Contextual review and revision — inspect draft in context, revise, attach notes,
promote to artifact, hand off to approval/planner/executor/workspace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.in_flow.models import (
    DraftArtifact,
    HandoffPackage,
    RevisionEntry,
    REVIEW_STATUS_PROMOTED,
    REVIEW_STATUS_HANDED_OFF,
    REVIEW_STATUS_REVISED,
)
from workflow_dataset.in_flow.store import (
    load_draft,
    save_draft,
    load_handoff,
    save_handoff,
    append_revision,
)
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_draft_in_context(
    draft_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Return draft plus context for review: draft fields, affected step, plan/session refs,
    linked artifacts. Use for inspect-in-context.
    """
    draft = load_draft(draft_id, repo_root=repo_root)
    if not draft:
        return {}
    step = draft.affected_step
    ctx: dict[str, Any] = {
        "draft_id": draft.draft_id,
        "draft_type": draft.draft_type,
        "title": draft.title,
        "content": draft.content,
        "review_status": draft.review_status,
        "project_id": draft.project_id,
        "session_id": draft.session_id,
        "episode_ref": draft.episode_ref,
        "artifact_refs": list(draft.artifact_refs),
        "operator_notes": draft.operator_notes,
        "revision_count": len(draft.revision_history),
        "promoted_artifact_path": draft.promoted_artifact_path,
        "handed_off_to": draft.handed_off_to,
    }
    if step:
        ctx["affected_step"] = {
            "step_index": step.step_index,
            "plan_id": step.plan_id,
            "plan_ref": step.plan_ref,
            "step_label": step.step_label,
            "run_id": step.run_id,
            "episode_id": step.episode_id,
        }
    else:
        ctx["affected_step"] = None
    return ctx


def revise_draft(
    draft_id: str,
    new_content: str,
    summary: str = "",
    note: str = "",
    repo_root: Path | str | None = None,
) -> bool:
    """Update draft content and append a revision entry."""
    draft = load_draft(draft_id, repo_root=repo_root)
    if not draft:
        return False
    draft.content = new_content
    draft.review_status = REVIEW_STATUS_REVISED
    draft.updated_utc = utc_now_iso()
    rev = RevisionEntry(
        revision_id=stable_id("rev", draft_id, draft.updated_utc, prefix="rev_"),
        timestamp_utc=draft.updated_utc,
        summary=summary or "Revised",
        note=note,
    )
    draft.revision_history = list(draft.revision_history) + [rev]
    save_draft(draft, repo_root=repo_root)
    return True


def attach_note(draft_id: str, note: str, repo_root: Path | str | None = None) -> bool:
    """Append to operator_notes (or set if empty)."""
    draft = load_draft(draft_id, repo_root=repo_root)
    if not draft:
        return False
    draft.operator_notes = (draft.operator_notes + "\n" + note).strip() if draft.operator_notes else note
    draft.updated_utc = utc_now_iso()
    save_draft(draft, repo_root=repo_root)
    return True


def promote_to_artifact(
    draft_id: str,
    artifact_path: str,
    repo_root: Path | str | None = None,
) -> bool:
    """
    Mark draft as promoted and record artifact path. Optionally write content to path.
    Does not bypass review; this records the promotion for audit.
    """
    draft = load_draft(draft_id, repo_root=repo_root)
    if not draft:
        return False
    draft.review_status = REVIEW_STATUS_PROMOTED
    draft.promoted_artifact_path = artifact_path
    draft.updated_utc = utc_now_iso()
    root = _repo_root(repo_root)
    path = root / artifact_path if not Path(artifact_path).is_absolute() else Path(artifact_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(draft.content, encoding="utf-8")
    except Exception:
        pass
    save_draft(draft, repo_root=repo_root)
    return True


def handoff_to_target(
    handoff_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Deliver handoff to its target: approval_studio, planner, executor, workspace, artifact.
    Returns outcome dict; does not bypass trust/approval.
    """
    handoff = load_handoff(handoff_id, repo_root=repo_root)
    if not handoff:
        return {"ok": False, "error": "handoff_not_found", "handoff_id": handoff_id}
    root = _repo_root(repo_root)
    now = utc_now_iso()
    outcome: dict[str, Any] = {"ok": True, "handoff_id": handoff_id, "target": handoff.target}

    if handoff.target == "artifact":
        # Write handoff summary to in_flow dir
        out_path = root / "handoffs" / f"{handoff_id}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# {handoff.title}", "", handoff.summary, "", "## Next steps"]
        for s in handoff.next_steps:
            lines.append(f"- {s}")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        outcome["artifact_path"] = str(out_path)
        handoff.delivered_utc = now
        handoff.target_ref = str(out_path)
        save_handoff(handoff, repo_root=repo_root)
    elif handoff.target == "approval_studio":
        outcome["message"] = "Hand off to approval queue: use review studio or supervised_loop to queue for approval."
        handoff.delivered_utc = now
        save_handoff(handoff, repo_root=repo_root)
    elif handoff.target == "planner":
        outcome["message"] = f"Hand off to planner: goal/summary available. Use planner with goal: {handoff.summary[:80]}..."
        handoff.delivered_utc = now
        save_handoff(handoff, repo_root=repo_root)
    elif handoff.target == "executor":
        outcome["message"] = "Hand off to executor: use executor run with plan_ref from handoff context."
        handoff.delivered_utc = now
        save_handoff(handoff, repo_root=repo_root)
    elif handoff.target == "workspace":
        outcome["message"] = "Hand off to workspace: open timeline/inbox with handoff context."
        handoff.delivered_utc = now
        save_handoff(handoff, repo_root=repo_root)
    else:
        outcome["message"] = f"Target '{handoff.target}' recorded; no automatic delivery."
        handoff.delivered_utc = now
        save_handoff(handoff, repo_root=repo_root)

    # Mark linked drafts as handed_off
    for did in handoff.draft_ids:
        d = load_draft(did, repo_root=repo_root)
        if d:
            d.review_status = REVIEW_STATUS_HANDED_OFF
            d.handed_off_to = handoff.target
            d.updated_utc = now
            save_draft(d, repo_root=repo_root)
    return outcome
