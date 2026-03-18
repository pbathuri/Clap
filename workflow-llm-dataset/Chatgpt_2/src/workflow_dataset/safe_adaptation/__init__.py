"""
M38I–M38L: Safe real-user adaptation and boundary manager — cohort-scoped adaptation
candidates, boundary checks, quarantine, review/apply within supported/experimental surfaces.
"""

from workflow_dataset.safe_adaptation.models import (
    AdaptationCandidate,
    AdaptationEvidenceBundle,
    CohortBoundaryCheck,
    ReviewDecision,
    QuarantineState,
    SupportedSurfaceAdaptation,
    ExperimentalSurfaceAdaptation,
    BlockedAdaptation,
    ReviewDecisionKind,
)
from workflow_dataset.safe_adaptation.boundary import (
    evaluate_boundary_check,
    classify_adaptation,
    affects_supported_surface,
    affects_experimental_surface,
    affects_blocked_surface,
    safe_for_cohort,
    must_quarantine,
    changes_trust_posture,
    experimental_only,
)
from workflow_dataset.safe_adaptation.store import (
    save_candidate,
    load_candidate,
    list_candidates,
    update_review_status,
    list_quarantined,
    append_quarantine,
    append_decision,
    list_recent_decisions,
)
from workflow_dataset.safe_adaptation.review import (
    inspect_candidate,
    accept_candidate,
    reject_candidate,
    quarantine_candidate,
    apply_within_boundaries,
    record_rationale_and_delta,
)
from workflow_dataset.safe_adaptation.evidence_bundle import (
    build_evidence_bundle,
    build_bundle_from_session_feedback,
)
from workflow_dataset.safe_adaptation.candidates import create_candidate

__all__ = [
    "AdaptationCandidate",
    "AdaptationEvidenceBundle",
    "CohortBoundaryCheck",
    "ReviewDecision",
    "QuarantineState",
    "SupportedSurfaceAdaptation",
    "ExperimentalSurfaceAdaptation",
    "BlockedAdaptation",
    "ReviewDecisionKind",
    "evaluate_boundary_check",
    "classify_adaptation",
    "affects_supported_surface",
    "affects_experimental_surface",
    "affects_blocked_surface",
    "safe_for_cohort",
    "must_quarantine",
    "changes_trust_posture",
    "experimental_only",
    "save_candidate",
    "load_candidate",
    "list_candidates",
    "update_review_status",
    "list_quarantined",
    "append_quarantine",
    "append_decision",
    "list_recent_decisions",
    "inspect_candidate",
    "accept_candidate",
    "reject_candidate",
    "quarantine_candidate",
    "apply_within_boundaries",
    "record_rationale_and_delta",
    "build_evidence_bundle",
    "build_bundle_from_session_feedback",
    "create_candidate",
]
