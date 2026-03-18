"""
M30E–M30H: Data models for reliability harness and recovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GoldenPathScenario:
    """A single golden-path user journey: id, name, step IDs, optional subsystem tags per step."""
    path_id: str
    name: str
    description: str
    step_ids: list[str]
    subsystem_tags: list[str] = field(default_factory=list)  # e.g. ["install", "onboarding", "workspace"]


@dataclass
class ReliabilityRunResult:
    """Result of running one golden path: outcome, failure step index, subsystem, reasons."""
    run_id: str
    path_id: str
    path_name: str
    outcome: str  # pass | degraded | blocked | fail
    failure_step_index: int | None = None
    failure_step_id: str | None = None
    subsystem: str | None = None
    reasons: list[str] = field(default_factory=list)
    steps_results: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "path_id": self.path_id,
            "path_name": self.path_name,
            "outcome": self.outcome,
            "failure_step_index": self.failure_step_index,
            "failure_step_id": self.failure_step_id,
            "subsystem": self.subsystem,
            "reasons": self.reasons,
            "steps_results": self.steps_results,
            "timestamp": self.timestamp,
        }


@dataclass
class RecoveryCase:
    """A recovery playbook case: when to use and step-by-step guide."""
    case_id: str
    name: str
    when_to_use: str
    steps_guide: list[str]
    related_subsystems: list[str] = field(default_factory=list)


@dataclass
class DegradedModeProfile:
    """M30H.1: Degraded mode profile — which subsystems are disabled and what still works."""
    profile_id: str
    name: str
    description: str
    disabled_subsystems: list[str] = field(default_factory=list)
    still_works: list[str] = field(default_factory=list)  # flow ids, capability labels
    disabled_flows: list[str] = field(default_factory=list)  # golden path ids or capability names to avoid
    operator_explanation: str = ""


@dataclass
class FallbackRule:
    """M30H.1: Safe fallback when a subsystem is unavailable: what to disable, what to use instead."""
    when_subsystem_unavailable: str
    disable_flows: list[str] = field(default_factory=list)
    fallback_capability: str = ""  # e.g. "simulate_only", "local_templates_only"
    operator_explanation: str = ""
