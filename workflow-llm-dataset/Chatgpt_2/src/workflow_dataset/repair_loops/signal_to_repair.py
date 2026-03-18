"""
M46E–M46H: Map drift and degradation signals to proposed bounded repair plans.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.repair_loops.models import BoundedRepairPlan
from workflow_dataset.repair_loops.patterns import get_known_pattern, list_known_pattern_ids


# Map (signal_type, subsystem or key) -> pattern_id
SIGNAL_TO_PATTERN: dict[tuple[str, str], str] = {
    ("reliability_run", "queue"): "queue_calmness_retune",
    ("reliability_run", "packs"): "runtime_route_fallback_reset",
    ("reliability_run", "runtime_mesh"): "runtime_route_fallback_reset",
    ("reliability_run", "trust"): "operator_mode_narrowing",
    ("reliability_run", "human_policy"): "operator_mode_narrowing",
    ("reliability_run", "workspace"): "continuity_resume_reconciliation",
    ("reliability_run", "planner"): "continuity_resume_reconciliation",
    ("reliability_run", "executor"): "continuity_resume_reconciliation",
    ("reliability_run", "install"): "benchmark_refresh_rollback",
    ("drift", "queue"): "queue_calmness_retune",
    ("drift", "memory"): "memory_curation_refresh",
    ("drift", "memory_curation"): "memory_curation_refresh",
    ("degraded_profile", "packs_unavailable"): "runtime_route_fallback_reset",
    ("degraded_profile", "workspace_degraded"): "continuity_resume_reconciliation",
    ("degraded_profile", "approval_blocked"): "operator_mode_narrowing",
    ("automation", "automations"): "automation_suppression",
    ("feature_degraded", "features"): "degraded_feature_quarantine",
}


def propose_plan_from_signal(
    signal_type: str,
    signal_id: str,
    subsystem: str = "",
    degraded_profile_id: str = "",
    pattern_id_override: str = "",
    plan_id: str | None = None,
) -> BoundedRepairPlan | None:
    """
    Propose a bounded repair plan from a drift/degradation signal.
    Uses subsystem or degraded_profile_id to look up pattern; pattern_id_override wins if set.
    """
    key_subsystem = subsystem.strip() or degraded_profile_id.strip()
    pattern_id = pattern_id_override.strip()
    if not pattern_id:
        pattern_id = SIGNAL_TO_PATTERN.get((signal_type, key_subsystem))
    if not pattern_id:
        # Fallback: try signal_type + "" for generic
        pattern_id = SIGNAL_TO_PATTERN.get((signal_type, ""))
    if not pattern_id:
        return None
    pid = plan_id or f"repair_{signal_id}_{pattern_id}"
    return get_known_pattern(pattern_id, plan_id=pid)


def propose_plan_and_pattern_from_signal(
    signal_type: str,
    signal_id: str,
    subsystem: str = "",
    degraded_profile_id: str = "",
    pattern_id_override: str = "",
    plan_id: str | None = None,
) -> tuple[BoundedRepairPlan | None, str]:
    """M46H.1: Like propose_plan_from_signal but returns (plan, pattern_id) for profile/bundle guidance."""
    key_subsystem = subsystem.strip() or degraded_profile_id.strip()
    pattern_id = pattern_id_override.strip()
    if not pattern_id:
        pattern_id = SIGNAL_TO_PATTERN.get((signal_type, key_subsystem)) or SIGNAL_TO_PATTERN.get((signal_type, "")) or ""
    plan = propose_plan_from_signal(
        signal_type=signal_type,
        signal_id=signal_id,
        subsystem=subsystem,
        degraded_profile_id=degraded_profile_id,
        pattern_id_override=pattern_id_override,
        plan_id=plan_id,
    )
    return (plan, pattern_id or (plan.plan_id if plan else ""))


def propose_plan_from_reliability_run(
    run_id: str,
    outcome: str,
    subsystem: str = "",
    plan_id: str | None = None,
) -> BoundedRepairPlan | None:
    """Propose repair plan from a reliability run result (outcome degraded/blocked/fail + subsystem)."""
    if outcome not in ("degraded", "blocked", "fail"):
        return None
    return propose_plan_from_signal(
        signal_type="reliability_run",
        signal_id=run_id,
        subsystem=subsystem,
        plan_id=plan_id or f"repair_{run_id}",
    )


def propose_plan_from_drift(
    drift_id: str,
    drift_key: str,
    plan_id: str | None = None,
) -> BoundedRepairPlan | None:
    """Propose repair plan from a drift signal (e.g. queue, memory_curation)."""
    return propose_plan_from_signal(
        signal_type="drift",
        signal_id=drift_id,
        subsystem=drift_key,
        plan_id=plan_id or f"repair_{drift_id}",
    )


def list_signal_mappings() -> list[dict[str, Any]]:
    """List (signal_type, key) -> pattern_id for docs/debug."""
    return [
        {"signal_type": st, "key": k, "pattern_id": p}
        for (st, k), p in sorted(SIGNAL_TO_PATTERN.items())
    ]
