"""
M34E–M34H: Policy and trust gating before a background run.
Evaluate: allowed in background, simulate-only required, approval required, degraded fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.background_run.models import QueuedRecurringJob


@dataclass
class GatingResult:
    """Result of evaluating whether and how to run a background workflow."""
    allowed: bool = True
    simulate_only: bool = True
    approval_required: bool = True
    degraded_fallback: bool = False
    notes: list[str] = field(default_factory=list)


def evaluate_background_policy(
    job: QueuedRecurringJob,
    work_state: Any | None = None,
    repo_root: Path | str | None = None,
) -> GatingResult:
    """
    Evaluate policy and trust for running this recurring job in background.
    Returns: allowed, simulate_only, approval_required, degraded_fallback, notes.
    """
    root = Path(repo_root).resolve() if repo_root else None
    out = GatingResult(notes=[])

    # Default: background runs are simulate-first; real only if explicitly allowed and approved
    if "real" not in job.allowed_modes:
        out.simulate_only = True
        out.notes.append("allowed_modes does not include real")
    else:
        out.simulate_only = job.require_approval_before_real
        if job.require_approval_before_real:
            out.approval_required = True
            out.notes.append("require_approval_before_real=true")

    # Work state: job trust and simulate-only lists (when plan_ref is a job)
    if work_state is not None and job.plan_source == "job":
        plan_ref = job.plan_ref
        if hasattr(work_state, "approval_blocked_jobs") and plan_ref in getattr(work_state, "approval_blocked_jobs", []):
            out.allowed = False
            out.notes.append("job in approval_blocked_jobs")
            return out
        if hasattr(work_state, "simulate_only_jobs") and plan_ref in getattr(work_state, "simulate_only_jobs", []):
            out.simulate_only = True
            out.notes.append("job in simulate_only_jobs")

    # Human policy: if we have project/pack context, check simulate_only and blocked
    try:
        from workflow_dataset.human_policy.evaluate import evaluate as policy_evaluate
        # Use generic action class for background; project/pack from job or empty
        policy_result = policy_evaluate(
            action_class="executor_run",
            project_id="",
            pack_id="",
            repo_root=root,
        )
        if getattr(policy_result, "blocked", False):
            out.allowed = False
            out.notes.append("human_policy: blocked")
        if getattr(policy_result, "simulate_only", False):
            out.simulate_only = True
            out.notes.append("human_policy: simulate_only")
    except Exception:
        pass

    # Degraded mode: can be wired to reliability harness when "current degraded" API exists
    return out
