"""
M28E–M28H: Delegated subplan generation from goals, planner, skills, pack, context.
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
        return prefix + hashlib.sha256("".join(parts).encode()).hexdigest()[:16]

from workflow_dataset.lanes.models import (
    LaneScope,
    DelegatedSubplan,
    DelegatedSubplanStep,
    TRUST_MODE_SIMULATE,
)
from workflow_dataset.planner.schema import Plan, PlanStep


def create_delegated_subplan(
    project_id: str = "",
    goal_id: str = "",
    goal_text: str = "",
    scope_id: str = "default",
    scope_label: str = "",
    scope_description: str = "",
    allowed_step_classes: list[str] | None = None,
    plan: Plan | None = None,
    step_indices: list[int] | None = None,
    trust_mode: str = TRUST_MODE_SIMULATE,
    approval_mode: str = "checkpoint_before_real",
    stop_conditions: list[str] | None = None,
    max_steps: int = 10,
    bundle_id: str = "",
    repo_root: Path | str | None = None,
) -> DelegatedSubplan:
    """
    Create a bounded delegated subplan from active goal/planner output.
    If bundle_id is set, scope and default_stop_conditions are taken from the bundle.
    """
    scope: LaneScope
    if bundle_id:
        try:
            from workflow_dataset.lanes.bundles import load_bundle
            bundle = load_bundle(bundle_id, repo_root)
            if bundle:
                scope = bundle.scope
                if not stop_conditions:
                    stop_conditions = list(bundle.default_stop_conditions)
            else:
                scope = LaneScope(scope_id=scope_id, label=scope_label or scope_id, description=scope_description, allowed_step_classes=allowed_step_classes or [])
        except Exception:
            scope = LaneScope(scope_id=scope_id, label=scope_label or scope_id, description=scope_description, allowed_step_classes=allowed_step_classes or [])
    else:
        scope = LaneScope(
            scope_id=scope_id,
            label=scope_label or scope_id,
            description=scope_description,
            allowed_step_classes=allowed_step_classes or [],
        )
    subplan_id = stable_id("subplan", project_id, goal_id, scope_id, utc_now_iso(), prefix="")[:24]
    steps: list[DelegatedSubplanStep] = []
    expected_outputs: list[str] = []

    if plan and plan.steps:
        indices = step_indices if step_indices is not None else list(range(min(len(plan.steps), max_steps)))
        for i in indices:
            if i >= len(plan.steps):
                continue
            s = plan.steps[i]
            steps.append(DelegatedSubplanStep(
                step_index=s.step_index,
                label=s.label,
                step_class=s.step_class,
                trust_level=s.trust_level,
                approval_required=s.approval_required,
                expected_outputs=list(s.expected_outputs),
            ))
            expected_outputs.extend(s.expected_outputs)
        expected_artifacts = list({a.label for a in plan.expected_artifacts if a.step_index in indices})
        expected_outputs = list(dict.fromkeys(expected_outputs + expected_artifacts))
    else:
        # Minimal subplan from goal text
        steps.append(DelegatedSubplanStep(
            step_index=0,
            label=goal_text[:80] if goal_text else "delegated_step",
            step_class="reasoning_only",
            expected_outputs=["summary"],
        ))
        expected_outputs = ["summary"]

    conditions = list(stop_conditions) if stop_conditions else []
    if f"max_steps:{max_steps}" not in [c for c in conditions if c.startswith("max_steps:")]:
        conditions.append(f"max_steps:{max_steps}")
    if "on_blocked" not in conditions:
        conditions.append("on_blocked")

    return DelegatedSubplan(
        subplan_id=subplan_id,
        scope=scope,
        steps=steps,
        expected_outputs=expected_outputs,
        trust_mode=trust_mode,
        approval_mode=approval_mode,
        stop_conditions=conditions,
        parent_plan_id=plan.plan_id if plan else "",
        parent_goal_id=goal_id,
        created_at=utc_now_iso(),
    )


def gather_subplan_context(
    project_id: str = "",
    goal_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Gather context for subplan generation: current project, goal, latest plan, accepted skills (stub)."""
    root = Path(repo_root).resolve() if repo_root else None
    ctx: dict[str, Any] = {
        "project_id": project_id,
        "goal_id": goal_id,
        "plan": None,
        "goal_text": "",
        "accepted_skills": [],
        "pack_defaults": {},
    }
    try:
        from workflow_dataset.planner.store import load_latest_plan
        ctx["plan"] = load_latest_plan(root)
        if ctx["plan"]:
            ctx["goal_text"] = ctx["plan"].goal_text or ""
    except Exception:
        pass
    try:
        from workflow_dataset.project_case.store import get_project_goals, load_project
        if project_id:
            proj = load_project(project_id, root)
            if proj:
                goals = get_project_goals(project_id, root)
                for g in goals:
                    if g.goal_id == goal_id:
                        ctx["goal_text"] = ctx["goal_text"] or g.title or g.description
                        break
    except Exception:
        pass
    return ctx
