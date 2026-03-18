"""
M21: Intake pipeline: validate candidate, classify role, assess risk/fit, produce recommendation.
"""

from __future__ import annotations

from workflow_dataset.capability_intake.source_models import (
    ExternalSourceCandidate,
    SourceRole,
    SourceAdoptionDecision,
)
from workflow_dataset.capability_intake.repo_classifier import classify_role
from workflow_dataset.capability_intake.source_risk import assess_risk
from workflow_dataset.capability_intake.source_fit import assess_fit


def intake_candidate(raw: dict) -> ExternalSourceCandidate:
    """Build and classify a candidate from raw metadata. No network calls."""
    c = ExternalSourceCandidate.model_validate(raw)
    if not c.recommended_role:
        c.recommended_role = classify_role(c)
    if not c.safety_risk_level:
        c.safety_risk_level = assess_risk(c)
    if not c.local_runtime_fit or not c.cloud_pack_fit:
        local, cloud = assess_fit(c)
        if not c.local_runtime_fit:
            c.local_runtime_fit = local
        if not c.cloud_pack_fit:
            c.cloud_pack_fit = cloud
    if not c.adoption_recommendation:
        c.adoption_recommendation = _recommend_adoption(c)
    return c


def _recommend_adoption(c: ExternalSourceCandidate) -> str:
    """Recommend adoption decision from risk/fit/role."""
    if c.safety_risk_level == "high" or c.recommended_role == SourceRole.UNSAFE_OR_REJECTED.value:
        return SourceAdoptionDecision.REJECT.value
    if c.unresolved_reason:
        return SourceAdoptionDecision.REFERENCE_ONLY.value
    if c.local_runtime_fit == "high" and c.safety_risk_level == "low":
        return SourceAdoptionDecision.CANDIDATE_FOR_PACK.value
    if c.local_runtime_fit in ("medium", "high") and c.safety_risk_level in ("low", "medium"):
        return SourceAdoptionDecision.OPTIONAL_WRAPPER.value
    if c.local_runtime_fit == "none" and c.cloud_pack_fit == "none":
        return SourceAdoptionDecision.REFERENCE_ONLY.value
    return SourceAdoptionDecision.BORROW_PATTERNS.value
