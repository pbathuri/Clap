"""
M32E–M32H: Generate just-in-time assist suggestions from live context.

Sources: progress board, goal/plan, inbox/digest, routines, skills, packs, preferences.
Types: next_step, draft_summary, blocked_review, resume_routine, open_artifact, use_preference, remind.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.assist_engine.models import (
    AssistSuggestion,
    TriggeringContext,
    SuggestionReason,
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


def generate_assist_suggestions(
    repo_root: Path | str | None = None,
    max_total: int = 20,
) -> list[AssistSuggestion]:
    """
    Generate suggestions from live context. No LLM; deterministic and grounded.
    Suppression of repeats is applied by caller (queue layer) using store.list_dismissed_patterns.
    """
    root = _repo_root(repo_root)
    now = utc_now_iso()
    out: list[AssistSuggestion] = []

    # --- Progress board: stalled, blocked, next intervention ---
    try:
        from workflow_dataset.progress.board import build_progress_board
        board = build_progress_board(repo_root=root)
    except Exception:
        board = {}

    # --- Goal and plan ---
    goal = ""
    plan = None
    try:
        from workflow_dataset.planner.store import load_current_goal, load_latest_plan
        goal = load_current_goal(repo_root=root) or ""
        plan = load_latest_plan(repo_root=root)
    except Exception:
        pass

    # --- Daily digest: top next, blocked, inbox ---
    digest = None
    try:
        from workflow_dataset.daily.inbox import build_daily_digest
        digest = build_daily_digest(repo_root=root)
    except Exception:
        pass

    # --- Routines (for resume_routine) ---
    routines: list[Any] = []
    try:
        from workflow_dataset.copilot.routines import list_routines
        routine_ids = list(list_routines(root))[:15]
        routines = [{"id": rid} for rid in routine_ids]
    except Exception:
        pass

    # --- Next step from plan or digest ---
    if plan and getattr(plan, "steps", None):
        steps = plan.steps
        unblocked = [s for s in steps if not getattr(s, "blocked_reason", None)]
        if unblocked:
            first = unblocked[0]
            step_label = getattr(first, "label", "") or getattr(first, "description", "") or "Next step"
            sug_id = stable_id("assist", "next_step", goal[:50], step_label[:50], prefix="sug_")
            out.append(AssistSuggestion(
                suggestion_id=sug_id,
                suggestion_type="next_step",
                title="Next step from plan",
                description=step_label[:200] or "Continue with current plan.",
                reason=SuggestionReason(
                    title="Plan has next step",
                    description="Current plan has an unblocked step.",
                    evidence=[f"Goal: {goal[:80]}", f"Step: {step_label[:80]}"],
                ),
                triggering_context=TriggeringContext(
                    source="goal_plan",
                    summary="Current goal and latest plan",
                    signals=["plan_steps", "goal_set"],
                    project_id=board.get("active_projects", ["default"])[0] if board.get("active_projects") else "default",
                ),
                confidence=0.85,
                usefulness_score=0.8,
                interruptiveness_score=0.2,
                affected_project_id=board.get("active_projects", ["default"])[0] if board.get("active_projects") else "default",
                required_operator_action="Run or preview the next step.",
                status="pending",
                created_utc=now,
                updated_utc=now,
                supporting_signals=["planner", "plan_steps"],
            ))
    if digest and getattr(digest, "top_next_recommended", None):
        top = digest.top_next_recommended
        if isinstance(top, dict) and top.get("label"):
            sug_id = stable_id("assist", "next_step", "digest", top.get("label", "")[:50], prefix="sug_")
            if not any(s.suggestion_id == sug_id for s in out):
                out.append(AssistSuggestion(
                    suggestion_id=sug_id,
                    suggestion_type="next_step",
                    title="Recommended next action",
                    description=(top.get("label") or "")[:200],
                    reason=SuggestionReason(
                        title="Daily digest recommendation",
                        description=top.get("reason", "Inbox suggests this next."),
                        evidence=[top.get("reason", "")],
                    ),
                    triggering_context=TriggeringContext(
                        source="inbox",
                        summary="Daily digest top next",
                        signals=["digest", "top_next"],
                    ),
                    confidence=0.75,
                    usefulness_score=0.75,
                    interruptiveness_score=0.25,
                    required_operator_action=top.get("command", "Review and run."),
                    status="pending",
                    created_utc=now,
                    updated_utc=now,
                    supporting_signals=["daily_digest"],
                ))

    # --- Blocked review: suggest switching to blocked-review or approval mode ---
    blocked_items = []
    if digest and getattr(digest, "blocked_items", None):
        blocked_items = list(digest.blocked_items)[:5]
    if board.get("stalled_projects") or board.get("next_intervention_candidate") or blocked_items:
        sug_id = stable_id("assist", "blocked_review", now[:10], prefix="sug_")
        reasons = []
        if board.get("stalled_projects"):
            reasons.append("Stalled projects")
        if board.get("next_intervention_candidate"):
            reasons.append("Intervention candidate")
        if blocked_items:
            reasons.append(f"{len(blocked_items)} blocked item(s)")
        out.append(AssistSuggestion(
            suggestion_id=sug_id,
            suggestion_type="blocked_review",
            title="Review blocked or stalled work",
            description="There are blocked items or stalled projects. Consider switching to blocked-review or approval mode.",
            reason=SuggestionReason(
                title="Blocked/stalled signals",
                description="; ".join(reasons),
                evidence=reasons,
            ),
            triggering_context=TriggeringContext(
                source="progress_board",
                summary="Progress board and digest",
                signals=["stalled_projects", "blocked_items", "next_intervention"],
                project_id=board.get("next_intervention_candidate", ""),
            ),
            confidence=0.8,
            usefulness_score=0.85,
            interruptiveness_score=0.4,
            required_operator_action="Open review or approval flow.",
            status="pending",
            created_utc=now,
            updated_utc=now,
            supporting_signals=["progress_board", "digest"],
        ))

    # --- Draft/summary: suggest creating draft or checklist from plan ---
    if plan and getattr(plan, "steps", None) and len(plan.steps) >= 2:
        sug_id = stable_id("assist", "draft_summary", goal[:40], prefix="sug_")
        out.append(AssistSuggestion(
            suggestion_id=sug_id,
            suggestion_type="draft_summary",
            title="Propose draft or checklist from plan",
            description="Current plan has multiple steps. I can suggest a draft summary or checklist.",
            reason=SuggestionReason(
                title="Plan has multiple steps",
                description=f"Plan has {len(plan.steps)} steps; a summary or checklist may help.",
                evidence=[f"Steps: {len(plan.steps)}"],
            ),
            triggering_context=TriggeringContext(
                source="goal_plan",
                summary="Latest plan",
                signals=["plan_steps"],
            ),
            confidence=0.7,
            usefulness_score=0.6,
            interruptiveness_score=0.3,
            required_operator_action="Request draft or checklist via assist draft.",
            status="pending",
            created_utc=now,
            updated_utc=now,
            supporting_signals=["planner"],
        ))

    # --- Resume routine: if we have routines and no strong “in plan” signal ---
    if routines and not (plan and getattr(plan, "steps", None)):
        rid = routines[0].get("id", "default_routine")
        sug_id = stable_id("assist", "resume_routine", rid, prefix="sug_")
        out.append(AssistSuggestion(
            suggestion_id=sug_id,
            suggestion_type="resume_routine",
            title="Resume a routine",
            description=f"Routine '{rid}' is available. Consider resuming if you were in the middle of it.",
            reason=SuggestionReason(
                title="Routine available",
                description="No active plan steps; routines may help continue work.",
                evidence=[f"Routine: {rid}"],
            ),
            triggering_context=TriggeringContext(
                source="routines",
                summary="Copilot routines",
                signals=["list_routines"],
            ),
            confidence=0.6,
            usefulness_score=0.5,
            interruptiveness_score=0.35,
            required_operator_action=f"Run or simulate routine {rid}.",
            status="pending",
            created_utc=now,
            updated_utc=now,
            supporting_signals=["copilot_routines"],
        ))

    # --- Open artifact: from digest or focus (simplified: suggest opening review or workspace) ---
    if digest and getattr(digest, "inbox_items", None) and digest.inbox_items:
        first = digest.inbox_items[0]
        item_id = first.get("id", "")
        kind = first.get("kind", "item")
        sug_id = stable_id("assist", "open_artifact", kind, item_id[:30], prefix="sug_")
        out.append(AssistSuggestion(
            suggestion_id=sug_id,
            suggestion_type="open_artifact",
            title="Open relevant artifact or workflow",
            description=f"Top inbox item: {kind} '{item_id}'. Open or run it?",
            reason=SuggestionReason(
                title="Inbox has items",
                description="Daily digest has items; opening the top one may be relevant.",
                evidence=[f"{kind}: {item_id}"],
            ),
            triggering_context=TriggeringContext(
                source="inbox",
                summary="Daily digest inbox",
                signals=["inbox_items"],
            ),
            confidence=0.65,
            usefulness_score=0.55,
            interruptiveness_score=0.3,
            required_operator_action=f"Open or run {kind} {item_id}.",
            status="pending",
            created_utc=now,
            updated_utc=now,
            supporting_signals=["daily_digest"],
        ))

    # Cap total
    if len(out) > max_total:
        # Sort by usefulness then confidence, keep top
        out.sort(key=lambda s: (s.usefulness_score, s.confidence), reverse=True)
        out = out[:max_total]

    return out
