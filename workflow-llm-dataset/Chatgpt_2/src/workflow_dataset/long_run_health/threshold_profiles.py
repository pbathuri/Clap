"""
M46D.1: Drift threshold profiles — conservative, balanced, production-strict.
Profiles control when drift signals fire (tighter = more sensitive).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DriftThresholdProfile:
    """Named set of thresholds for drift detection."""
    profile_id: str
    label: str
    description: str
    # Keys used by drift_detection; defaults in collect_drift_signals when profile is None
    execution_loop_fail_ratio_max: float = 0.3  # drift when fail_ratio >= this
    intervention_rate_max: float = 0.5  # drift when rate >= this
    queue_calmness_min: float = 0.5  # drift when calmness < this
    memory_weak_cautions_max: int = 2  # drift when weak > this
    triage_open_issues_min: int = 3  # drift when open_count >= this
    takeover_count_min: int = 2  # drift when forced+taken >= this
    value_usefulness_min: float = 0.4  # drift when avg_usefulness < this
    # Severity band boundaries (optional; keep simple for first draft)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "description": self.description,
            "execution_loop_fail_ratio_max": self.execution_loop_fail_ratio_max,
            "intervention_rate_max": self.intervention_rate_max,
            "queue_calmness_min": self.queue_calmness_min,
            "memory_weak_cautions_max": self.memory_weak_cautions_max,
            "triage_open_issues_min": self.triage_open_issues_min,
            "takeover_count_min": self.takeover_count_min,
            "value_usefulness_min": self.value_usefulness_min,
        }


PROFILE_CONSERVATIVE = DriftThresholdProfile(
    profile_id="conservative",
    label="Conservative",
    description="Tighter thresholds; drift signals fire earlier. Use for new or high-stakes deployments.",
    execution_loop_fail_ratio_max=0.2,
    intervention_rate_max=0.4,
    queue_calmness_min=0.6,
    memory_weak_cautions_max=1,
    triage_open_issues_min=2,
    takeover_count_min=1,
    value_usefulness_min=0.5,
)

PROFILE_BALANCED = DriftThresholdProfile(
    profile_id="balanced",
    label="Balanced",
    description="Default thresholds; balanced sensitivity for most deployments.",
    execution_loop_fail_ratio_max=0.3,
    intervention_rate_max=0.5,
    queue_calmness_min=0.5,
    memory_weak_cautions_max=2,
    triage_open_issues_min=3,
    takeover_count_min=2,
    value_usefulness_min=0.4,
)

PROFILE_PRODUCTION_STRICT = DriftThresholdProfile(
    profile_id="production_strict",
    label="Production-strict",
    description="Looser thresholds; fewer drift signals. Use when production stability is paramount.",
    execution_loop_fail_ratio_max=0.4,
    intervention_rate_max=0.6,
    queue_calmness_min=0.4,
    memory_weak_cautions_max=4,
    triage_open_issues_min=5,
    takeover_count_min=4,
    value_usefulness_min=0.3,
)

BUILTIN_PROFILES: list[DriftThresholdProfile] = [
    PROFILE_CONSERVATIVE,
    PROFILE_BALANCED,
    PROFILE_PRODUCTION_STRICT,
]


def list_threshold_profiles() -> list[dict[str, Any]]:
    """Return all threshold profiles as dicts."""
    return [p.to_dict() for p in BUILTIN_PROFILES]


def get_threshold_profile(profile_id: str) -> DriftThresholdProfile | None:
    """Return the profile for profile_id, or None."""
    for p in BUILTIN_PROFILES:
        if p.profile_id == (profile_id or "").strip():
            return p
    return None
