"""
M46H.1: Safe repair bundles — grouped patterns for common degradation with operator guidance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_dataset.repair_loops.models import Precondition
from workflow_dataset.repair_loops.patterns import get_known_pattern, list_known_pattern_ids


@dataclass
class SafeRepairBundle:
    """M46H.1: Safe repair bundle — ordered pattern IDs + do-now vs schedule-later guidance."""
    bundle_id: str
    name: str
    description: str = ""
    # Ordered pattern IDs to run (first match or full sequence by design)
    pattern_ids: list[str] = field(default_factory=list)
    # When this bundle is recommended as do-now
    do_now_guidance: str = ""
    # When to schedule later
    schedule_later_guidance: str = ""
    # Short operator-facing summary
    operator_summary: str = ""
    # Optional preconditions for the bundle as a whole
    preconditions: list[Precondition] = field(default_factory=list)
    # Degradation signals that map to this bundle (signal_type, key) -> use this bundle
    signal_hints: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "name": self.name,
            "description": self.description,
            "pattern_ids": self.pattern_ids,
            "do_now_guidance": self.do_now_guidance,
            "schedule_later_guidance": self.schedule_later_guidance,
            "operator_summary": self.operator_summary,
            "preconditions": [p.to_dict() for p in self.preconditions],
            "signal_hints": list(self.signal_hints),
        }


BUILTIN_SAFE_REPAIR_BUNDLES: list[SafeRepairBundle] = [
    SafeRepairBundle(
        bundle_id="queue_memory_baseline",
        name="Queue + memory baseline",
        description="Re-establish queue calmness and memory curation baseline. Low risk.",
        pattern_ids=["queue_calmness_retune", "memory_curation_refresh"],
        do_now_guidance="Safe to run now; read-heavy and non-destructive.",
        schedule_later_guidance="If system is under load, run in next quiet window.",
        operator_summary="Do now: queue summary + calmness review, then memory curation refresh. Schedule later only if under load.",
        signal_hints=[("drift", "queue"), ("drift", "memory_curation")],
    ),
    SafeRepairBundle(
        bundle_id="degraded_runtime_recovery",
        name="Degraded runtime recovery",
        description="Recover from packs/runtime degradation: fallback reset then verify.",
        pattern_ids=["runtime_route_fallback_reset"],
        do_now_guidance="Run now if runtime is currently degraded and blocking workflows.",
        schedule_later_guidance="If degradation is intermittent, schedule during next maintenance.",
        operator_summary="Do now if blocked; otherwise schedule later. Resets route fallback and re-runs behavior query.",
        signal_hints=[("reliability_run", "packs"), ("reliability_run", "runtime_mesh"), ("degraded_profile", "packs_unavailable")],
    ),
    SafeRepairBundle(
        bundle_id="approval_planner_recovery",
        name="Approval / planner recovery",
        description="When trust or planner is blocked: operator-mode narrowing or continuity reconciliation.",
        pattern_ids=["operator_mode_narrowing", "continuity_resume_reconciliation"],
        do_now_guidance="Operator-mode narrow can be do-now to reduce blast radius; continuity reconcile is low risk.",
        schedule_later_guidance="If multiple subsystems are down, schedule full recovery in maintenance window.",
        operator_summary="Do now: continuity reconcile. Schedule later: operator-mode narrow (review scope first).",
        signal_hints=[("reliability_run", "trust"), ("reliability_run", "planner"), ("degraded_profile", "approval_blocked")],
    ),
    SafeRepairBundle(
        bundle_id="automation_feature_safety",
        name="Automation + feature safety",
        description="Pause automations or quarantine degraded feature. Prefer schedule-later with review.",
        pattern_ids=["automation_suppression", "degraded_feature_quarantine"],
        do_now_guidance="Only do-now if automation/feature is actively causing incidents.",
        schedule_later_guidance="Default: schedule pause/quarantine in next window and review impact.",
        operator_summary="Schedule later unless incident in progress. Review automation list and feature impact before running.",
        signal_hints=[("automation", "automations"), ("feature_degraded", "features")],
    ),
    SafeRepairBundle(
        bundle_id="install_benchmark_recovery",
        name="Install + benchmark recovery",
        description="After install or evaluation degradation: benchmark refresh and optional candidate rollback.",
        pattern_ids=["benchmark_refresh_rollback"],
        do_now_guidance="Not recommended do-now; involves reliability run and possible rollback.",
        schedule_later_guidance="Run in scheduled maintenance; council review recommended for rollback.",
        operator_summary="Schedule later. Run benchmark refresh in maintenance window; get council review for candidate rollback.",
        signal_hints=[("reliability_run", "install")],
    ),
]


def get_safe_repair_bundle(bundle_id: str) -> SafeRepairBundle | None:
    for b in BUILTIN_SAFE_REPAIR_BUNDLES:
        if b.bundle_id == bundle_id:
            return b
    return None


def list_safe_repair_bundle_ids() -> list[str]:
    return [b.bundle_id for b in BUILTIN_SAFE_REPAIR_BUNDLES]


def bundle_first_plan(bundle_id: str, plan_id: str | None = None) -> Any:
    """Return the first pattern in the bundle as a BoundedRepairPlan, or None if bundle/pattern missing."""
    bundle = get_safe_repair_bundle(bundle_id)
    if not bundle or not bundle.pattern_ids:
        return None
    first_pattern = bundle.pattern_ids[0]
    pid = plan_id or f"bundle_{bundle_id}_{first_pattern}"
    return get_known_pattern(first_pattern, plan_id=pid)


def bundle_pattern_ids_for_signal(signal_type: str, key: str) -> list[str]:
    """Return bundle pattern_ids for bundles that match (signal_type, key). First match wins; returns that bundle's pattern_ids."""
    for b in BUILTIN_SAFE_REPAIR_BUNDLES:
        for st, k in b.signal_hints:
            if st == signal_type and k == key:
                return b.pattern_ids
    return []
