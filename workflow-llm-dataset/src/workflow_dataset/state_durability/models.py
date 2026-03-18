"""
M37I–M37L: Durable state models — snapshot, recoverable partial state, startup readiness,
resume target, stale/corrupt markers, persistence boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PersistenceBoundary:
    """One subsystem's persistence boundary: id, path, status, last_write_utc, note."""
    subsystem_id: str = ""
    path: str = ""
    status: str = ""  # ok | missing | stale | corrupt | incomplete
    last_write_utc: str = ""
    note: str = ""
    critical_for_startup: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "path": self.path,
            "status": self.status,
            "last_write_utc": self.last_write_utc,
            "note": self.note,
            "critical_for_startup": self.critical_for_startup,
        }


@dataclass
class StaleStateMarker:
    """Marker for state that is considered stale (e.g. older than threshold)."""
    subsystem_id: str = ""
    path: str = ""
    last_write_utc: str = ""
    stale_threshold_hours: float = 24.0
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "path": self.path,
            "last_write_utc": self.last_write_utc,
            "stale_threshold_hours": self.stale_threshold_hours,
            "recommended_action": self.recommended_action,
        }


@dataclass
class CorruptedStateNote:
    """Note about corrupted or incomplete state that could not be loaded."""
    subsystem_id: str = ""
    path: str = ""
    error_summary: str = ""
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "path": self.path,
            "error_summary": self.error_summary,
            "recommended_action": self.recommended_action,
        }


@dataclass
class RecoverablePartialState:
    """State where some subsystems are ok and some missing/corrupt; safe to resume with degraded mode."""
    boundaries_ok: list[PersistenceBoundary] = field(default_factory=list)
    boundaries_missing: list[PersistenceBoundary] = field(default_factory=list)
    boundaries_corrupt: list[CorruptedStateNote] = field(default_factory=list)
    boundaries_stale: list[StaleStateMarker] = field(default_factory=list)
    can_resume_degraded: bool = True
    recommended_recovery_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundaries_ok": [b.to_dict() for b in self.boundaries_ok],
            "boundaries_missing": [b.to_dict() for b in self.boundaries_missing],
            "boundaries_corrupt": [c.to_dict() for c in self.boundaries_corrupt],
            "boundaries_stale": [s.to_dict() for s in self.boundaries_stale],
            "can_resume_degraded": self.can_resume_degraded,
            "recommended_recovery_actions": list(self.recommended_recovery_actions),
        }


@dataclass
class StartupReadiness:
    """Aggregate startup readiness: health checks, hydration order, degraded flag."""
    ready: bool = True
    generated_at_utc: str = ""
    boundaries: list[PersistenceBoundary] = field(default_factory=list)
    corrupt_notes: list[CorruptedStateNote] = field(default_factory=list)
    stale_markers: list[StaleStateMarker] = field(default_factory=list)
    hydration_order: list[str] = field(default_factory=list)
    degraded_but_usable: bool = False
    summary_lines: list[str] = field(default_factory=list)
    recommended_first_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "generated_at_utc": self.generated_at_utc,
            "boundaries": [b.to_dict() for b in self.boundaries],
            "corrupt_notes": [c.to_dict() for c in self.corrupt_notes],
            "stale_markers": [s.to_dict() for s in self.stale_markers],
            "hydration_order": list(self.hydration_order),
            "degraded_but_usable": self.degraded_but_usable,
            "summary_lines": list(self.summary_lines),
            "recommended_first_action": self.recommended_first_action,
        }


@dataclass
class ResumeTarget:
    """Single recommended resume target: label, command, quality, rationale."""
    label: str = ""
    command: str = ""
    quality: str = ""  # high | medium | low | degraded
    rationale: list[str] = field(default_factory=list)
    project_id: str = ""
    day_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "command": self.command,
            "quality": self.quality,
            "rationale": list(self.rationale),
            "project_id": self.project_id,
            "day_id": self.day_id,
        }


@dataclass
class DurableStateSnapshot:
    """Point-in-time snapshot of durable state health and key refs."""
    snapshot_id: str = ""
    generated_at_utc: str = ""
    readiness: StartupReadiness | None = None
    resume_target: ResumeTarget | None = None
    partial_state: RecoverablePartialState | None = None
    summary_lines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "generated_at_utc": self.generated_at_utc,
            "readiness": self.readiness.to_dict() if self.readiness else {},
            "resume_target": self.resume_target.to_dict() if self.resume_target else {},
            "partial_state": self.partial_state.to_dict() if self.partial_state else {},
            "summary_lines": list(self.summary_lines),
        }


# ----- M37L.1 State compaction + long-run maintenance profiles -----


@dataclass
class CompactionPolicy:
    """Policy for one subsystem: retain_days, max_items_before_summarize, summarization_kind."""
    subsystem_id: str = ""
    retain_days: int = 30
    max_items_before_summarize: int = 200
    summarization_kind: str = ""  # archive | summarize_only | skip
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "retain_days": self.retain_days,
            "max_items_before_summarize": self.max_items_before_summarize,
            "summarization_kind": self.summarization_kind,
            "description": self.description,
        }


@dataclass
class MaintenanceProfile:
    """M37L.1: Named maintenance profile — policies per subsystem, operator-facing label."""
    profile_id: str = ""
    label: str = ""
    description: str = ""
    policies: list[CompactionPolicy] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "description": self.description,
            "policies": [p.to_dict() for p in self.policies],
        }


@dataclass
class ArchivalTarget:
    """M37L.1: One target for archival/summarization — subsystem, path or scope, item_count, oldest_utc."""
    subsystem_id: str = ""
    scope: str = ""  # e.g. background_run_history, automation_inbox_decisions, event_log
    path_or_location: str = ""
    item_count: int = 0
    oldest_utc: str = ""
    retain_days_recommended: int = 30

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "scope": self.scope,
            "path_or_location": self.path_or_location,
            "item_count": self.item_count,
            "oldest_utc": self.oldest_utc,
            "retain_days_recommended": self.retain_days_recommended,
        }


@dataclass
class CompactionRecommendation:
    """M37L.1: Single operator-facing compaction recommendation."""
    recommendation_id: str = ""
    subsystem_id: str = ""
    scope: str = ""
    operator_summary: str = ""
    action_kind: str = ""  # summarize | archive | review_only
    item_count: int = 0
    suggested_command: str = ""
    safe_to_apply: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "subsystem_id": self.subsystem_id,
            "scope": self.scope,
            "operator_summary": self.operator_summary,
            "action_kind": self.action_kind,
            "item_count": self.item_count,
            "suggested_command": self.suggested_command,
            "safe_to_apply": self.safe_to_apply,
        }


@dataclass
class CompactionRecommendationOutput:
    """M37L.1: Full output of compaction recommendations + maintenance profile used."""
    generated_at_utc: str = ""
    profile_id: str = ""
    profile_label: str = ""
    archival_targets: list[ArchivalTarget] = field(default_factory=list)
    recommendations: list[CompactionRecommendation] = field(default_factory=list)
    operator_summary_lines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at_utc": self.generated_at_utc,
            "profile_id": self.profile_id,
            "profile_label": self.profile_label,
            "archival_targets": [a.to_dict() for a in self.archival_targets],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "operator_summary_lines": list(self.operator_summary_lines),
        }
