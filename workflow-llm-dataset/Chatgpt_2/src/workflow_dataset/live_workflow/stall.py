"""
M33H.1: Stall detection and recovery paths for real-time workflow.

Detects when a run is stalled (e.g. no activity for threshold); suggests recovery
paths and alternate paths. Operator-facing explanations.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.live_workflow.models import (
    SupervisedLiveWorkflow,
    WorkflowRunState,
    StallDetectionResult,
    StallRecoveryPath,
    AlternatePathRecommendation,
)
from workflow_dataset.live_workflow.bundles import get_bundle
from workflow_dataset.utils.dates import utc_now_iso


def _parse_utc(s: str) -> float:
    """Parse ISO UTC to timestamp for delta. Return 0 if invalid."""
    if not s:
        return 0.0
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


def detect_stall(
    run: SupervisedLiveWorkflow,
    last_activity_utc: str | None = None,
    idle_threshold_seconds: float = 600.0,
    now_utc: str | None = None,
) -> StallDetectionResult:
    """
    Detect if the workflow run is stalled (no progress for idle_threshold_seconds).
    Uses run.updated_utc or run.last_activity_utc or last_activity_utc argument.
    """
    now = now_utc or utc_now_iso()
    ref_utc = last_activity_utc or run.last_activity_utc or run.updated_utc or run.created_utc
    ref_ts = _parse_utc(ref_utc)
    now_ts = _parse_utc(now)
    idle_seconds = (now_ts - ref_ts) if ref_ts > 0 else 0.0

    stalled = idle_seconds >= idle_threshold_seconds and run.state == WorkflowRunState.ACTIVE
    if run.state in (WorkflowRunState.BLOCKED, WorkflowRunState.PAUSED):
        stalled = False  # Already in a non-active state; stall is secondary

    result = StallDetectionResult(
        stalled=stalled,
        reason="",
        detected_at_utc=now,
        suggested_recovery_paths=[],
        alternate_paths=[],
        idle_seconds=idle_seconds,
    )
    if not stalled:
        result.reason = "No stall detected."
        return result

    result.reason = f"No progress for {int(idle_seconds)}s on step {run.current_step_index} ({_step_label(run)}). Try escalating or choosing an alternate path."
    result.suggested_recovery_paths = suggest_recovery_paths(run, result)
    result.alternate_paths = _gather_alternate_paths(run)
    return result


def _step_label(run: SupervisedLiveWorkflow) -> str:
    if run.steps and run.current_step_index < len(run.steps):
        return run.steps[run.current_step_index].label or ""
    return ""


def suggest_recovery_paths(
    run: SupervisedLiveWorkflow,
    stall_result: StallDetectionResult,
    repo_root: Any = None,
) -> list[StallRecoveryPath]:
    """
    Build suggested recovery paths for a stalled run: escalate one tier, try alternate goal, open planner.
    """
    from workflow_dataset.live_workflow.escalation import build_handoff_for_tier, next_escalation_tier

    paths: list[StallRecoveryPath] = []
    if not run.steps or run.current_step_index >= len(run.steps):
        paths.append(StallRecoveryPath(
            action_label="Start a new workflow with a goal",
            handoff_target="prefill_command",
            handoff_params={"command": "workflow-dataset live-workflow now --goal \"<goal>\""},
            reason="No current step; start fresh with a clear goal.",
        ))
        return paths

    step = run.steps[run.current_step_index]
    next_tier = next_escalation_tier(run.current_escalation_tier)
    if next_tier:
        handoff = build_handoff_for_tier(next_tier, step, run)
        paths.append(StallRecoveryPath(
            action_label=f"Escalate to {next_tier.value}",
            handoff_target=handoff.get("handoff_target", ""),
            handoff_params=handoff.get("handoff_params", {}),
            reason=f"You've been on '{step.label}' with hint-only help. Escalating gives you an action card or planner prefill.",
        ))

    paths.append(StallRecoveryPath(
        action_label="Open planner with current goal",
        handoff_target="compile_plan",
        handoff_params={"goal": run.goal_text or run.plan_ref, "plan_ref": run.plan_ref, "mode": "simulate"},
        reason="Recompile the plan to see full steps or try a different goal.",
    ))

    bundle = get_bundle(run.bundle_id, repo_root) if run.bundle_id else None
    if bundle and bundle.recovery_suggestions:
        for sug in bundle.recovery_suggestions[:3]:
            paths.append(StallRecoveryPath(
                action_label=sug,
                handoff_target="prefill_command",
                handoff_params={"command": sug},
                reason="Suggested by this workflow bundle.",
            ))

    return paths


def _gather_alternate_paths(run: SupervisedLiveWorkflow) -> list[AlternatePathRecommendation]:
    """Gather alternate-path recommendations from run's alternate_path_recommendations or bundle."""
    if run.alternate_path_recommendations:
        return [AlternatePathRecommendation.model_validate(a) for a in run.alternate_path_recommendations]
    alts: list[AlternatePathRecommendation] = []
    if run.bundle_id:
        # Will be filled by caller if bundle loaded
        pass
    return alts
