"""
M39I–M39L: Success proof and value validation — proof types, tracking, report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_launch.models import SuccessProofMetric
from workflow_dataset.vertical_launch.store import get_proof_state, get_active_launch, record_proof_met

# Standard proof ids (align with first-value milestones and extra proofs)
PROOF_FIRST_RUN_COMPLETED = "first_run_completed"
PROOF_FIRST_SIMULATE_DONE = "first_simulate_done"
PROOF_FIRST_REAL_DONE = "first_real_done"
PROOF_FIRST_USEFUL_ARTIFACT = "first_useful_artifact"
PROOF_FIRST_REVIEW_APPROVAL_CYCLE = "first_review_approval_cycle"
PROOF_FIRST_CONTINUITY_RESUME = "first_continuity_resume"
PROOF_FIRST_TRUSTED_ROUTINE = "first_trusted_routine"
PROOF_RECOVERY_FROM_FAILURE = "recovery_from_failure"
PROOF_REDUCED_BLOCKED_OVERHEAD = "reduced_blocked_overhead"

DEFAULT_PROOF_METRICS = [
    SuccessProofMetric(PROOF_FIRST_RUN_COMPLETED, "First run completed", "Install/bootstrap completed", "first_run_completed", "pending"),
    SuccessProofMetric(PROOF_FIRST_SIMULATE_DONE, "First simulate done", "First simulate run completed", "first_simulate_done", "pending"),
    SuccessProofMetric(PROOF_FIRST_REAL_DONE, "First real run done", "First trusted-real run after approvals", "first_real_done", "pending"),
    SuccessProofMetric(PROOF_FIRST_USEFUL_ARTIFACT, "First useful artifact", "First useful artifact produced", "first_artifact_produced", "pending"),
    SuccessProofMetric(PROOF_FIRST_REVIEW_APPROVAL_CYCLE, "First review/approval cycle", "First useful review/approval cycle completed", "first_review_cycle_done", "pending"),
    SuccessProofMetric(PROOF_FIRST_CONTINUITY_RESUME, "First continuity/resume", "First continuity/resume success", "first_continuity_resume", "pending"),
    SuccessProofMetric(PROOF_FIRST_TRUSTED_ROUTINE, "First trusted routine", "First recurring routine successfully trusted", "first_trusted_routine", "pending"),
    SuccessProofMetric(PROOF_RECOVERY_FROM_FAILURE, "Recovery from failure", "Successful recovery from a common failure", "recovery_completed", "pending"),
    SuccessProofMetric(PROOF_REDUCED_BLOCKED_OVERHEAD, "Reduced blocked overhead", "Reduction in blocked/manual overhead", "blocked_overhead_reduced", "pending"),
]


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_proof_metrics_for_kit(launch_kit_id: str, repo_root: Path | str | None = None) -> list[SuccessProofMetric]:
    """Return default proof metrics for a launch kit (status filled from store if active)."""
    state = get_proof_state(repo_root)
    proofs_by_id = {p["proof_id"]: p for p in state.get("proofs", []) if state.get("launch_kit_id") == launch_kit_id}
    out = []
    for m in DEFAULT_PROOF_METRICS:
        rec = proofs_by_id.get(m.proof_id, {})
        out.append(SuccessProofMetric(
            proof_id=m.proof_id,
            label=m.label,
            description=m.description,
            reached_when=m.reached_when,
            status=rec.get("status", m.status),
            reached_at_utc=rec.get("reached_at_utc", ""),
            path_id=launch_kit_id,
        ))
    return out


def build_success_proof_report(
    launch_kit_id: str,
    cohort_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build success-proof report for a launch kit. Tied to vertical, cohort, path.
    Keys: launch_kit_id, cohort_id, proofs (list of metric dicts), met_count, pending_count, failed_count,
    first_value_milestone_reached, suggested_next_proof.
    """
    root = _root(repo_root)
    metrics = get_proof_metrics_for_kit(launch_kit_id, root)
    state = get_proof_state(root)
    if state.get("launch_kit_id") == launch_kit_id:
        for m in metrics:
            for p in state.get("proofs", []):
                if p.get("proof_id") == m.proof_id:
                    m.status = p.get("status", m.status)
                    m.reached_at_utc = p.get("reached_at_utc", "")
                    break
    met = [m for m in metrics if m.status == "met"]
    pending = [m for m in metrics if m.status == "pending"]
    failed = [m for m in metrics if m.status == "failed"]
    first_value_reached = any(m.proof_id in (PROOF_FIRST_SIMULATE_DONE, PROOF_FIRST_REAL_DONE) and m.status == "met" for m in metrics)
    suggested = pending[0] if pending else None
    return {
        "launch_kit_id": launch_kit_id,
        "cohort_id": cohort_id,
        "proofs": [m.to_dict() for m in metrics],
        "met_count": len(met),
        "pending_count": len(pending),
        "failed_count": len(failed),
        "first_value_milestone_reached": first_value_reached,
        "suggested_next_proof_id": suggested.proof_id if suggested else "",
        "suggested_next_proof_label": suggested.label if suggested else "",
    }
