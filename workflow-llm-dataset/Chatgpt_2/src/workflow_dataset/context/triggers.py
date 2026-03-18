"""
M23L: Context-aware trigger policies for jobs and routines. Explicit reasoning; no auto-run.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from workflow_dataset.context.work_state import WorkState


@dataclass
class TriggerResult:
    """Result of evaluating one trigger for a job or routine."""
    job_or_routine_id: str
    kind: str  # "job" | "routine"
    trigger_type: str
    triggered: bool
    reason: str
    blocker: str | None = None
    evidence: list[str] | None = None


def evaluate_trigger_for_job(
    job_pack_id: str,
    work_state: WorkState,
    repo_root: Path | str | None = None,
) -> list[TriggerResult]:
    """
    Evaluate all relevant triggers for a single job. Returns list of trigger results with explicit reasoning.
    """
    root = Path(repo_root).resolve() if repo_root else None
    results: list[TriggerResult] = []

    # Previous job succeeded recently
    recent_ids = {r.get("job_pack_id") for r in work_state.recent_successful_jobs if r.get("job_pack_id")}
    if job_pack_id in recent_ids:
        results.append(TriggerResult(
            job_or_routine_id=job_pack_id,
            kind="job",
            trigger_type="previous_job_succeeded",
            triggered=True,
            reason="Job has a recent successful run in specialization memory.",
            evidence=[f"recent_successful: {job_pack_id}"],
        ))
    else:
        results.append(TriggerResult(
            job_or_routine_id=job_pack_id,
            kind="job",
            trigger_type="previous_job_succeeded",
            triggered=False,
            reason="No recent successful run for this job.",
        ))

    # Approval present / blocked
    if job_pack_id in work_state.approval_blocked_jobs:
        results.append(TriggerResult(
            job_or_routine_id=job_pack_id,
            kind="job",
            trigger_type="approval_blocked",
            triggered=False,
            reason="Job is eligible for real mode but approval registry or scope is missing.",
            blocker="approval_registry_or_scope_missing",
        ))
    elif work_state.approvals_file_exists and job_pack_id in work_state.trusted_for_real_jobs:
        results.append(TriggerResult(
            job_or_routine_id=job_pack_id,
            kind="job",
            trigger_type="approval_present",
            triggered=True,
            reason="Approval registry exists and job is in trusted_for_real set.",
            evidence=["approvals_file_exists", "trusted_for_real_jobs"],
        ))

    # Simulate only: no real mode
    if job_pack_id in work_state.simulate_only_jobs:
        results.append(TriggerResult(
            job_or_routine_id=job_pack_id,
            kind="job",
            trigger_type="simulate_only",
            triggered=True,
            reason="Job is simulate-only; recommend for simulate mode only.",
        ))

    # Reminder due (check if any reminder targets this job)
    for rem in work_state.reminders_due_sample:
        if rem.get("job_pack_id") == job_pack_id:
            results.append(TriggerResult(
                job_or_routine_id=job_pack_id,
                kind="job",
                trigger_type="reminder_due",
                triggered=True,
                reason=f"Reminder due for this job: {rem.get('title', '')}.",
                evidence=[rem.get("reminder_id", "")],
            ))
            break

    # Intake: if job consumes intake, having intake can be a soft trigger (we don't map job->intake here; generic)
    if work_state.intake_labels:
        results.append(TriggerResult(
            job_or_routine_id=job_pack_id,
            kind="job",
            trigger_type="intake_available",
            triggered=True,
            reason=f"Intake sets available ({len(work_state.intake_labels)}); job may use them.",
            evidence=work_state.intake_labels[:3],
        ))

    return results


def evaluate_trigger_for_routine(
    routine_id: str,
    work_state: WorkState,
    repo_root: Path | str | None = None,
) -> list[TriggerResult]:
    """Evaluate triggers for a routine (reminder_due, approval for contained jobs, etc.)."""
    root = Path(repo_root).resolve() if repo_root else None
    results: list[TriggerResult] = []

    # Reminder due for this routine
    for rem in work_state.reminders_due_sample:
        if rem.get("routine_id") == routine_id:
            results.append(TriggerResult(
                job_or_routine_id=routine_id,
                kind="routine",
                trigger_type="reminder_due",
                triggered=True,
                reason=f"Reminder due for routine: {rem.get('title', '')}.",
                evidence=[rem.get("reminder_id", "")],
            ))
            break

    # Routine exists and has jobs
    if routine_id in work_state.routine_ids:
        results.append(TriggerResult(
            job_or_routine_id=routine_id,
            kind="routine",
            trigger_type="routine_defined",
            triggered=True,
            reason="Routine is defined and available to run.",
        ))
    else:
        results.append(TriggerResult(
            job_or_routine_id=routine_id,
            kind="routine",
            trigger_type="routine_defined",
            triggered=False,
            reason="Routine not found in copilot routines.",
            blocker="routine_not_found",
        ))

    return results


def evaluate_all_triggers(
    work_state: WorkState,
    repo_root: Path | str | None = None,
    job_limit: int = 30,
) -> list[TriggerResult]:
    """
    Evaluate triggers across all eligible jobs and routines. Returns flat list of results.
    """
    root = Path(repo_root).resolve() if repo_root else None
    all_job_ids = (
        [r.get("job_pack_id") for r in work_state.recent_successful_jobs if r.get("job_pack_id")]
        + work_state.trusted_for_real_jobs
        + work_state.approval_blocked_jobs
        + work_state.simulate_only_jobs
    )
    seen_jobs = set()
    job_ids = []
    for jid in all_job_ids:
        if jid and jid not in seen_jobs:
            seen_jobs.add(jid)
            job_ids.append(jid)
            if len(job_ids) >= job_limit:
                break

    results: list[TriggerResult] = []
    for jid in job_ids:
        results.extend(evaluate_trigger_for_job(jid, work_state, root))
    for rid in work_state.routine_ids:
        results.extend(evaluate_trigger_for_routine(rid, work_state, root))
    return results
