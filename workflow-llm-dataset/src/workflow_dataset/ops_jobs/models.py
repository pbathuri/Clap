"""
M41I–M41L: Ops job model — maintenance/research loops, cadence, prerequisite, output, health, blocked, escalation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobCadence:
    """Cadence for recurring ops job: interval and optional time-of-day hint."""
    interval_hours: float = 0.0  # 0 = no recurring
    interval_days: float = 0.0   # e.g. 7 = weekly
    label: str = ""             # e.g. "daily", "weekly"

    def to_dict(self) -> dict[str, Any]:
        return {
            "interval_hours": self.interval_hours,
            "interval_days": self.interval_days,
            "label": self.label,
        }


@dataclass
class JobPrerequisite:
    """Prerequisite for running an ops job."""
    prerequisite_id: str = ""
    description: str = ""
    check_command: str = ""     # e.g. deploy-bundle validate
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "prerequisite_id": self.prerequisite_id,
            "description": self.description,
            "check_command": self.check_command,
            "required": self.required,
        }


@dataclass
class JobBlockedReason:
    """Reason an ops job is blocked."""
    reason_id: str = ""
    summary: str = ""
    escalation_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason_id": self.reason_id,
            "summary": self.summary,
            "escalation_command": self.escalation_command,
        }


@dataclass
class JobEscalationTarget:
    """Where to escalate when job is blocked or fails."""
    surface_id: str = ""        # triage | council | support | deploy_bundle | mission_control
    command_hint: str = ""
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"surface_id": self.surface_id, "command_hint": self.command_hint, "label": self.label}


@dataclass
class JobOutput:
    """Output of one ops job run."""
    run_id: str = ""
    job_id: str = ""
    outcome: str = ""           # pass | fail | degraded | blocked | skipped
    summary: str = ""
    started_utc: str = ""
    finished_utc: str = ""
    duration_seconds: float = 0.0
    output_refs: dict[str, str] = field(default_factory=dict)  # e.g. reliability_run_id, triage_report_path
    linked_surfaces: list[str] = field(default_factory=list)   # triage, council, support
    blocked_reason: str = ""
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "job_id": self.job_id,
            "outcome": self.outcome,
            "summary": self.summary,
            "started_utc": self.started_utc,
            "finished_utc": self.finished_utc,
            "duration_seconds": self.duration_seconds,
            "output_refs": dict(self.output_refs),
            "linked_surfaces": list(self.linked_surfaces),
            "blocked_reason": self.blocked_reason,
            "error_message": self.error_message,
        }


@dataclass
class JobHealth:
    """Health indicator for an ops job (from last run or prerequisite check)."""
    job_id: str = ""
    last_run_outcome: str = ""
    last_run_utc: str = ""
    prerequisites_met: bool = True
    blocked: bool = False
    blocked_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "last_run_outcome": self.last_run_outcome,
            "last_run_utc": self.last_run_utc,
            "prerequisites_met": self.prerequisites_met,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
        }


@dataclass
class OpsJob:
    """One operational maintenance/research job: id, cadence, prerequisites, run action, outputs, escalation."""
    job_id: str = ""
    name: str = ""
    description: str = ""
    job_class: str = ""         # maintenance | research_eval | audit
    cadence: JobCadence = field(default_factory=JobCadence)
    prerequisites: list[JobPrerequisite] = field(default_factory=list)
    run_command: str = ""       # CLI or internal ref, e.g. "reliability_run:golden_first_run"
    run_command_args: list[str] = field(default_factory=list)
    max_duration_seconds: float = 0.0  # advisory
    output_surfaces: list[str] = field(default_factory=list)   # triage, council, support
    escalation_targets: list[JobEscalationTarget] = field(default_factory=list)
    blocked_reasons: list[JobBlockedReason] = field(default_factory=list)
    retryable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "description": self.description,
            "job_class": self.job_class,
            "cadence": self.cadence.to_dict(),
            "prerequisites": [p.to_dict() for p in self.prerequisites],
            "run_command": self.run_command,
            "run_command_args": list(self.run_command_args),
            "max_duration_seconds": self.max_duration_seconds,
            "output_surfaces": list(self.output_surfaces),
            "escalation_targets": [e.to_dict() for e in self.escalation_targets],
            "blocked_reasons": [b.to_dict() for b in self.blocked_reasons],
            "retryable": self.retryable,
        }


# --- M41L.1 Maintenance calendars + production rhythm packs ---


@dataclass
class MaintenanceCalendarEntry:
    """One rhythm band in the maintenance calendar: e.g. daily, weekly, monthly."""
    rhythm: str = ""            # daily | twice_daily | weekly | monthly
    job_ids: list[str] = field(default_factory=list)
    label: str = ""             # e.g. "Daily", "Weekly"
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rhythm": self.rhythm,
            "job_ids": list(self.job_ids),
            "label": self.label,
            "description": self.description,
        }


@dataclass
class ProductionRhythmPack:
    """Named pack of ops jobs + review checklist for a production rhythm (weekly/monthly)."""
    pack_id: str = ""
    name: str = ""
    description: str = ""
    rhythm: str = ""            # weekly | monthly
    job_ids: list[str] = field(default_factory=list)
    review_checklist: list[str] = field(default_factory=list)  # operator-facing "review X"

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "name": self.name,
            "description": self.description,
            "rhythm": self.rhythm,
            "job_ids": list(self.job_ids),
            "review_checklist": list(self.review_checklist),
        }
