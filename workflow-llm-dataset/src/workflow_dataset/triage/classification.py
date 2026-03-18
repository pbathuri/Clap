"""
M38E–M38H: Classify issues by severity, scope, reproducibility, supportability, cohort impact.
"""

from __future__ import annotations

from workflow_dataset.triage.models import (
    UserObservedIssue,
    SupportabilityImpact,
    CohortImpact,
    ReproducibilityNote,
    OperatorNotes,
)


def classify_severity(blocking_count: int, outcome: str, has_critical_blocker: bool) -> str:
    """Return critical | high | medium | low."""
    if has_critical_blocker or outcome == "fail":
        return "critical"
    if outcome == "blocked" or blocking_count > 0:
        return "high"
    if outcome == "degraded":
        return "medium"
    return "low"


def classify_impact_scope(cohort_affected: bool, session_count: int) -> str:
    """Return cohort | project | user | subsystem."""
    if cohort_affected and session_count > 1:
        return "cohort"
    if session_count >= 1:
        return "project"
    return "subsystem"


def classify_supportability(
    supported_surface_involved: bool,
    experimental_involved: bool,
    recovery_exists: bool,
    trust_violation: bool,
) -> SupportabilityImpact:
    """Build supportability impact from flags."""
    return SupportabilityImpact(
        supported_surface_involved=supported_surface_involved,
        experimental_surface_involved=experimental_involved,
        recovery_exists=recovery_exists,
        trust_boundary_violation=trust_violation,
        summary="Supported surface" if supported_surface_involved else "Experimental or unknown",
    )


def classify_cohort_impact(
    cohort_id: str,
    session_count_affected: int,
    severity: str,
    supported_surface: bool,
) -> CohortImpact:
    """Recommend pause/downgrade from severity and supported surface."""
    should_pause = severity in ("critical", "high") and session_count_affected >= 1
    should_downgrade = severity == "critical" and supported_surface
    return CohortImpact(
        cohort_id=cohort_id,
        session_count_affected=session_count_affected,
        should_pause_cohort=should_pause,
        should_downgrade=should_downgrade,
        summary=f"Affected sessions: {session_count_affected}; " + ("pause recommended" if should_pause else "monitor"),
    )


def apply_classification(
    issue: UserObservedIssue,
    severity: str = "",
    impact_scope: str = "",
    reproducibility: str = "",
    supported_surface: bool = False,
    experimental_surface: bool = False,
    recovery_exists: bool = False,
    trust_violation: bool = False,
    session_count_affected: int = 0,
) -> UserObservedIssue:
    """Set classification fields on issue."""
    if severity:
        issue.severity = severity
    if impact_scope:
        issue.impact_scope = impact_scope
    if reproducibility:
        issue.reproducibility = reproducibility
    issue.supportability = classify_supportability(supported_surface, experimental_surface, recovery_exists, trust_violation)
    issue.cohort_impact = classify_cohort_impact(issue.cohort_id, session_count_affected, issue.severity, supported_surface)
    return issue
