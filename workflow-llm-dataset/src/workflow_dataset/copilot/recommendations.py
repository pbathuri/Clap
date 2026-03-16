"""
M23K: Local recommendation layer for job packs. Explicit reasons only.
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

from workflow_dataset.job_packs import list_job_packs, get_job_pack, load_specialization, job_packs_report
from workflow_dataset.job_packs.policy import check_job_policy


def recommend_jobs(
    repo_root: Path | str | None = None,
    limit: int = 20,
    context_snapshot: Any = None,
) -> list[dict[str, Any]]:
    """
    Build recommendation list from local inspectable data only.
    Each item: recommendation_id, job_pack_id, reason, trust_level, required_approvals, mode_allowed, blocking_issues, recommended_timing_context.
    If context_snapshot is provided (WorkState or "latest" to load), adds why_now_evidence and context_trigger from trigger evaluation.
    No opaque ranking; reasons are explicit.
    """
    root = Path(repo_root).resolve() if repo_root else None
    work_state = None
    if context_snapshot == "latest":
        try:
            from workflow_dataset.context.snapshot import load_snapshot
            work_state = load_snapshot("latest", root)
        except Exception:
            pass
    elif context_snapshot is not None and hasattr(context_snapshot, "recent_successful_jobs"):
        work_state = context_snapshot
    report = job_packs_report(root)
    ids = list_job_packs(root)
    recommendations: list[dict[str, Any]] = []
    seen = set()
    # 1. Recent successful — recommend for repeat
    for r in report.get("recent_successful", [])[:limit]:
        jid = r.get("job_pack_id")
        if not jid or jid in seen:
            continue
        seen.add(jid)
        job = get_job_pack(jid, root)
        if not job:
            continue
        spec = load_specialization(jid, root)
        allowed_sim, _ = check_job_policy(job, "simulate", spec.preferred_params or {}, root)
        allowed_real, msg_real = check_job_policy(job, "real", spec.preferred_params or {}, root)
        mode_allowed = "simulate_only" if not job.real_mode_eligibility else ("trusted_real_eligible" if allowed_real else "simulate_only")
        blocking: list[str] = []
        if not allowed_real and job.real_mode_eligibility:
            blocking.append(msg_real or "approval or registry missing")
        rec = {
            "recommendation_id": f"rec_{jid}_{len(recommendations)}",
            "job_pack_id": jid,
            "reason": "recent_successful_run",
            "trust_level": job.trust_level,
            "required_approvals": list(job.required_approvals) or [],
            "mode_allowed": mode_allowed,
            "blocking_issues": blocking,
            "recommended_timing_context": "repeat_after_success",
        }
        _enrich_with_context(rec, jid, "job", work_state, root)
        recommendations.append(rec)
    # 2. Trusted for real (not yet in list)
    for jid in report.get("trusted_for_real_jobs", []):
        if jid in seen:
            continue
        seen.add(jid)
        job = get_job_pack(jid, root)
        if not job:
            continue
        spec = load_specialization(jid, root)
        allowed_real, msg_real = check_job_policy(job, "real", spec.preferred_params or {}, root)
        blocking = [] if allowed_real else [msg_real or "approval missing"]
        rec = {
            "recommendation_id": f"rec_{jid}_{len(recommendations)}",
            "job_pack_id": jid,
            "reason": "trusted_for_real",
            "trust_level": job.trust_level,
            "required_approvals": list(job.required_approvals) or [],
            "mode_allowed": "trusted_real_eligible" if allowed_real else "simulate_only",
            "blocking_issues": blocking,
            "recommended_timing_context": "trusted_daily",
        }
        _enrich_with_context(rec, jid, "job", work_state, root)
        recommendations.append(rec)
    # 3. Approval-blocked — recommend with blocking reason
    for jid in report.get("approval_blocked_jobs", []):
        if jid in seen:
            continue
        seen.add(jid)
        job = get_job_pack(jid, root)
        if not job:
            continue
        spec = load_specialization(jid, root)
        _, msg_real = check_job_policy(job, "real", spec.preferred_params or {}, root)
        rec = {
            "recommendation_id": f"rec_{jid}_{len(recommendations)}",
            "job_pack_id": jid,
            "reason": "approval_blocked",
            "trust_level": job.trust_level,
            "required_approvals": list(job.required_approvals) or [],
            "mode_allowed": "simulate_only",
            "blocking_issues": [msg_real or "approval registry or scope missing"],
            "recommended_timing_context": "after_approval_refresh",
        }
        _enrich_with_context(rec, jid, "job", work_state, root)
        recommendations.append(rec)
    # 4. Remaining simulate-only
    for jid in report.get("simulate_only_jobs", []):
        if len(recommendations) >= limit:
            break
        if jid in seen:
            continue
        seen.add(jid)
        job = get_job_pack(jid, root)
        if not job:
            continue
        rec = {
            "recommendation_id": f"rec_{jid}_{len(recommendations)}",
            "job_pack_id": jid,
            "reason": "simulate_only_available",
            "trust_level": job.trust_level,
            "required_approvals": [],
            "mode_allowed": "simulate_only",
            "blocking_issues": [],
            "recommended_timing_context": "any",
        }
        _enrich_with_context(rec, jid, "job", work_state, root)
        recommendations.append(rec)
    return recommendations[:limit]


def _enrich_with_context(
    rec: dict[str, Any],
    job_or_routine_id: str,
    kind: str,
    work_state: Any,
    root: Path | None,
) -> None:
    """Add why_now_evidence and context_trigger to rec from trigger evaluation."""
    if work_state is None:
        return
    try:
        from workflow_dataset.context.triggers import (
            evaluate_trigger_for_job,
            evaluate_trigger_for_routine,
        )
        if kind == "job":
            results = evaluate_trigger_for_job(job_or_routine_id, work_state, root)
        else:
            results = evaluate_trigger_for_routine(job_or_routine_id, work_state, root)
        triggered = [r for r in results if r.triggered]
        rec["why_now_evidence"] = [r.reason for r in triggered]
        rec["context_trigger"] = [r.trigger_type for r in triggered]
    except Exception:
        pass
