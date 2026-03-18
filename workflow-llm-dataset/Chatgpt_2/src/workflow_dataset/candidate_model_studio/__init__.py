"""
M42E–M42H: Candidate model studio — bounded local candidate-model experiments from evidence.
"""

from workflow_dataset.candidate_model_studio.models import (
    CandidateModel,
    CandidateRuntimeVariant,
    TrainingDistillationPath,
    DatasetSlice,
    StudioEvidenceBundle,
    ExperimentLineage,
    PromotionEligibility,
    RollbackPath,
    SupportedExperimentalBoundary,
    ProductionAdjacentRestrictions,
    CandidateTemplate,
    DistillationSafetyProfile,
    CANDIDATE_STATUS_DRAFT,
    CANDIDATE_STATUS_READY_FOR_EVAL,
    CANDIDATE_STATUS_QUARANTINED,
    CANDIDATE_STATUS_PROMOTED,
    CANDIDATE_STATUS_REJECTED,
    BOUNDARY_SUPPORTED,
    BOUNDARY_EXPERIMENTAL,
)

__all__ = [
    "CandidateModel",
    "CandidateRuntimeVariant",
    "TrainingDistillationPath",
    "DatasetSlice",
    "StudioEvidenceBundle",
    "ExperimentLineage",
    "PromotionEligibility",
    "RollbackPath",
    "SupportedExperimentalBoundary",
    "CANDIDATE_STATUS_DRAFT",
    "CANDIDATE_STATUS_READY_FOR_EVAL",
    "CANDIDATE_STATUS_QUARANTINED",
    "CANDIDATE_STATUS_PROMOTED",
    "CANDIDATE_STATUS_REJECTED",
    "BOUNDARY_SUPPORTED",
    "BOUNDARY_EXPERIMENTAL",
    "ProductionAdjacentRestrictions",
    "CandidateTemplate",
    "DistillationSafetyProfile",
]
