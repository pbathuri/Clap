"""
M38A–M38D: Cohort profile and supported-surface model — cohort profile, support level, allowed trust/workday/automation, readiness, support expectations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Support level for a surface in a cohort
SUPPORT_SUPPORTED = "supported"
SUPPORT_EXPERIMENTAL = "experimental"
SUPPORT_BLOCKED = "blocked"

# Required readiness (from release_readiness status)
READINESS_ANY = "any"
READINESS_READY_OR_DEGRADED = "ready_or_degraded"
READINESS_READY_ONLY = "ready_only"

# Support expectation
SUPPORT_EXPECTATION_FULL = "full"       # In scope; we commit to support
SUPPORT_EXPECTATION_BEST_EFFORT = "best_effort"  # Experimental; known limitations
SUPPORT_EXPECTATION_OUT_OF_SCOPE = "out_of_scope"  # Blocked for this cohort


@dataclass
class CohortProfile:
    """Cohort profile: id, label, description, surface support map, allowed trust/workday/automation, required readiness, support expectations."""
    cohort_id: str = ""
    label: str = ""
    description: str = ""
    # surface_id -> supported | experimental | blocked
    surface_support: dict[str, str] = field(default_factory=dict)
    # Allowed authority tier ids (trust)
    allowed_trust_tier_ids: list[str] = field(default_factory=list)
    # Allowed workday mode ids (simplified: start, focus, review, operator, wrap_up, resume)
    allowed_workday_modes: list[str] = field(default_factory=list)
    # Allowed automation scope: simulate_only | trusted_real | both
    allowed_automation_scope: str = "simulate_only"
    # Required release readiness: any | ready_or_degraded | ready_only
    required_readiness: str = READINESS_READY_OR_DEGRADED
    # Default workday preset id (e.g. founder_operator, analyst)
    default_workday_preset_id: str = ""
    # Default experience profile id (e.g. calm_default, first_user)
    default_experience_profile_id: str = ""
    # Support expectation summary for this cohort
    support_expectations: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cohort_id": self.cohort_id,
            "label": self.label,
            "description": self.description,
            "surface_support": dict(self.surface_support),
            "allowed_trust_tier_ids": list(self.allowed_trust_tier_ids),
            "allowed_workday_modes": list(self.allowed_workday_modes),
            "allowed_automation_scope": self.allowed_automation_scope,
            "required_readiness": self.required_readiness,
            "default_workday_preset_id": self.default_workday_preset_id,
            "default_experience_profile_id": self.default_experience_profile_id,
            "support_expectations": self.support_expectations,
        }


# M38D.1: Readiness gate — per-cohort or global condition that must pass
GATE_SOURCE_RELEASE_READINESS = "release_readiness"
GATE_SOURCE_TRIAGE = "triage"
GATE_SOURCE_RELIABILITY = "reliability"
GATE_SOURCE_TRUST = "trust"


@dataclass
class ReadinessGate:
    """One readiness gate: id, label, source of truth, required condition."""
    gate_id: str = ""
    label: str = ""
    description: str = ""
    check_source: str = GATE_SOURCE_RELEASE_READINESS  # release_readiness | triage | reliability | trust
    required_value: str = ""  # e.g. ready, ready_or_degraded, no_critical, no_downgrade
    cohort_ids: list[str] = field(default_factory=list)  # empty = applies to all cohorts that use it

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "label": self.label,
            "description": self.description,
            "check_source": self.check_source,
            "required_value": self.required_value,
            "cohort_ids": list(self.cohort_ids),
        }


# M38D.1: Cohort transition — escalation or downgrade path
TRANSITION_ESCALATION = "escalation"
TRANSITION_DOWNGRADE = "downgrade"
TRIGGER_RELIABILITY_WORSENED = "reliability_worsened"
TRIGGER_TRIAGE_RECOMMEND_DOWNGRADE = "triage_recommend_downgrade"
TRIGGER_READINESS_MET = "readiness_met"
TRIGGER_MANUAL = "manual"


@dataclass
class CohortTransition:
    """One transition path: from cohort -> to cohort, direction, trigger, criteria hint."""
    from_cohort_id: str = ""
    to_cohort_id: str = ""
    direction: str = TRANSITION_DOWNGRADE  # escalation | downgrade
    trigger: str = TRIGGER_MANUAL  # reliability_worsened | triage_recommend_downgrade | readiness_met | manual
    criteria_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_cohort_id": self.from_cohort_id,
            "to_cohort_id": self.to_cohort_id,
            "direction": self.direction,
            "trigger": self.trigger,
            "criteria_hint": self.criteria_hint,
        }
