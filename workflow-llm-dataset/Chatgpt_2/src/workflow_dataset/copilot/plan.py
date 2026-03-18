"""
M23K: Plan preview. No execution; show jobs, order, mode, approvals, blocked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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

from workflow_dataset.job_packs import get_job_pack, load_specialization, preview_job
from workflow_dataset.job_packs.execute import resolve_params
from workflow_dataset.job_packs.policy import check_job_policy
from workflow_dataset.desktop_bench.trusted_actions import get_trusted_real_actions
from workflow_dataset.copilot.routines import get_routine, get_ordered_job_ids


@dataclass
class PlanPreview:
    """Preview of what would run: jobs, order, mode, approvals, blocked."""
    plan_id: str
    job_pack_ids: list[str]
    mode: str
    approvals_required: list[str] = field(default_factory=list)
    trusted_actions_involved: list[dict] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    blocked_reasons: dict[str, str] = field(default_factory=dict)
    step_previews: list[dict] = field(default_factory=list)
    created_at: str = ""


def build_plan_for_job(
    job_pack_id: str,
    mode: str,
    params: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> PlanPreview | None:
    """Build plan preview for a single job. No execution."""
    root = Path(repo_root).resolve() if repo_root else None
    job = get_job_pack(job_pack_id, root)
    if not job:
        return None
    params = params or {}
    spec = load_specialization(job_pack_id, root)
    resolved = resolve_params(job, spec.preferred_params if spec else {}, params)
    allowed, msg = check_job_policy(job, mode, resolved, root)
    plan_id = stable_id("plan", job_pack_id, mode, utc_now_iso(), prefix="")[:20]
    step_previews = []
    blocked = []
    blocked_reasons = {}
    if not allowed:
        blocked.append(job_pack_id)
        blocked_reasons[job_pack_id] = msg
    else:
        prev = preview_job(job_pack_id, mode, resolved, root)
        step_previews.append(prev)
    trusted = get_trusted_real_actions(root) if mode == "real" else {"trusted_actions": []}
    return PlanPreview(
        plan_id=plan_id,
        job_pack_ids=[job_pack_id],
        mode=mode,
        approvals_required=list(job.required_approvals) if job else [],
        trusted_actions_involved=trusted.get("trusted_actions", []) if mode == "real" else [],
        expected_outputs=list(job.expected_outputs) if job else [],
        blocked=blocked,
        blocked_reasons=blocked_reasons,
        step_previews=step_previews,
        created_at=utc_now_iso(),
    )


def build_plan_for_routine(
    routine_id: str,
    mode: str,
    repo_root: Path | str | None = None,
) -> PlanPreview | None:
    """Build plan preview for a routine (ordered job list). No execution."""
    root = Path(repo_root).resolve() if repo_root else None
    routine = get_routine(routine_id, root)
    if not routine:
        return None
    if routine.simulate_only and mode == "real":
        plan_id = stable_id("plan", routine_id, mode, utc_now_iso(), prefix="")[:20]
        return PlanPreview(
            plan_id=plan_id,
            job_pack_ids=get_ordered_job_ids(routine),
            mode=mode,
            approvals_required=list(routine.required_approvals),
            blocked=[f"routine_{routine_id}"],
            blocked_reasons={f"routine_{routine_id}": "Routine is simulate_only; cannot run in real mode."},
            expected_outputs=list(routine.expected_outputs),
            created_at=utc_now_iso(),
        )
    job_ids = get_ordered_job_ids(routine)
    plan_id = stable_id("plan", routine_id, ",".join(job_ids), mode, utc_now_iso(), prefix="")[:20]
    step_previews = []
    blocked = []
    blocked_reasons = {}
    for jid in job_ids:
        job = get_job_pack(jid, root)
        if not job:
            blocked.append(jid)
            blocked_reasons[jid] = "Job pack not found."
            continue
        spec = load_specialization(jid, root)
        allowed, msg = check_job_policy(job, mode, spec.preferred_params or {}, root)
        if not allowed:
            blocked.append(jid)
            blocked_reasons[jid] = msg
        prev = preview_job(jid, mode, spec.preferred_params or {}, root)
        step_previews.append(prev)
    trusted = get_trusted_real_actions(root) if mode == "real" else {"trusted_actions": []}
    return PlanPreview(
        plan_id=plan_id,
        job_pack_ids=job_ids,
        mode=mode,
        approvals_required=list(routine.required_approvals),
        trusted_actions_involved=trusted.get("trusted_actions", []),
        expected_outputs=list(routine.expected_outputs),
        blocked=blocked,
        blocked_reasons=blocked_reasons,
        step_previews=step_previews,
        created_at=utc_now_iso(),
    )
