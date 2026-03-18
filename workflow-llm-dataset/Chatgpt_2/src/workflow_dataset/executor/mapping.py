"""
M26E–M26H: Map compiled plan (PlanPreview) to action envelopes.
Uses job policy and step classifier; no new execution paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.executor.models import ActionEnvelope
from workflow_dataset.macros.step_classifier import classify_step
from workflow_dataset.macros.schema import STEP_TYPE_TRUSTED_REAL
from workflow_dataset.job_packs import get_job_pack


def plan_preview_to_envelopes(
    plan_id: str,
    job_pack_ids: list[str],
    mode: str,
    blocked: list[str],
    blocked_reasons: dict[str, str],
    repo_root: Path | str | None = None,
    checkpoint_after_indices: list[int] | None = None,
) -> list[ActionEnvelope]:
    """
    Map PlanPreview (job_pack_ids, mode, blocked) to list of ActionEnvelope.
    Sets checkpoint_required before next trusted_real step or at checkpoint_after_indices.
    """
    root = Path(repo_root).resolve() if repo_root else None
    checkpoint_after = set(checkpoint_after_indices or [])
    envelopes: list[ActionEnvelope] = []
    for i, jid in enumerate(job_pack_ids):
        classified = classify_step(jid, mode, root)
        blocked_reason = blocked_reasons.get(jid, "") if jid in blocked else ""
        if not blocked_reason and classified.step_type == "blocked":
            blocked_reason = "policy or classification blocked"
        # Checkpoint required before this step if (a) we're about to run a trusted_real step in real mode, or (b) previous step was in checkpoint_after
        checkpoint_required = (
            (mode == "real" and classified.step_type == STEP_TYPE_TRUSTED_REAL)
            or (i - 1 in checkpoint_after)
        )
        job = get_job_pack(jid, root)
        approvals: list[str] = list(job.required_approvals) if job else []
        env = ActionEnvelope(
            step_id=f"step_{i}_{jid}",
            step_index=i,
            action_type="job_run",
            action_ref=jid,
            mode=mode,
            approvals_required=approvals,
            capability_required=getattr(classified, "trust_requirement", "") or "",
            expected_artifact=", ".join(classified.expected_outputs) if classified.expected_outputs else "",
            reversible=False,
            checkpoint_required=checkpoint_required,
            blocked_reason=blocked_reason,
            label=jid,
        )
        envelopes.append(env)
    return envelopes
