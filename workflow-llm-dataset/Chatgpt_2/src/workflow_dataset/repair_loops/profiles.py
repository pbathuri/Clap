"""
M46H.1: Maintenance profiles — light-touch, balanced, production-strict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_dataset.repair_loops.models import RepairGuidance, RepairGuidanceKind


@dataclass
class MaintenanceProfile:
    """M46H.1: Maintenance profile governing which repairs are allowed and do-now vs schedule-later."""
    profile_id: str
    name: str
    description: str = ""
    # Pattern IDs allowed under this profile; empty or ["*"] means all known patterns
    allowed_pattern_ids: list[str] = field(default_factory=list)
    # Pattern IDs that require council review before execute
    require_council_for_pattern_ids: list[str] = field(default_factory=list)
    # Pattern IDs recommended as "do now" when proposed (rest default to schedule_later)
    do_now_pattern_ids: list[str] = field(default_factory=list)
    # Default reason for schedule_later when not in do_now list
    schedule_later_default_reason: str = "Run in next maintenance window."
    # Max actions per plan that can be executed without explicit council (0 = no limit for operator)
    max_actions_without_council: int = 0  # 0 = no extra limit

    def is_pattern_allowed(self, pattern_id: str) -> bool:
        if not self.allowed_pattern_ids or "*" in self.allowed_pattern_ids:
            return True
        return pattern_id in self.allowed_pattern_ids

    def requires_council(self, pattern_id: str) -> bool:
        return pattern_id in self.require_council_for_pattern_ids

    def guidance_for_pattern(self, pattern_id: str) -> RepairGuidance:
        if pattern_id in self.do_now_pattern_ids:
            return RepairGuidance(
                kind=RepairGuidanceKind.do_now,
                reason="Recommended to run now to restore baseline.",
            )
        return RepairGuidance(
            kind=RepairGuidanceKind.schedule_later,
            reason=self.schedule_later_default_reason,
            suggested_schedule="next_ops_window",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "description": self.description,
            "allowed_pattern_ids": self.allowed_pattern_ids,
            "require_council_for_pattern_ids": self.require_council_for_pattern_ids,
            "do_now_pattern_ids": self.do_now_pattern_ids,
            "schedule_later_default_reason": self.schedule_later_default_reason,
            "max_actions_without_council": self.max_actions_without_council,
        }


BUILTIN_MAINTENANCE_PROFILES: list[MaintenanceProfile] = [
    MaintenanceProfile(
        profile_id="light_touch",
        name="Light-touch",
        description="Minimal automated repair; prefer read-only and schedule-later. Low risk, low disruption.",
        allowed_pattern_ids=["*"],
        require_council_for_pattern_ids=[],
        do_now_pattern_ids=["queue_calmness_retune"],
        schedule_later_default_reason="Schedule in next quiet window.",
        max_actions_without_council=0,
    ),
    MaintenanceProfile(
        profile_id="balanced",
        name="Balanced",
        description="Mix of do-now (queue, memory refresh) and schedule-later (runtime reset, automation pause).",
        allowed_pattern_ids=["*"],
        require_council_for_pattern_ids=["benchmark_refresh_rollback", "degraded_feature_quarantine"],
        do_now_pattern_ids=["queue_calmness_retune", "memory_curation_refresh", "continuity_resume_reconciliation"],
        schedule_later_default_reason="Run in next maintenance window.",
        max_actions_without_council=0,
    ),
    MaintenanceProfile(
        profile_id="production_strict",
        name="Production-strict",
        description="Most repairs require review; only low-impact actions are do-now. Council for rollback and quarantine.",
        allowed_pattern_ids=["*"],
        require_council_for_pattern_ids=[
            "benchmark_refresh_rollback",
            "degraded_feature_quarantine",
            "operator_mode_narrowing",
            "automation_suppression",
        ],
        do_now_pattern_ids=["queue_calmness_retune"],
        schedule_later_default_reason="Requires scheduled maintenance window and change approval.",
        max_actions_without_council=2,
    ),
]


def get_maintenance_profile(profile_id: str) -> MaintenanceProfile | None:
    for p in BUILTIN_MAINTENANCE_PROFILES:
        if p.profile_id == profile_id:
            return p
    return None


def list_maintenance_profile_ids() -> list[str]:
    return [p.profile_id for p in BUILTIN_MAINTENANCE_PROFILES]
