"""
M41I–M41L: Built-in ops jobs — reliability, triage, deploy, supportability, vertical value, audit.
"""

from __future__ import annotations

from workflow_dataset.ops_jobs.models import (
    OpsJob,
    JobCadence,
    JobPrerequisite,
    JobBlockedReason,
    JobEscalationTarget,
)


def _reliability_refresh() -> OpsJob:
    return OpsJob(
        job_id="reliability_refresh",
        name="Reliability sweep",
        description="Run golden-path reliability run to validate install and core flows.",
        job_class="maintenance",
        cadence=JobCadence(interval_days=1, label="daily"),
        prerequisites=[
            JobPrerequisite("install_ok", "Install check passes", "workflow-dataset package install-check", True),
        ],
        run_command="reliability_run",
        run_command_args=["golden_first_run"],
        max_duration_seconds=300,
        output_surfaces=["reliability"],
        escalation_targets=[
            JobEscalationTarget("reliability", "workflow-dataset reliability run --id golden_first_run", "Reliability"),
            JobEscalationTarget("support", "workflow-dataset recovery suggest --case failed_upgrade", "Recovery"),
        ],
        blocked_reasons=[
            JobBlockedReason("install_fail", "Install check failed", "workflow-dataset package install-check"),
        ],
        retryable=True,
    )


def _queue_calmness_review() -> OpsJob:
    return OpsJob(
        job_id="queue_calmness_review",
        name="Queue calmness review",
        description="Review queue summary and calmness; no heavy run, read-only.",
        job_class="maintenance",
        cadence=JobCadence(interval_hours=12, label="twice daily"),
        prerequisites=[],
        run_command="queue_summary",
        run_command_args=[],
        max_duration_seconds=30,
        output_surfaces=["queue"],
        escalation_targets=[JobEscalationTarget("mission_control", "workflow-dataset mission-control report", "Mission control")],
        blocked_reasons=[],
        retryable=True,
    )


def _issue_cluster_review() -> OpsJob:
    return OpsJob(
        job_id="issue_cluster_review",
        name="Issue cluster review",
        description="Refresh triage issue clusters and cohort health; surfaces open issues and recommended mitigation.",
        job_class="maintenance",
        cadence=JobCadence(interval_days=1, label="daily"),
        prerequisites=[],
        run_command="triage_health",
        run_command_args=[],
        max_duration_seconds=120,
        output_surfaces=["triage", "cohort"],
        escalation_targets=[
            JobEscalationTarget("triage", "workflow-dataset cohort health", "Cohort health"),
            JobEscalationTarget("triage", "workflow-dataset release triage playbook", "Triage playbook"),
        ],
        blocked_reasons=[],
        retryable=True,
    )


def _adaptation_audit() -> OpsJob:
    return OpsJob(
        job_id="adaptation_audit",
        name="Adaptation candidate audit",
        description="Review adaptation/experiment candidates; read-only audit.",
        job_class="audit",
        cadence=JobCadence(interval_days=7, label="weekly"),
        prerequisites=[],
        run_command="devlab_queue",
        run_command_args=[],
        max_duration_seconds=60,
        output_surfaces=["development"],
        escalation_targets=[JobEscalationTarget("mission_control", "workflow-dataset mission-control report", "Mission control")],
        blocked_reasons=[],
        retryable=True,
    )


def _production_cut_regression() -> OpsJob:
    return OpsJob(
        job_id="production_cut_regression",
        name="Production-cut regression check",
        description="Validate deployment bundle and readiness; ensure no regression for production cut.",
        job_class="maintenance",
        cadence=JobCadence(interval_days=1, label="daily"),
        prerequisites=[],
        run_command="deploy_bundle_validate",
        run_command_args=[],
        max_duration_seconds=90,
        output_surfaces=["deploy_bundle", "release_readiness"],
        escalation_targets=[
            JobEscalationTarget("deploy_bundle", "workflow-dataset deploy-bundle validate", "Deploy bundle"),
            JobEscalationTarget("deploy_bundle", "workflow-dataset deploy-bundle recovery-report", "Recovery"),
        ],
        blocked_reasons=[
            JobBlockedReason("validation_fail", "Bundle validation failed", "workflow-dataset deploy-bundle validate"),
        ],
        retryable=True,
    )


def _vertical_value_review() -> OpsJob:
    return OpsJob(
        job_id="vertical_value_review",
        name="Vertical value review",
        description="Refresh vertical pack progress and first-value path; next milestone and blocked step.",
        job_class="maintenance",
        cadence=JobCadence(interval_days=1, label="daily"),
        prerequisites=[],
        run_command="vertical_packs_progress",
        run_command_args=[],
        max_duration_seconds=30,
        output_surfaces=["vertical_packs"],
        escalation_targets=[
            JobEscalationTarget("vertical_packs", "workflow-dataset vertical-packs progress", "Vertical progress"),
            JobEscalationTarget("vertical_packs", "workflow-dataset vertical-packs recovery --id <pack> --step <N>", "Recovery"),
        ],
        blocked_reasons=[],
        retryable=True,
    )


def _supportability_refresh() -> OpsJob:
    return OpsJob(
        job_id="supportability_refresh",
        name="Supportability and readiness refresh",
        description="Refresh release readiness and supportability report.",
        job_class="maintenance",
        cadence=JobCadence(interval_days=7, label="weekly"),
        prerequisites=[],
        run_command="release_readiness",
        run_command_args=[],
        max_duration_seconds=60,
        output_surfaces=["release_readiness", "support"],
        escalation_targets=[
            JobEscalationTarget("support", "workflow-dataset release handoff-pack", "Handoff pack"),
        ],
        blocked_reasons=[],
        retryable=True,
    )


def _operator_audit_review() -> OpsJob:
    return OpsJob(
        job_id="operator_audit_review",
        name="Operator-mode audit review",
        description="Review operator mode status and maintenance mode; deploy-bundle maintenance report.",
        job_class="audit",
        cadence=JobCadence(interval_days=1, label="daily"),
        prerequisites=[],
        run_command="maintenance_mode_report",
        run_command_args=[],
        max_duration_seconds=30,
        output_surfaces=["deploy_bundle"],
        escalation_targets=[
            JobEscalationTarget("deploy_bundle", "workflow-dataset deploy-bundle maintenance-mode", "Maintenance"),
        ],
        blocked_reasons=[],
        retryable=True,
    )


BUILTIN_OPS_JOBS: list[OpsJob] = [
    _reliability_refresh(),
    _queue_calmness_review(),
    _issue_cluster_review(),
    _adaptation_audit(),
    _production_cut_regression(),
    _vertical_value_review(),
    _supportability_refresh(),
    _operator_audit_review(),
]


def get_ops_job(job_id: str) -> OpsJob | None:
    for j in BUILTIN_OPS_JOBS:
        if j.job_id == job_id:
            return j
    return None


def list_ops_job_ids() -> list[str]:
    return [j.job_id for j in BUILTIN_OPS_JOBS]
