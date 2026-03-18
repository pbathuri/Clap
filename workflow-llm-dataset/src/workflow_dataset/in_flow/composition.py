"""
M33I–M33L: In-flow composition — create drafts, handoffs, stage summaries/checklists/decisions.
Tied to active workflow episode, step, project, session, artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.in_flow.models import (
    DraftArtifact,
    HandoffPackage,
    ReviewCheckpoint,
    StagedSummary,
    StagedChecklist,
    StagedDecisionRequest,
    AffectedWorkflowStep,
    DRAFT_TYPE_STATUS_SUMMARY,
    DRAFT_TYPE_REVIEW_CHECKLIST,
    DRAFT_TYPE_NEXT_STEP_HANDOFF_BRIEF,
    DRAFT_TYPE_BLOCKED_ESCALATION_NOTE,
    DRAFT_TYPE_MEETING_FOLLOW_UP,
    DRAFT_TYPE_APPROVAL_REQUEST_SUMMARY,
    DRAFT_TYPE_UPDATE,
    REVIEW_STATUS_WAITING_REVIEW,
)
from workflow_dataset.in_flow.store import save_draft, save_handoff, save_checkpoint
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


def _gather_plan_context(repo_root: Path) -> tuple[str, list[str], str]:
    """Return goal_text, step_labels, plan_id."""
    goal = ""
    steps: list[str] = []
    plan_id = ""
    try:
        from workflow_dataset.planner.store import load_current_goal, load_latest_plan
        goal = load_current_goal(repo_root=repo_root) or ""
        plan = load_latest_plan(repo_root=repo_root)
        if plan:
            plan_id = getattr(plan, "plan_id", "")
            for s in getattr(plan, "steps", [])[:20]:
                steps.append(getattr(s, "label", "") or "")
    except Exception:
        pass
    return goal, steps, plan_id


def _gather_session_handoff(repo_root: Path, session_id: str) -> tuple[str, list[str]]:
    """Return summary, next_steps for session."""
    try:
        from workflow_dataset.session.artifacts import get_handoff
        h = get_handoff(session_id, repo_root=repo_root)
        return h.get("summary", ""), list(h.get("next_steps", []))
    except Exception:
        return "", []


def create_draft(
    draft_type: str,
    repo_root: Path | str | None = None,
    *,
    project_id: str = "",
    session_id: str = "",
    step_index: int = -1,
    plan_id: str = "",
    plan_ref: str = "",
    step_label: str = "",
    run_id: str = "",
    episode_ref: str = "",
    title: str = "",
    extra_context: dict[str, Any] | None = None,
) -> DraftArtifact:
    """
    Create a draft artifact at a workflow moment. Content is template + context;
    no hidden LLM. Tied to project/session/step/episode.
    """
    root = _repo_root(repo_root)
    now = utc_now_iso()
    goal, step_labels, latest_plan_id = _gather_plan_context(root)
    plan_id = plan_id or latest_plan_id
    if not step_label and 0 <= step_index < len(step_labels):
        step_label = step_labels[step_index]

    draft_id = stable_id("draft", draft_type, project_id or "default", session_id or "", now[:10], prefix="draft_")
    affected = AffectedWorkflowStep(
        step_index=step_index,
        plan_id=plan_id,
        plan_ref=plan_ref or plan_id,
        step_label=step_label,
        run_id=run_id,
        episode_id=episode_ref,
    )

    # Template content by type
    content = ""
    if draft_type == DRAFT_TYPE_STATUS_SUMMARY:
        title = title or "Status summary"
        content = f"# {title}\n\n**Goal:** {goal[:200]}\n\n**Steps:**\n"
        for i, lbl in enumerate(step_labels[:15], 1):
            content += f"- {i}. {lbl}\n"
        content += "\n**Context:** In-flow draft; revise and promote as needed.\n"
    elif draft_type == DRAFT_TYPE_REVIEW_CHECKLIST:
        title = title or "Review checklist"
        content = f"# {title}\n\n- [ ] Confirm step: {step_label or 'current step'}\n- [ ] Verify outputs\n- [ ] Note blockers\n- [ ] Next action\n"
    elif draft_type == DRAFT_TYPE_NEXT_STEP_HANDOFF_BRIEF:
        title = title or "Next-step handoff brief"
        summary, next_steps = _gather_session_handoff(root, session_id) if session_id else ("", [])
        content = f"# {title}\n\n**Summary:** {summary[:300] or '(add summary)'}\n\n**Next steps:**\n"
        for s in next_steps[:10] or ["(add next steps)"]:
            content += f"- {s}\n"
    elif draft_type == DRAFT_TYPE_BLOCKED_ESCALATION_NOTE:
        title = title or "Blocked item escalation note"
        content = f"# {title}\n\n**Step:** {step_label or 'N/A'}\n**Run:** {run_id or 'N/A'}\n\n**Block reason:** (describe)\n**Requested action:** (escalate / unblock / defer)\n"
    elif draft_type == DRAFT_TYPE_MEETING_FOLLOW_UP:
        title = title or "Meeting follow-up note"
        content = "# Meeting follow-up\n\n## Attendees\n## Decisions\n## Action items\n## Next meeting\n"
    elif draft_type == DRAFT_TYPE_APPROVAL_REQUEST_SUMMARY:
        title = title or "Approval request summary"
        content = f"# {title}\n\n**Context:** {goal[:150]}\n\n**Requested approval:** (describe)\n**Risk level:** (low/medium/high)\n"
    else:
        title = title or f"Draft ({draft_type})"
        content = f"# {title}\n\n(Add content. Tied to step: {step_label or 'N/A'}, plan: {plan_id or 'N/A'})\n"

    if extra_context:
        content += "\n\n---\n*Context:* " + str(extra_context)[:500]

    draft = DraftArtifact(
        draft_id=draft_id,
        draft_type=draft_type,
        title=title,
        content=content,
        project_id=project_id or "default",
        session_id=session_id,
        affected_step=affected,
        episode_ref=episode_ref,
        review_status=REVIEW_STATUS_WAITING_REVIEW,
        created_utc=now,
        updated_utc=now,
    )
    save_draft(draft, repo_root=repo_root)
    return draft


def create_handoff(
    repo_root: Path | str | None = None,
    *,
    from_workflow: str = "latest",
    from_session_id: str = "",
    from_project_id: str = "",
    title: str = "",
    draft_ids: list[str] | None = None,
    target: str = "artifact",
) -> HandoffPackage:
    """
    Create a handoff package from current workflow/session. from_workflow can be
    run_id, episode_id, or "latest" (resolve from planner/executor/session).
    """
    root = _repo_root(repo_root)
    now = utc_now_iso()
    handoff_id = stable_id("handoff", from_workflow, from_session_id or "", now[:10], prefix="handoff_")

    goal, step_labels, plan_id = _gather_plan_context(root)
    summary = f"Goal: {goal[:200]}" if goal else "No current goal."
    next_steps = step_labels[:5] if step_labels else ["Set next steps in session handoff."]
    if from_session_id:
        s, n = _gather_session_handoff(root, from_session_id)
        if s:
            summary = s[:400]
        if n:
            next_steps = n[:10]

    # Resolve "latest" run if needed
    if from_workflow == "latest":
        try:
            from workflow_dataset.executor.hub import list_runs
            runs = list_runs(limit=1, repo_root=root)
            if runs:
                from_workflow = runs[0].get("run_id", "latest")
        except Exception:
            pass

    pkg = HandoffPackage(
        handoff_id=handoff_id,
        from_workflow=from_workflow,
        from_session_id=from_session_id,
        from_project_id=from_project_id or "default",
        title=title or f"Handoff from {from_workflow}",
        summary=summary,
        next_steps=next_steps,
        draft_ids=list(draft_ids or []),
        target=target,
        target_ref="",
        created_utc=now,
    )
    save_handoff(pkg, repo_root=repo_root)
    return pkg


def stage_summary(
    content: str,
    repo_root: Path | str | None = None,
    project_id: str = "",
    session_id: str = "",
    step_ref: str = "",
    episode_ref: str = "",
) -> StagedSummary:
    """Stage a summary; returns StagedSummary (caller may persist to draft or handoff)."""
    now = utc_now_iso()
    summary_id = stable_id("summary", content[:50], now, prefix="staged_")
    return StagedSummary(
        summary_id=summary_id,
        content=content,
        project_id=project_id,
        session_id=session_id,
        step_ref=step_ref,
        episode_ref=episode_ref,
        created_utc=now,
    )


def stage_checklist(
    title: str,
    items: list[str],
    repo_root: Path | str | None = None,
    project_id: str = "",
    session_id: str = "",
    step_ref: str = "",
) -> StagedChecklist:
    """Stage a checklist."""
    now = utc_now_iso()
    checklist_id = stable_id("checklist", title[:30], now, prefix="staged_")
    return StagedChecklist(
        checklist_id=checklist_id,
        title=title,
        items=list(items),
        done=[False] * len(items),
        project_id=project_id,
        session_id=session_id,
        step_ref=step_ref,
        created_utc=now,
    )


def stage_decision_request(
    question: str,
    options: list[str],
    context: str = "",
    repo_root: Path | str | None = None,
    project_id: str = "",
    step_ref: str = "",
) -> StagedDecisionRequest:
    """Stage a decision request."""
    now = utc_now_iso()
    decision_id = stable_id("decision", question[:40], now, prefix="staged_")
    return StagedDecisionRequest(
        decision_id=decision_id,
        question=question,
        options=list(options),
        context=context,
        project_id=project_id,
        step_ref=step_ref,
        created_utc=now,
    )


def link_checkpoint_to_step(
    plan_id: str,
    step_index: int,
    label: str = "",
    draft_id: str = "",
    episode_ref: str = "",
    repo_root: Path | str | None = None,
) -> ReviewCheckpoint:
    """Create a review checkpoint linked to a plan step."""
    root = _repo_root(repo_root)
    now = utc_now_iso()
    checkpoint_id = stable_id("checkpoint", plan_id, str(step_index), now[:10], prefix="cp_")
    cp = ReviewCheckpoint(
        checkpoint_id=checkpoint_id,
        label=label or f"Step {step_index} review",
        step_index=step_index,
        plan_id=plan_id,
        episode_ref=episode_ref,
        draft_id=draft_id,
        status="pending",
        created_utc=now,
    )
    save_checkpoint(cp, repo_root=repo_root)
    return cp
