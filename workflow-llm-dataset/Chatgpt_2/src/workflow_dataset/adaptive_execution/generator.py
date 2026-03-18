"""
M45B: Multi-step loop generation from goals, routines, operator responsibilities, memory prior cases, runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.adaptive_execution.models import (
    AdaptiveExecutionPlan,
    BoundedExecutionLoop,
    ExecutionStep,
    PlanBranch,
    AdaptationTrigger,
    StopCondition,
    EscalationCondition,
    HumanTakeoverPoint,
)
from workflow_dataset.adaptive_execution.profiles import get_profile
from workflow_dataset.adaptive_execution.templates import get_template

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def generate_plan_from_goal(
    goal_text: str,
    max_steps: int = 20,
    repo_root: Path | str | None = None,
    project_id: str = "",
    session_id: str = "",
) -> AdaptiveExecutionPlan:
    """
    Generate an adaptive execution plan from a goal. Uses planner if available; otherwise minimal plan.
    """
    root = _repo_root(repo_root)
    plan_id = stable_id("aplan", goal_text or "", utc_now_iso(), prefix="aplan_")[:24]
    steps: list[ExecutionStep] = []
    sources_used: list[str] = []

    try:
        from workflow_dataset.planner import compile_goal_to_plan
        from workflow_dataset.planner.schema import Plan
        plan = compile_goal_to_plan(goal_text, repo_root=root, mode="simulate")
        if plan and plan.steps:
            for ps in plan.steps:
                steps.append(ExecutionStep(
                    step_index=len(steps),
                    step_id=stable_id("step", plan_id, str(ps.step_index), prefix="step_"),
                    label=ps.label,
                    action_type="job_run" if ps.provenance and ps.provenance.kind == "job" else "macro_step",
                    action_ref=ps.provenance.ref if ps.provenance else "",
                    trust_level=ps.trust_level,
                    approval_required=ps.approval_required,
                    checkpoint_before=ps.checkpoint_before,
                    allowed=ps.step_class != "blocked",
                    blocked_reason=ps.blocked_reason or "",
                ))
            sources_used.append("planner")
    except Exception:
        pass

    if not steps:
        steps.append(ExecutionStep(
            step_index=0,
            step_id=stable_id("step", plan_id, "0", prefix="step_"),
            label="Manual step (no plan compiled)",
            action_type="human_required",
            action_ref="",
            allowed=True,
        ))

    main_branch = PlanBranch(
        branch_id="main",
        label="Main",
        description="Primary path",
        step_indices=list(range(len(steps))),
        is_fallback=False,
        is_human_only=False,
    )
    fallback_branch = PlanBranch(
        branch_id="fallback",
        label="Fallback",
        description="Safer path on block or low confidence",
        step_indices=[i for i in range(len(steps)) if i < len(steps)],
        is_fallback=True,
        is_human_only=True,
    )

    plan = AdaptiveExecutionPlan(
        plan_id=plan_id,
        goal_text=goal_text or "",
        steps=steps,
        branches=[main_branch, fallback_branch],
        default_branch_id="main",
        fallback_branch_id="fallback",
        adaptation_triggers=[
            AdaptationTrigger(
                trigger_id="on_blocked",
                kind="outcome_status",
                outcome_status="blocked",
                branch_to_id="fallback",
                reason="Switch to fallback when step is blocked.",
            ),
            AdaptationTrigger(
                trigger_id="on_confidence_low",
                kind="confidence_below",
                confidence_threshold=0.5,
                branch_to_id="fallback",
                reason="Switch to fallback when confidence drops below 0.5.",
            ),
        ],
        stop_conditions=[
            StopCondition(condition_id="max_steps", kind="max_steps_reached", description="Max steps reached."),
            StopCondition(condition_id="manual", kind="manual_stop", description="Operator stopped the loop."),
            StopCondition(condition_id="blocked", kind="blocked_step", description="Step blocked and fallback not desired."),
        ],
        escalation_conditions=[
            EscalationCondition(condition_id="blocked_esc", kind="blocked", description="Step blocked; human decision required.", handoff_reason="blocked"),
            EscalationCondition(condition_id="approval", kind="approval_required", description="Approval required before next step.", handoff_reason="approval_required"),
        ],
        human_takeover_points=[
            HumanTakeoverPoint(step_index=i, label=s.label, gate_kind="approval" if s.approval_required else "review", required_approval="checkpoint", reason="Plan checkpoint")
            for i, s in enumerate(steps) if s.approval_required or s.checkpoint_before
        ],
        allowed_action_refs=[s.action_ref for s in steps if s.action_ref and s.allowed],
        forbidden_action_refs=[],
        sources_used=sources_used,
        created_at=utc_now_iso(),
    )
    return plan


def create_bounded_loop(
    plan: AdaptiveExecutionPlan,
    max_steps: int | None = None,
    required_review_step_indices: list[int] | None = None,
    repo_root: Path | str | None = None,
    profile_id: str = "",
    template_id: str = "",
) -> BoundedExecutionLoop:
    """
    Create a bounded execution loop from a plan. Optionally apply profile (max_steps, reviews) and set template_id for explanation.
    """
    root = _repo_root(repo_root)
    loop_id = stable_id("loop", plan.plan_id, utc_now_iso(), prefix="loop_")[:20]
    now = utc_now_iso()

    profile = get_profile(profile_id) if profile_id else None
    template = get_template(template_id) if template_id else None

    review_indices = required_review_step_indices if required_review_step_indices is not None else []
    if not review_indices and plan.human_takeover_points:
        review_indices = sorted(set(h.step_index for h in plan.human_takeover_points))

    if profile and profile.review_every_n_steps > 0:
        review_indices = list(range(0, max(len(plan.steps), 1), max(1, profile.review_every_n_steps)))
    if profile and profile.require_review_before_first_step and 0 not in review_indices:
        review_indices = [0] + [i for i in review_indices if i != 0]
        review_indices.sort()

    cap = max_steps if max_steps is not None else max(len(plan.steps), 20)
    if profile and profile.max_steps_cap > 0:
        cap = min(cap, profile.max_steps_cap)
    if template and template.max_steps_default > 0 and max_steps is None:
        cap = min(cap, template.max_steps_default)

    next_takeover: int | None = None
    for i in review_indices:
        if i >= 0:
            next_takeover = i
            break

    loop = BoundedExecutionLoop(
        loop_id=loop_id,
        plan_id=plan.plan_id,
        plan=plan,
        status="running",
        current_step_index=0,
        current_branch_id=plan.default_branch_id,
        max_steps=cap,
        steps_executed=0,
        required_review_step_indices=review_indices,
        outcomes=[],
        stop_reason="",
        escalation_reason="",
        next_takeover_step_index=next_takeover,
        fallback_activated=False,
        created_at=now,
        updated_at=now,
        profile_id=profile_id or (template.default_profile_id if template else ""),
        template_id=template_id,
    )
    return loop


def generate_loop_from_goal(
    goal_text: str,
    max_steps: int = 20,
    repo_root: Path | str | None = None,
    project_id: str = "",
    session_id: str = "",
    profile_id: str = "",
    template_id: str = "",
) -> BoundedExecutionLoop:
    """Generate plan from goal and create a bounded loop. Optionally use profile_id and template_id (M45D.1)."""
    root = _repo_root(repo_root)
    template = get_template(template_id) if template_id else None
    effective_goal = (template.goal_hint or goal_text) if template and not goal_text else goal_text
    plan = generate_plan_from_goal(effective_goal, max_steps=max_steps, repo_root=root, project_id=project_id, session_id=session_id)

    try:
        from workflow_dataset.memory_intelligence.planner_enrichment import enrich_planning_sources
        from workflow_dataset.planner.sources import gather_planning_sources
        sources = gather_planning_sources(root, project_id=project_id, session_id=session_id)
        enriched = enrich_planning_sources(sources, project_id=project_id, session_id=session_id, repo_root=root, limit=3)
        if enriched.get("memory_prior_cases"):
            plan.sources_used = list(plan.sources_used) + ["memory_prior_cases"]
    except Exception:
        pass

    effective_profile = profile_id or (template.default_profile_id if template else "")
    default_max = template.max_steps_default if template and template.max_steps_default > 0 else max_steps
    return create_bounded_loop(
        plan,
        max_steps=default_max if template else max_steps,
        repo_root=root,
        profile_id=effective_profile,
        template_id=template_id,
    )
