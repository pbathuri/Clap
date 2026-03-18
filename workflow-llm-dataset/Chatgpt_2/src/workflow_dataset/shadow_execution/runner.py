"""
M45E–M45H: Create and run shadow execution loops; record expected/observed, evaluate confidence and gates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.shadow_execution.models import (
    ShadowRun,
    ExpectedOutcome,
    ObservedOutcome,
    ConfidenceScore,
    RiskMarker,
)
from workflow_dataset.shadow_execution.confidence import (
    evaluate_confidence_step,
    evaluate_confidence_loop,
    evaluate_risk_step,
    evaluate_risk_loop,
)
from workflow_dataset.shadow_execution.gates import (
    evaluate_gates_for_run,
    compute_safe_to_continue,
    compute_forced_takeover,
)
from workflow_dataset.shadow_execution.store import save_shadow_run
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


def create_shadow_run(
    plan_source: str,
    plan_ref: str,
    loop_type: str = "",
    project_id: str = "",
    repo_root: Path | str | None = None,
) -> ShadowRun:
    """Create a shadow run from plan: resolve plan, build expected outcomes, do not execute yet."""
    root = _repo_root(repo_root)
    loop_type = loop_type or ("routine" if plan_source == "routine" else "job")
    expected_outcomes: list[ExpectedOutcome] = []

    try:
        from workflow_dataset.executor.runner import resolve_plan
        from workflow_dataset.executor.mapping import plan_preview_to_envelopes
        plan = resolve_plan(plan_source, plan_ref, "simulate", root)
        if plan and getattr(plan, "job_pack_ids", None):
            blocked = getattr(plan, "blocked", []) or []
            blocked_reasons = getattr(plan, "blocked_reasons", {}) or {}
            envelopes = plan_preview_to_envelopes(
                plan.plan_id,
                plan.job_pack_ids,
                "simulate",
                blocked,
                blocked_reasons,
                root,
            )
            for env in envelopes:
                expected_outcomes.append(ExpectedOutcome(
                    step_index=env.step_index,
                    step_id=env.step_id,
                    label=env.label or env.action_ref,
                    expected_artifact=env.expected_artifact,
                    expected_status="blocked" if env.blocked_reason else "success",
                    success_criteria="simulate success",
                ))
    except Exception:
        pass

    if not expected_outcomes:
        expected_outcomes.append(ExpectedOutcome(
            step_index=0,
            step_id="step_0",
            label=plan_ref,
            expected_status="success",
            success_criteria="placeholder",
        ))

    shadow_run_id = stable_id("shadow", plan_source, plan_ref, utc_now_iso()[:16], prefix="shadow_")
    run = ShadowRun(
        shadow_run_id=shadow_run_id,
        plan_source=plan_source,
        plan_ref=plan_ref,
        loop_type=loop_type,
        status="pending",
        current_step_index=0,
        expected_outcomes=expected_outcomes,
        observed_outcomes=[],
        confidence_step=[],
        confidence_loop=None,
        risk_markers=[],
        gates=[],
        safe_to_continue=None,
        forced_takeover=None,
        timestamp_start=utc_now_iso(),
        timestamp_end="",
        executor_run_id="",
    )
    return run


def run_shadow_loop(
    run: ShadowRun,
    project_id: str = "",
    persist: bool = True,
    repo_root: Path | str | None = None,
) -> ShadowRun:
    """
    Run shadow loop: for each expected step, record observed outcome (simulate path),
    evaluate confidence and risk, evaluate gates, set safe_to_continue and forced_takeover.
    """
    root = _repo_root(repo_root)
    run.status = "running"
    observed: list[ObservedOutcome] = []
    confidence_step: list[ConfidenceScore] = []
    risk_markers: list[RiskMarker] = []

    for exp in run.expected_outcomes:
        obs_status = "success"
        if exp.expected_status == "blocked":
            obs_status = "blocked"
        observed.append(ObservedOutcome(
            step_index=exp.step_index,
            step_id=exp.step_id,
            observed_status=obs_status,
            observed_artifact=exp.expected_artifact,
            drift_summary="",
            matched_expected=(obs_status == exp.expected_status),
        ))
        conf = evaluate_confidence_step(
            exp.step_index,
            exp.step_id,
            plan_ref=run.plan_ref,
            loop_type=run.loop_type,
            project_id=project_id,
            repo_root=root,
        )
        confidence_step.append(conf)
        risk_markers.append(evaluate_risk_step(exp.step_index, conf.score, obs_status, root))

    run.observed_outcomes = observed
    run.confidence_step = confidence_step
    step_scores = [c.score for c in confidence_step]
    run.confidence_loop = evaluate_confidence_loop(
        plan_ref=run.plan_ref,
        loop_type=run.loop_type,
        step_scores=step_scores,
        project_id=project_id,
        repo_root=root,
    )
    any_high = any(r.level == "high" for r in risk_markers)
    run.risk_markers = risk_markers
    run.risk_markers.append(evaluate_risk_loop(run.confidence_loop.score, any_high))

    run.gates = evaluate_gates_for_run(run)
    run.safe_to_continue = compute_safe_to_continue(run)
    run.forced_takeover = compute_forced_takeover(run)

    if run.forced_takeover and run.forced_takeover.forced:
        run.status = "takeover"
    else:
        run.status = "completed"
    run.timestamp_end = utc_now_iso()
    run.current_step_index = len(run.expected_outcomes)

    if persist:
        save_shadow_run(run, repo_root=root)
    return run
