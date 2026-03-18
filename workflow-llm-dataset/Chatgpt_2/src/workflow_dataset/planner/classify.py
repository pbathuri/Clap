"""
M26C: Classify a plan step by trust/action type. Uses job policy and macro step types.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.planner.schema import (
    PlanStep,
    ProvenanceSource,
    STEP_CLASS_REASONING,
    STEP_CLASS_LOCAL_INSPECT,
    STEP_CLASS_SANDBOX_WRITE,
    STEP_CLASS_TRUSTED_REAL_CANDIDATE,
    STEP_CLASS_HUMAN_REQUIRED,
    STEP_CLASS_BLOCKED,
)


def classify_plan_step(
    step: PlanStep,
    repo_root: Path | str | None = None,
    mode: str = "simulate",
) -> str:
    """
    Map step to: reasoning_only | local_inspect | sandbox_write | trusted_real_candidate | human_required | blocked.
    Uses job trust_level and macro step_classifier when provenance is job/macro.
    """
    if step.blocked_reason:
        return STEP_CLASS_BLOCKED
    if step.approval_required or step.checkpoint_before:
        return STEP_CLASS_HUMAN_REQUIRED

    root = Path(repo_root).resolve() if repo_root else None
    prov = step.provenance
    if not prov:
        return step.step_class or STEP_CLASS_REASONING

    if prov.kind == "job":
        try:
            from workflow_dataset.job_packs import get_job_pack
            from workflow_dataset.job_packs.policy import check_job_policy
            from workflow_dataset.macros.step_classifier import (
                classify_step as macro_classify_step,
                STEP_TYPE_SAFE_INSPECT,
                STEP_TYPE_SANDBOX_WRITE,
                STEP_TYPE_TRUSTED_REAL,
                STEP_TYPE_BLOCKED,
                STEP_TYPE_HUMAN_CHECKPOINT,
            )
            macro_step = macro_classify_step(prov.ref, mode, root)
            st = macro_step.step_type
            if st == STEP_TYPE_BLOCKED:
                return STEP_CLASS_BLOCKED
            if st == STEP_TYPE_HUMAN_CHECKPOINT:
                return STEP_CLASS_HUMAN_REQUIRED
            if st == STEP_TYPE_TRUSTED_REAL:
                return STEP_CLASS_TRUSTED_REAL_CANDIDATE
            if st == STEP_TYPE_SANDBOX_WRITE:
                return STEP_CLASS_SANDBOX_WRITE
            if st == STEP_TYPE_SAFE_INSPECT:
                return STEP_CLASS_LOCAL_INSPECT
        except Exception:
            pass
        job = get_job_pack(prov.ref, root) if root else None
        if job:
            if getattr(job, "trust_level", "") in ("simulate_only", "benchmark_only"):
                return STEP_CLASS_SANDBOX_WRITE
            if getattr(job, "real_mode_eligibility", False):
                return STEP_CLASS_TRUSTED_REAL_CANDIDATE
        return STEP_CLASS_SANDBOX_WRITE

    if prov.kind == "macro" or prov.kind == "routine":
        return step.step_class or STEP_CLASS_SANDBOX_WRITE

    if prov.kind == "task_demo":
        return STEP_CLASS_LOCAL_INSPECT

    return step.step_class or STEP_CLASS_REASONING
