"""
M38E–M38H: Cohort evidence and issue triage models.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EvidenceKind(str, Enum):
    """Source of evidence."""
    SESSION_FEEDBACK = "session_feedback"
    RELIABILITY_FAILURE = "reliability_failure"
    READINESS_BLOCKER = "readiness_blocker"
    DEGRADED_MODE = "degraded_mode"
    INTERVENTION = "intervention"
    OTHER = "other"


class CohortEvidenceItem(BaseModel):
    """One piece of cohort evidence (from session, reliability, readiness, etc.)."""

    evidence_id: str = Field(default="", description="Stable id (e.g. ev_...)")
    cohort_id: str = Field(default="")
    session_id: str = Field(default="")
    project_id: str = Field(default="")
    workflow_or_context: str = Field(default="")
    trust_mode: str = Field(default="")
    kind: EvidenceKind = Field(default=EvidenceKind.OTHER)
    source_ref: str = Field(default="", description="e.g. run_id, session_id, blocker_id")
    summary: str = Field(default="", description="Short summary; no unbounded freeform")
    created_at_utc: str = Field(default="")
    extra: dict[str, Any] = Field(default_factory=dict)


class DegradedModeEvidence(BaseModel):
    """Evidence that system was in degraded mode."""

    evidence_id: str = Field(default="")
    degraded_profile: str = Field(default="")
    subsystem: str = Field(default="")
    summary: str = Field(default="")
    created_at_utc: str = Field(default="")


class ReproducibilityNote(BaseModel):
    """Steps or conditions to reproduce an issue."""

    steps_summary: str = Field(default="")
    steps_detail: list[str] = Field(default_factory=list)
    reproducible: bool = Field(default=False)
    notes: str = Field(default="")


class AffectedSubsystem(BaseModel):
    """Subsystem involved in the issue."""

    subsystem_id: str = Field(default="", description="e.g. executor, install_upgrade, review_studio")
    label: str = Field(default="")


class CohortImpact(BaseModel):
    """Impact at cohort level."""

    cohort_id: str = Field(default="")
    session_count_affected: int = Field(default=0)
    should_pause_cohort: bool = Field(default=False)
    should_downgrade: bool = Field(default=False)
    summary: str = Field(default="")


class SupportabilityImpact(BaseModel):
    """Supportability impact: supported vs experimental surface, recovery exists."""

    supported_surface_involved: bool = Field(default=False)
    experimental_surface_involved: bool = Field(default=False)
    recovery_exists: bool = Field(default=False)
    trust_boundary_violation: bool = Field(default=False)
    summary: str = Field(default="")


class TriageStatus(str, Enum):
    """Triage state."""
    NEW = "new"
    INVESTIGATED = "investigated"
    REPRODUCED = "reproduced"
    MITIGATED = "mitigated"
    BLOCKED = "blocked"
    RESOLVED = "resolved"


class OperatorNotes(BaseModel):
    """Operator notes and reproduction hints."""

    reproduction_hints: str = Field(default="")
    mitigation_notes: str = Field(default="")
    internal_notes: str = Field(default="")
    updated_at_utc: str = Field(default="")


class UserObservedIssue(BaseModel):
    """One user-observed issue (triage item)."""

    issue_id: str = Field(default="", description="Stable id (e.g. issue_...)")
    cohort_id: str = Field(default="")
    project_id: str = Field(default="")
    workflow_or_context: str = Field(default="")
    trust_mode: str = Field(default="")
    evidence_ids: list[str] = Field(default_factory=list)
    severity: str = Field(default="medium", description="critical | high | medium | low")
    impact_scope: str = Field(default="", description="cohort | project | user | subsystem")
    reproducibility: str = Field(default="", description="yes | no | partial | unknown")
    affected_subsystems: list[str] = Field(default_factory=list)
    supportability: SupportabilityImpact = Field(default_factory=SupportabilityImpact)
    cohort_impact: CohortImpact | None = Field(default=None)
    triage_status: TriageStatus = Field(default=TriageStatus.NEW)
    reproducibility_note: ReproducibilityNote | None = Field(default=None)
    operator_notes: OperatorNotes | None = Field(default=None)
    summary: str = Field(default="")
    route_target: str = Field(default="", description="supportability | reliability | product")
    created_at_utc: str = Field(default="")
    updated_at_utc: str = Field(default="")
    resolved_at_utc: str = Field(default="")
    extra: dict[str, Any] = Field(default_factory=dict)


# ----- M38H.1 Issue clusters -----


class IssueCluster(BaseModel):
    """Cluster of issues by subsystem, workflow, or cohort."""

    cluster_id: str = Field(default="", description="e.g. cluster_subsystem_executor_abc")
    cohort_id: str = Field(default="")
    subsystem: str = Field(default="", description="Primary subsystem for this cluster")
    workflow_or_context: str = Field(default="")
    issue_ids: list[str] = Field(default_factory=list)
    severity: str = Field(default="", description="Highest severity in cluster")
    summary: str = Field(default="")
    playbook_id: str = Field(default="", description="Suggested mitigation playbook id")
    created_at_utc: str = Field(default="")


# ----- M38H.1 Mitigation playbooks -----


class OperatorDoNow(BaseModel):
    """What the operator should do now: guidance text + links to support/recovery/readiness."""

    guidance: str = Field(default="", description="Short 'do this now' text")
    link_support: str = Field(default="", description="e.g. workflow-dataset release triage")
    link_recovery: str = Field(default="", description="e.g. workflow-dataset recovery guide --case X")
    link_readiness: str = Field(default="", description="e.g. workflow-dataset release report")
    commands: list[str] = Field(default_factory=list, description="Suggested CLI commands")


class MitigationPlaybook(BaseModel):
    """Mitigation playbook: steps and links to support/recovery/readiness surfaces."""

    playbook_id: str = Field(default="")
    label: str = Field(default="")
    description: str = Field(default="")
    steps: list[str] = Field(default_factory=list)
    operator_do_now: OperatorDoNow = Field(default_factory=OperatorDoNow)
    link_support: str = Field(default="")
    link_recovery: str = Field(default="")
    link_readiness: str = Field(default="")
    related_subsystems: list[str] = Field(default_factory=list)
    when_to_use: str = Field(default="")
