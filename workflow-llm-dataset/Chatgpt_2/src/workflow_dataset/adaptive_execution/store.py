"""
M45C: Persist active bounded loops; list by status.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.adaptive_execution.models import BoundedExecutionLoop, AdaptiveExecutionPlan, StepOutcome

DIR_NAME = "data/local/adaptive_execution"
LOOPS_FILE = "active_loops.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _loops_path(root: Path) -> Path:
    return root / DIR_NAME / LOOPS_FILE


def _load_loops(root: Path) -> list[dict[str, Any]]:
    p = _loops_path(root)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return list(data.get("loops", []))
    except Exception:
        return []


def _save_loops(root: Path, loops: list[dict[str, Any]]) -> Path:
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    p = d / LOOPS_FILE
    p.write_text(json.dumps({"loops": loops}, indent=2), encoding="utf-8")
    return p


def _plan_from_dict(d: dict[str, Any] | None) -> AdaptiveExecutionPlan | None:
    if not d:
        return None
    from workflow_dataset.adaptive_execution.models import (
        ExecutionStep,
        PlanBranch,
        AdaptationTrigger,
        StopCondition,
        EscalationCondition,
        HumanTakeoverPoint,
    )
    steps = [
        ExecutionStep(
            step_index=e.get("step_index", 0),
            step_id=e.get("step_id", ""),
            label=e.get("label", ""),
            action_type=e.get("action_type", ""),
            action_ref=e.get("action_ref", ""),
            trust_level=e.get("trust_level", ""),
            approval_required=bool(e.get("approval_required", False)),
            checkpoint_before=bool(e.get("checkpoint_before", False)),
            allowed=bool(e.get("allowed", True)),
            expected_artifact=e.get("expected_artifact", ""),
            blocked_reason=e.get("blocked_reason", ""),
        )
        for e in d.get("steps", [])
    ]
    branches = [
        PlanBranch(
            branch_id=b.get("branch_id", ""),
            label=b.get("label", ""),
            description=b.get("description", ""),
            step_indices=list(b.get("step_indices", [])),
            is_fallback=bool(b.get("is_fallback", False)),
            is_human_only=bool(b.get("is_human_only", False)),
        )
        for b in d.get("branches", [])
    ]
    def mk_trigger(t: dict) -> AdaptationTrigger:
        return AdaptationTrigger(
            trigger_id=t.get("trigger_id", ""),
            kind=t.get("kind", ""),
            outcome_status=t.get("outcome_status", ""),
            confidence_threshold=float(t.get("confidence_threshold", 0)),
            condition_ref=t.get("condition_ref", ""),
            branch_to_id=t.get("branch_to_id", ""),
            reason=t.get("reason", ""),
        )
    def mk_stop(c: dict) -> StopCondition:
        return StopCondition(
            condition_id=c.get("condition_id", ""),
            kind=c.get("kind", ""),
            description=c.get("description", ""),
            step_index=c.get("step_index"),
        )
    def mk_esc(c: dict) -> EscalationCondition:
        return EscalationCondition(
            condition_id=c.get("condition_id", ""),
            kind=c.get("kind", ""),
            description=c.get("description", ""),
            step_index=c.get("step_index"),
            handoff_reason=c.get("handoff_reason", ""),
        )
    def mk_takeover(h: dict) -> HumanTakeoverPoint:
        return HumanTakeoverPoint(
            step_index=int(h.get("step_index", 0)),
            label=h.get("label", ""),
            gate_kind=h.get("gate_kind", ""),
            required_approval=h.get("required_approval", ""),
            reason=h.get("reason", ""),
        )
    triggers = [mk_trigger(t) for t in d.get("adaptation_triggers", [])]
    stop_c = [mk_stop(c) for c in d.get("stop_conditions", [])]
    esc_c = [mk_esc(c) for c in d.get("escalation_conditions", [])]
    takeover = [mk_takeover(h) for h in d.get("human_takeover_points", [])]
    return AdaptiveExecutionPlan(
        plan_id=d.get("plan_id", ""),
        goal_text=d.get("goal_text", ""),
        steps=steps,
        branches=branches,
        default_branch_id=d.get("default_branch_id", ""),
        fallback_branch_id=d.get("fallback_branch_id", ""),
        adaptation_triggers=triggers,
        stop_conditions=stop_c,
        escalation_conditions=esc_c,
        human_takeover_points=takeover,
        allowed_action_refs=list(d.get("allowed_action_refs", [])),
        forbidden_action_refs=list(d.get("forbidden_action_refs", [])),
        sources_used=list(d.get("sources_used", [])),
        created_at=d.get("created_at", ""),
    )


def save_loop(loop: BoundedExecutionLoop, repo_root: Path | str | None = None) -> Path:
    """Persist a bounded loop; merge into active_loops.json by loop_id."""
    root = _repo_root(repo_root)
    loops = _load_loops(root)
    payload = loop.to_dict()
    existing = [i for i, L in enumerate(loops) if L.get("loop_id") == loop.loop_id]
    if existing:
        loops[existing[0]] = payload
    else:
        loops.append(payload)
    return _save_loops(root, loops)


def load_loop(loop_id: str, repo_root: Path | str | None = None) -> BoundedExecutionLoop | None:
    """Load a bounded loop by loop_id."""
    root = _repo_root(repo_root)
    loops = _load_loops(root)
    for L in loops:
        if L.get("loop_id") == loop_id:
            plan = _plan_from_dict(L.get("plan"))
            outcomes = [StepOutcome(**{k: o.get(k) for k in ["step_index", "step_id", "status", "artifact", "confidence", "drift_summary", "matched_expected"]}) for o in L.get("outcomes", [])]
            return BoundedExecutionLoop(
                loop_id=L.get("loop_id", ""),
                plan_id=L.get("plan_id", ""),
                plan=plan,
                status=L.get("status", ""),
                current_step_index=int(L.get("current_step_index", 0)),
                current_branch_id=L.get("current_branch_id", ""),
                max_steps=int(L.get("max_steps", 0)),
                steps_executed=int(L.get("steps_executed", 0)),
                required_review_step_indices=list(L.get("required_review_step_indices", [])),
                outcomes=outcomes,
                stop_reason=L.get("stop_reason", ""),
                escalation_reason=L.get("escalation_reason", ""),
                next_takeover_step_index=L.get("next_takeover_step_index"),
                fallback_activated=bool(L.get("fallback_activated", False)),
                created_at=L.get("created_at", ""),
                updated_at=L.get("updated_at", ""),
                profile_id=L.get("profile_id", ""),
                template_id=L.get("template_id", ""),
            )
    return None


def list_active_loops(
    status_filter: str | None = None,
    repo_root: Path | str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List stored loops; optionally filter by status (running, paused, awaiting_takeover, stopped, escalated, completed)."""
    root = _repo_root(repo_root)
    loops = _load_loops(root)
    if status_filter:
        loops = [L for L in loops if L.get("status") == status_filter]
    return loops[:limit]
