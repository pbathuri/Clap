"""
M27E–M27H: Propose next actions from goal, session, plan, skills, packs, trust.
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

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]

from workflow_dataset.supervised_loop.models import QueuedAction, BlockedCycleReason
from workflow_dataset.planner.store import load_current_goal, load_latest_plan
from workflow_dataset.executor.hub import list_runs, load_run


def propose_next_actions(
    project_slug: str = "",
    repo_root: Path | str | None = None,
) -> tuple[list[QueuedAction], BlockedCycleReason | None]:
    """
    Propose a small set of next actions using:
    - planner current goal and latest plan
    - session (from gather_planning_sources / current session)
    - executor runs (if one is awaiting_approval, propose resume)
    Returns (list of proposed actions, None) or ([], BlockedCycleReason) if blocked.
    """
    root = Path(repo_root).resolve() if repo_root else None
    goal = load_current_goal(root)
    plan = load_latest_plan(root)
    proposed: list[QueuedAction] = []

    # 1) If executor has a run awaiting_approval, propose resume first
    try:
        runs = list_runs(limit=5, repo_root=root)
        for r in runs:
            if r.get("status") == "awaiting_approval":
                run_id = r.get("run_id", "")
                run = load_run(run_id, root) if run_id else None
                if run:
                    proposed.append(QueuedAction(
                        action_id=stable_id("act", "resume", run_id, utc_now_iso(), prefix="a_"),
                        label=f"Resume executor run {run_id} (approve next step)",
                        action_type="executor_resume",
                        plan_ref=run.plan_ref,
                        plan_source=run.plan_source,
                        mode=run.mode,
                        why="Run is paused at checkpoint; operator approval required to continue.",
                        risk_level="medium",
                        trust_mode=run.mode,
                        created_at=utc_now_iso(),
                    ))
                    return (proposed, None)
    except Exception:
        pass

    # 2) No plan or empty plan -> propose compile
    if not plan or not plan.steps:
        proposed.append(QueuedAction(
            action_id=stable_id("act", "compile", goal or project_slug, utc_now_iso(), prefix="a_"),
            label="Compile plan for current goal" + (f": {goal[:50]}..." if goal and len(goal) > 50 else (f": {goal}" if goal else "")),
            action_type="planner_compile",
            plan_ref="",
            plan_source="",
            mode="simulate",
            why="No plan or empty plan; compile goal to get executable steps.",
            risk_level="low",
            trust_mode="simulate",
            created_at=utc_now_iso(),
        ))
        return (proposed, None)

    # 3) Plan has steps: propose first executable step (job or routine)
    # Plan steps have provenance: kind=job ref=job_id, or kind=macro ref=routine_id
    routine_id: str = ""
    for s in plan.sources_used or []:
        if s.startswith("routine:"):
            routine_id = s.replace("routine:", "").strip()
            break
    first_job_id = ""
    for step in plan.steps:
        if step.blocked_reason:
            continue
        if step.step_class in ("human_required", "blocked", "reasoning_only"):
            continue
        prov = step.provenance
        if prov and prov.kind == "job" and prov.ref:
            first_job_id = prov.ref
            break
        if prov and prov.kind == "macro" and prov.ref:
            routine_id = prov.ref
            break
    if routine_id and not first_job_id:
        # Whole routine as one unit for executor
        proposed.append(QueuedAction(
            action_id=stable_id("act", "run", routine_id, utc_now_iso(), prefix="a_"),
            label=f"Run routine: {routine_id}",
            action_type="executor_run",
            plan_ref=routine_id,
            plan_source="routine",
            mode="simulate",
            step_index=0,
            why=f"Next step from plan: routine {routine_id} (goal: {plan.goal_text[:40]}...)" if plan.goal_text else f"Next: routine {routine_id}",
            risk_level="medium",
            trust_mode="simulate",
            created_at=utc_now_iso(),
        ))
        return (proposed, None)
    if first_job_id:
        proposed.append(QueuedAction(
            action_id=stable_id("act", "run", first_job_id, utc_now_iso(), prefix="a_"),
            label=f"Run job: {first_job_id}",
            action_type="executor_run",
            plan_ref=first_job_id,
            plan_source="job",
            mode="simulate",
            step_index=0,
            why=f"Next step from plan: job {first_job_id}" + (f" (goal: {plan.goal_text[:40]}...)" if plan.goal_text else ""),
            risk_level="medium",
            trust_mode="simulate",
            created_at=utc_now_iso(),
        ))
        return (proposed, None)

    # 4) All steps blocked or no executable step
    blocked_reason = "Plan has no executable step (all blocked or human_required)."
    if plan.blocked_conditions:
        blocked_reason = plan.blocked_conditions[0].reason
    return ([], BlockedCycleReason(reason=blocked_reason, detail="", step_index=0))
