"""
Workflow plan / step generation for real-time assist (M33F).

Uses active context, optional goal/routine, planner output to produce supervised
live workflow path: current step, next step, alternate path, escalation path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.live_workflow.models import (
    SupervisedLiveWorkflow,
    LiveStepSuggestion,
    EscalationTier,
    WorkflowRunState,
    BlockedRealTimeStep,
    ExpectedHandoff,
    AlternatePathRecommendation,
)
from workflow_dataset.live_workflow.bundles import get_bundle
from workflow_dataset.planner.compile import compile_goal_to_plan
from workflow_dataset.planner.schema import Plan, PlanStep
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _plan_step_to_live_suggestion(ps: PlanStep, plan_ref: str, plan_source: str) -> LiveStepSuggestion:
    """Convert planner PlanStep to LiveStepSuggestion."""
    handoff = None
    if ps.expected_outputs:
        handoff = ExpectedHandoff(
            label=ps.expected_outputs[0] if ps.expected_outputs else "",
            path_or_type=ps.expected_outputs[0] if ps.expected_outputs else "",
            step_index=ps.step_index,
            handoff_target="executor_run" if plan_ref else "compile_plan",
        )
    prov_label = (ps.provenance.label or ps.provenance.ref or "") if ps.provenance else ""
    return LiveStepSuggestion(
        step_index=ps.step_index,
        label=ps.label,
        description=ps.step_class or "",
        step_class=ps.step_class,
        approval_required=ps.approval_required,
        checkpoint_before=ps.checkpoint_before,
        expected_handoff=handoff,
        escalation_tier=EscalationTier.HINT_ONLY,
        hint_text=ps.label,
        plan_ref=plan_ref,
        provenance=prov_label,
    )


def generate_live_workflow_steps(
    goal_text: str = "",
    routine_id: str = "",
    plan_ref: str = "",
    bundle_id: str = "",
    project_hint: str = "",
    session_hint: str = "",
    repo_root: Path | str | None = None,
    mode: str = "simulate",
) -> SupervisedLiveWorkflow:
    """
    Generate a supervised live workflow from goal or routine. Uses planner when possible.
    Returns SupervisedLiveWorkflow with steps, current/next step, escalation path.
    """
    root = Path(repo_root).resolve() if repo_root else None
    # Resolve goal: explicit goal_text, routine_id, plan_ref, or from bundle
    bundle = get_bundle(bundle_id, root) if bundle_id else None
    goal = (goal_text or "").strip()
    if not goal and bundle:
        goal = (bundle.goal_template or bundle.routine_id or bundle.plan_ref or "").strip()
    if not goal and routine_id:
        goal = routine_id
    if not goal and plan_ref:
        goal = plan_ref
    if not goal and bundle:
        goal = bundle.routine_id or bundle.plan_ref or ""

    now = utc_now_iso()
    run_id = stable_id("lwr", now, goal or bundle_id or routine_id or plan_ref, prefix="lwr")[:20]

    if not goal:
        return SupervisedLiveWorkflow(
            run_id=run_id,
            goal_text="",
            plan_id="",
            plan_ref="",
            plan_source="",
            steps=[],
            current_step_index=0,
            next_step_index=None,
            alternate_path_summary="",
            escalation_path_summary="Add a goal or routine to get steps (e.g. live-workflow now --goal 'Weekly report').",
            state=WorkflowRunState.NO_WORKFLOW,
            project_hint=project_hint,
            session_hint=session_hint,
            created_utc=now,
            updated_utc=now,
            bundle_id=bundle_id,
        )

    try:
        plan = compile_goal_to_plan(goal, repo_root=root, mode=mode)
    except Exception:
        return SupervisedLiveWorkflow(
            run_id=run_id,
            goal_text=goal,
            plan_id="",
            plan_ref=plan_ref or goal,
            plan_source="goal",
            steps=[],
            current_step_index=0,
            next_step_index=None,
            alternate_path_summary="",
            escalation_path_summary="Plan compilation failed; try refining the goal or check session/routines.",
            state=WorkflowRunState.NO_WORKFLOW,
            project_hint=project_hint,
            session_hint=session_hint,
            created_utc=now,
            updated_utc=now,
        )

    steps: list[LiveStepSuggestion] = []
    plan_ref_resolved = (plan.sources_used[0].split(":", 1)[1] if plan.sources_used else "") or plan.plan_id
    plan_source_resolved = (plan.sources_used[0].split(":", 1)[0] if plan.sources_used else "goal") or "goal"

    for ps in plan.steps:
        steps.append(_plan_step_to_live_suggestion(ps, plan_ref_resolved, plan_source_resolved))

    # Blocked: first blocked step if any
    blocked_step: BlockedRealTimeStep | None = None
    if plan.blocked_conditions:
        bc = plan.blocked_conditions[0]
        idx = bc.step_index if bc.step_index is not None else 0
        label = next((s.label for s in plan.steps if s.step_index == idx), "")
        blocked_step = BlockedRealTimeStep(
            step_index=idx,
            label=label,
            blocked_reason=bc.reason,
            approval_scope=bc.approval_scope,
            handoff_suggestion="Open planner or approval studio to resolve.",
            plan_ref=plan_ref_resolved,
            run_id=run_id,
        )

    # Checkpoint: first checkpoint before which we need approval
    checkpoint_before: int | None = None
    for c in plan.checkpoints:
        checkpoint_before = c.step_index
        break

    next_idx = 1 if len(steps) > 1 else None
    if blocked_step and blocked_step.step_index == 0:
        next_idx = 0

    state = WorkflowRunState.BLOCKED if blocked_step else WorkflowRunState.ACTIVE
    escalation_path_summary = "hint → action card → planner prefill → simulated run → review" if steps else ""

    # Stronger alternate-path recommendations from bundle or heuristics
    alternate_path_recommendations: list[dict[str, Any]] = []
    if bundle:
        for i, alt_goal in enumerate(bundle.alternate_goals[:5]):
            alternate_path_recommendations.append({
                "label": alt_goal[:60],
                "goal_or_ref": alt_goal,
                "reason": "Alternate goal from workflow bundle.",
                "priority": 10 - i,
            })
    if not alternate_path_recommendations:
        alternate_path_recommendations.append({
            "label": "Refine goal or try a different routine",
            "goal_or_ref": "",
            "reason": "Use planner compile with a different goal for an alternate path.",
            "priority": 5,
        })

    alternate_path_summary = "Use planner compile with different goal for alternate path."
    if bundle and bundle.alternate_goals:
        alternate_path_summary = f"Alternate goals from bundle: {', '.join(bundle.alternate_goals[:3])}."

    return SupervisedLiveWorkflow(
        run_id=run_id,
        goal_text=plan.goal_text,
        plan_id=plan.plan_id,
        plan_ref=plan_ref_resolved,
        plan_source=plan_source_resolved,
        steps=steps,
        current_step_index=0,
        next_step_index=next_idx,
        alternate_path_summary=alternate_path_summary,
        escalation_path_summary=escalation_path_summary,
        current_escalation_tier=EscalationTier.HINT_ONLY,
        checkpoint_required_before=checkpoint_before,
        blocked_step=blocked_step,
        state=state,
        project_hint=project_hint,
        session_hint=session_hint,
        created_utc=now,
        updated_utc=now,
        bundle_id=bundle_id,
        alternate_path_recommendations=alternate_path_recommendations,
    )
