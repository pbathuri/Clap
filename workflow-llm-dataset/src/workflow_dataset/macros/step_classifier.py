"""
M23P: Step classification for macro runner. safe_inspect | sandbox_write | trusted_real | blocked | human_checkpoint.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.job_packs import get_job_pack
from workflow_dataset.job_packs.policy import check_job_policy
from workflow_dataset.macros.schema import (
    STEP_TYPE_SAFE_INSPECT,
    STEP_TYPE_SANDBOX_WRITE,
    STEP_TYPE_TRUSTED_REAL,
    STEP_TYPE_BLOCKED,
    STEP_TYPE_HUMAN_CHECKPOINT,
    MacroStep,
)


def classify_step(
    job_pack_id: str,
    mode: str,
    repo_root: Path | str | None = None,
    params: dict[str, Any] | None = None,
) -> MacroStep:
    """
    Classify a macro step by job pack and policy.
    - safe_inspect: simulate mode, read-only / inspect (simulate_support, no real)
    - sandbox_write: simulate mode, writes in sandbox only
    - trusted_real: real mode allowed by policy
    - blocked: not allowed (simulate not supported or real refused)
    - human_checkpoint: same as above but caller can mark checkpoint_before; classification does not set it
    """
    root = Path(repo_root).resolve() if repo_root else None
    params = params or {}
    job = get_job_pack(job_pack_id, root)
    if not job:
        return MacroStep(
            job_pack_id=job_pack_id,
            step_type=STEP_TYPE_BLOCKED,
            trust_requirement="",
            approval_requirement=False,
            simulate_eligible=False,
            real_mode_eligible=False,
            expected_outputs=[],
        )

    allowed_sim, msg_sim = check_job_policy(job, "simulate", params, root)
    allowed_real, msg_real = check_job_policy(job, "real", params, root)

    trust = getattr(job, "trust_level", "") or ""
    approval_req = bool(getattr(job, "required_approvals", None))

    if mode == "simulate":
        if not allowed_sim:
            return MacroStep(
                job_pack_id=job_pack_id,
                step_type=STEP_TYPE_BLOCKED,
                trust_requirement=trust,
                approval_requirement=approval_req,
                simulate_eligible=False,
                real_mode_eligible=job.real_mode_eligibility,
                expected_outputs=list(getattr(job, "expected_outputs", []) or []),
            )
        # Simulate allowed: treat as sandbox_write (writes stay in sandbox) or safe_inspect
        # Heuristic: if trust is benchmark_only/experimental and no real eligibility, treat as safe_inspect
        if not job.real_mode_eligibility and trust in ("benchmark_only", "experimental", "simulate_only"):
            step_type = STEP_TYPE_SAFE_INSPECT
        else:
            step_type = STEP_TYPE_SANDBOX_WRITE
        return MacroStep(
            job_pack_id=job_pack_id,
            step_type=step_type,
            trust_requirement=trust,
            approval_requirement=approval_req,
            simulate_eligible=True,
            real_mode_eligible=job.real_mode_eligibility,
            expected_outputs=list(getattr(job, "expected_outputs", []) or []),
        )

    # mode == "real"
    if not allowed_real:
        return MacroStep(
            job_pack_id=job_pack_id,
            step_type=STEP_TYPE_BLOCKED,
            trust_requirement=trust,
            approval_requirement=approval_req,
            simulate_eligible=allowed_sim,
            real_mode_eligible=job.real_mode_eligibility,
            expected_outputs=list(getattr(job, "expected_outputs", []) or []),
        )
    return MacroStep(
        job_pack_id=job_pack_id,
        step_type=STEP_TYPE_TRUSTED_REAL,
        trust_requirement=trust,
        approval_requirement=approval_req,
        simulate_eligible=allowed_sim,
        real_mode_eligible=True,
        expected_outputs=list(getattr(job, "expected_outputs", []) or []),
    )


def explain_step_categories() -> str:
    """Return a short explanation of step types for operator display."""
    return (
        "Step types: safe_inspect (read-only simulate), sandbox_write (simulate writes in sandbox), "
        "trusted_real (real mode allowed), blocked (not allowed in current mode), human_checkpoint (pause before step)."
    )
