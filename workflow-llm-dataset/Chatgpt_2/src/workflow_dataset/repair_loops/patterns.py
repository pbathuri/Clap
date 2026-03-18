"""
M46E–M46H: Known bounded repair patterns — queue calmness, memory curation, runtime fallback, etc.
"""

from __future__ import annotations

from workflow_dataset.repair_loops.models import (
    BoundedRepairPlan,
    RepairTargetSubsystem,
    MaintenanceAction,
    Precondition,
    RequiredReviewGate,
    ReviewGateKind,
)


def _subsystem(subsystem_id: str, name: str, description: str = "") -> RepairTargetSubsystem:
    return RepairTargetSubsystem(subsystem_id=subsystem_id, name=name, description=description)


def _gate(gate_id: str, kind: ReviewGateKind, description: str) -> RequiredReviewGate:
    return RequiredReviewGate(gate_id=gate_id, kind=kind, description=description)


# ----- Pattern templates (return new plan each time so caller can set plan_id) -----

def pattern_queue_calmness_retune(plan_id: str = "queue_calmness_retune") -> BoundedRepairPlan:
    """Re-tune queue calmness: run queue summary, then optional calmness refresh."""
    return BoundedRepairPlan(
        plan_id=plan_id,
        name="Queue calmness re-tune",
        description="Run queue summary and calmness review to re-establish baseline.",
        target_subsystem=_subsystem("queue", "Queue", "Background queue and calmness"),
        actions=[
            MaintenanceAction(
                action_id="queue_summary",
                name="Queue summary",
                description="Run queue summary (read-only).",
                run_command="queue",
                run_command_args=["summary"],
            ),
            MaintenanceAction(
                action_id="queue_calmness_review",
                name="Queue calmness review",
                description="Trigger queue calmness review ops job.",
                run_command="ops-jobs",
                run_command_args=["run", "--job", "queue_calmness_review"],
            ),
        ],
        preconditions=[],
        required_review_gate=_gate("operator_approve", ReviewGateKind.operator_approval, "Operator must approve before running queue jobs."),
        verification_command="queue",
        verification_args=["summary"],
        rollback_on_failed_repair=False,
        escalation_target="mission_control",
    )


def pattern_memory_curation_refresh(plan_id: str = "memory_curation_refresh") -> BoundedRepairPlan:
    """Refresh memory curation: compression candidates and optional summarization pass."""
    return BoundedRepairPlan(
        plan_id=plan_id,
        name="Memory curation / compression refresh",
        description="Refresh memory curation state and compression candidates.",
        target_subsystem=_subsystem("memory_curation", "Memory curation", "Summarization and compression"),
        actions=[
            MaintenanceAction(
                action_id="memory_curation_refresh",
                name="Memory curation refresh",
                description="Refresh compression candidates and summarization state.",
                run_command="memory-curation",
                run_command_args=["refresh"],
            ),
        ],
        preconditions=[],
        required_review_gate=_gate("operator_approve", ReviewGateKind.operator_approval, "Operator must approve memory refresh."),
        verification_command="memory-curation",
        verification_args=["status"],
        rollback_on_failed_repair=False,
        escalation_target="mission_control",
    )


def pattern_runtime_route_fallback_reset(plan_id: str = "runtime_route_fallback_reset") -> BoundedRepairPlan:
    """Reset runtime route fallback state (e.g. clear cached fallback, re-check routes)."""
    return BoundedRepairPlan(
        plan_id=plan_id,
        name="Runtime route fallback reset",
        description="Reset runtime route fallback to re-establish primary routes.",
        target_subsystem=_subsystem("runtime_mesh", "Runtime mesh", "Runtime and route fallback"),
        actions=[
            MaintenanceAction(
                action_id="runtime_fallback_reset",
                name="Runtime fallback reset",
                description="Reset fallback state; next request will re-evaluate routes.",
                run_command="runtime_fallback_reset",
                run_command_args=[],
            ),
        ],
        preconditions=[],
        required_review_gate=_gate("operator_approve", ReviewGateKind.operator_approval, "Operator must approve runtime reset."),
        verification_command="reliability",
        verification_args=["run", "--id", "pack_install_behavior_query"],
        rollback_on_failed_repair=True,
        escalation_target="reliability",
    )


def pattern_operator_mode_narrowing(plan_id: str = "operator_mode_narrowing") -> BoundedRepairPlan:
    """Narrow operator-mode responsibility (reduce scope of automated actions)."""
    return BoundedRepairPlan(
        plan_id=plan_id,
        name="Operator-mode responsibility narrowing",
        description="Narrow operator mode scope to reduce blast radius during degradation.",
        target_subsystem=_subsystem("operator_mode", "Operator mode", "Operator responsibility scope"),
        actions=[
            MaintenanceAction(
                action_id="operator_mode_narrow",
                name="Narrow operator mode",
                description="Set operator mode to narrowed scope.",
                run_command="operator-mode",
                run_command_args=["narrow"],
                rollback_command="operator-mode",
                rollback_args=["restore"],
            ),
        ],
        preconditions=[],
        required_review_gate=_gate("operator_approve", ReviewGateKind.operator_approval, "Operator must approve scope change."),
        verification_command="operator-mode",
        verification_args=["status"],
        rollback_on_failed_repair=True,
        escalation_target="mission_control",
    )


def pattern_automation_suppression(plan_id: str = "automation_suppression") -> BoundedRepairPlan:
    """Safe pause or suppression of selected automations."""
    return BoundedRepairPlan(
        plan_id=plan_id,
        name="Automation suppression or safe pause",
        description="Pause selected automations until degradation is resolved.",
        target_subsystem=_subsystem("automations", "Automations", "Background automations"),
        actions=[
            MaintenanceAction(
                action_id="automation_pause",
                name="Pause automations",
                description="Pause non-critical automations.",
                run_command="automations",
                run_command_args=["pause", "--safe"],
                rollback_command="automations",
                rollback_args=["resume"],
            ),
        ],
        preconditions=[],
        required_review_gate=_gate("operator_approve", ReviewGateKind.operator_approval, "Operator must approve automation pause."),
        verification_command="automation_status",
        verification_args=[],
        rollback_on_failed_repair=True,
        escalation_target="mission_control",
    )


def pattern_benchmark_refresh_candidate_rollback(plan_id: str = "benchmark_refresh_rollback") -> BoundedRepairPlan:
    """Refresh benchmark and optionally rollback candidate to last known good."""
    return BoundedRepairPlan(
        plan_id=plan_id,
        name="Benchmark refresh / candidate rollback",
        description="Refresh evaluation benchmark and optionally rollback to previous candidate.",
        target_subsystem=_subsystem("evaluation", "Evaluation", "Benchmark and candidate"),
        actions=[
            MaintenanceAction(
                action_id="benchmark_refresh",
                name="Benchmark refresh",
                description="Refresh benchmark run.",
                run_command="reliability",
                run_command_args=["run", "--id", "golden_first_run"],
            ),
            MaintenanceAction(
                action_id="candidate_rollback",
                name="Candidate rollback (optional)",
                description="Rollback to previous candidate if current degraded.",
                run_command="incubator",
                run_command_args=["rollback"],
            ),
        ],
        preconditions=[],
        required_review_gate=_gate("council_review", ReviewGateKind.council_review, "Council review recommended for candidate rollback."),
        verification_command="reliability",
        verification_args=["run", "--id", "golden_first_run"],
        rollback_on_failed_repair=True,
        escalation_target="evaluation",
    )


def pattern_degraded_feature_quarantine(plan_id: str = "degraded_feature_quarantine") -> BoundedRepairPlan:
    """Quarantine a degraded feature or surface to prevent cascade."""
    return BoundedRepairPlan(
        plan_id=plan_id,
        name="Degraded feature quarantine",
        description="Quarantine degraded feature so rest of system stays operational.",
        target_subsystem=_subsystem("features", "Features", "Feature flags and quarantine"),
        actions=[
            MaintenanceAction(
                action_id="quarantine_feature",
                name="Quarantine feature",
                description="Mark feature as quarantined; hide from active flows.",
                run_command="quarantine",
                run_command_args=["feature"],
                rollback_command="quarantine",
                rollback_args=["unquarantine"],
            ),
        ],
        preconditions=[],
        required_review_gate=_gate("operator_approve", ReviewGateKind.operator_approval, "Operator must approve quarantine."),
        verification_command="reliability",
        verification_args=["run", "--id", "golden_first_run"],
        rollback_on_failed_repair=True,
        escalation_target="mission_control",
    )


def pattern_continuity_resume_reconciliation(plan_id: str = "continuity_resume_reconciliation") -> BoundedRepairPlan:
    """Reconcile continuity/resume state (e.g. stuck sessions, resume state)."""
    return BoundedRepairPlan(
        plan_id=plan_id,
        name="Continuity / resume state reconciliation",
        description="Reconcile continuity and resume state after degradation.",
        target_subsystem=_subsystem("continuity", "Continuity", "Resume and session state"),
        actions=[
            MaintenanceAction(
                action_id="continuity_reconcile",
                name="Reconcile continuity state",
                description="Reconcile resume and session state.",
                run_command="continuity",
                run_command_args=["reconcile"],
            ),
        ],
        preconditions=[],
        required_review_gate=_gate("operator_approve", ReviewGateKind.operator_approval, "Operator must approve reconciliation."),
        verification_command="continuity",
        verification_args=["status"],
        rollback_on_failed_repair=False,
        escalation_target="mission_control",
    )


def get_known_pattern(pattern_id: str, plan_id: str | None = None) -> BoundedRepairPlan | None:
    """Return a known repair pattern by id. plan_id defaults to pattern_id."""
    pid = plan_id or pattern_id
    builders = {
        "queue_calmness_retune": pattern_queue_calmness_retune,
        "memory_curation_refresh": pattern_memory_curation_refresh,
        "runtime_route_fallback_reset": pattern_runtime_route_fallback_reset,
        "operator_mode_narrowing": pattern_operator_mode_narrowing,
        "automation_suppression": pattern_automation_suppression,
        "benchmark_refresh_rollback": pattern_benchmark_refresh_candidate_rollback,
        "degraded_feature_quarantine": pattern_degraded_feature_quarantine,
        "continuity_resume_reconciliation": pattern_continuity_resume_reconciliation,
    }
    fn = builders.get(pattern_id)
    if not fn:
        return None
    return fn(pid)


def list_known_pattern_ids() -> list[str]:
    return [
        "queue_calmness_retune",
        "memory_curation_refresh",
        "runtime_route_fallback_reset",
        "operator_mode_narrowing",
        "automation_suppression",
        "benchmark_refresh_rollback",
        "degraded_feature_quarantine",
        "continuity_resume_reconciliation",
    ]
