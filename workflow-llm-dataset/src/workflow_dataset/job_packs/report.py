"""
M23J: Job packs report and diagnostics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.job_packs import list_job_packs, get_job_pack, load_specialization
from workflow_dataset.job_packs.policy import check_job_policy


def job_packs_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Summary: most-used (by specialization update count), most-trusted (trust_level),
    simulate-only jobs, approval-blocked, jobs with repeated failures, jobs ready for benchmark promotion.
    """
    root = Path(repo_root).resolve() if repo_root else None
    ids = list_job_packs(root)
    report: dict[str, Any] = {
        "total_jobs": len(ids),
        "simulate_only_jobs": [],
        "trusted_for_real_jobs": [],
        "approval_blocked_jobs": [],
        "jobs_with_failure_notes": [],
        "jobs_ready_for_benchmark": [],
        "recent_successful": [],
    }
    for jid in ids:
        job = get_job_pack(jid, root)
        if not job:
            continue
        if job.trust_level == "simulate_only" or not job.real_mode_eligibility:
            report["simulate_only_jobs"].append(jid)
        if job.trust_level in ("trusted_for_real", "approval_valid_for_scope") and job.real_mode_eligibility:
            report["trusted_for_real_jobs"].append(jid)
        spec = load_specialization(jid, root)
        if spec.recurring_failure_notes:
            report["jobs_with_failure_notes"].append(jid)
        if spec.last_successful_run:
            report["recent_successful"].append({
                "job_pack_id": jid,
                "run_id": spec.last_successful_run.get("run_id"),
                "timestamp": spec.last_successful_run.get("timestamp"),
            })
        allowed, _ = check_job_policy(job, "real", spec.preferred_params or {}, root)
        if job.real_mode_eligibility and not allowed:
            report["approval_blocked_jobs"].append(jid)
    return report


def job_diagnostics(job_pack_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Per-job diagnostics: pack, specialization summary, last run, policy check for simulate and real."""
    root = Path(repo_root).resolve() if repo_root else None
    job = get_job_pack(job_pack_id, root)
    if not job:
        return {"error": f"Job pack not found: {job_pack_id}"}
    spec = load_specialization(job_pack_id, root)
    allowed_sim, msg_sim = check_job_policy(job, "simulate", {}, root)
    allowed_real, msg_real = check_job_policy(job, "real", spec.preferred_params or {}, root)
    return {
        "job_pack_id": job_pack_id,
        "title": job.title,
        "trust_level": job.trust_level,
        "real_mode_eligibility": job.real_mode_eligibility,
        "simulate_support": job.simulate_support,
        "source": {"kind": job.source.kind, "ref": job.source.ref} if job.source else None,
        "specialization": {
            "has_preferred_params": bool(spec.preferred_params),
            "last_successful_run": spec.last_successful_run,
            "recurring_failure_notes_count": len(spec.recurring_failure_notes),
        },
        "policy_simulate": {"allowed": allowed_sim, "message": msg_sim},
        "policy_real": {"allowed": allowed_real, "message": msg_real},
    }


def format_job_packs_report(report: dict[str, Any]) -> str:
    """Human-readable report."""
    lines = [
        "=== Job packs report (M23J) ===",
        "",
        f"Total jobs: {report.get('total_jobs', 0)}",
        f"Simulate-only: {report.get('simulate_only_jobs', [])}",
        f"Trusted for real: {report.get('trusted_for_real_jobs', [])}",
        f"Approval-blocked (real): {report.get('approval_blocked_jobs', [])}",
        f"Jobs with failure notes: {report.get('jobs_with_failure_notes', [])}",
        "",
    ]
    if report.get("recent_successful"):
        lines.append("Recent successful:")
        for r in report["recent_successful"][:5]:
            lines.append(f"  {r.get('job_pack_id')} run={r.get('run_id')} {r.get('timestamp')}")
    return "\n".join(lines)
