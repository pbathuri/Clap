"""
M42E–M42H Phase A: Candidate model studio — explicit models for candidate model,
runtime variant, training/distillation path, dataset slice, evidence bundle,
experiment lineage, promotion eligibility, rollback path, supported/experimental boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ----- Candidate status -----
CANDIDATE_STATUS_DRAFT = "draft"
CANDIDATE_STATUS_READY_FOR_EVAL = "ready_for_eval"
CANDIDATE_STATUS_QUARANTINED = "quarantined"
CANDIDATE_STATUS_PROMOTED = "promoted"
CANDIDATE_STATUS_REJECTED = "rejected"

# ----- Supported / experimental boundary -----
BOUNDARY_SUPPORTED = "supported"
BOUNDARY_EXPERIMENTAL = "experimental"


@dataclass
class StudioEvidenceBundle:
    """Evidence bundle for a candidate model: refs to evidence, corrections, adaptations, clusters."""
    evidence_ids: list[str] = field(default_factory=list)
    correction_ids: list[str] = field(default_factory=list)
    adaptation_ids: list[str] = field(default_factory=list)
    cluster_ids: list[str] = field(default_factory=list)
    session_ids: list[str] = field(default_factory=list)
    summary: str = ""
    evidence_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_ids": list(self.evidence_ids),
            "correction_ids": list(self.correction_ids),
            "adaptation_ids": list(self.adaptation_ids),
            "cluster_ids": list(self.cluster_ids),
            "session_ids": list(self.session_ids),
            "summary": self.summary,
            "evidence_count": self.evidence_count,
        }


# M43: provenance source for memory-backed slice
PROVENANCE_MEMORY_SLICE = "memory_slice"


@dataclass
class DatasetSlice:
    """Bounded dataset slice for a candidate model experiment; provenance and exclusion rules. M43: optional memory_slice_id."""
    slice_id: str = ""
    candidate_id: str = ""
    name: str = ""
    provenance_source: str = ""  # corrections | accepted_adaptations | issue_clusters | ... | memory_slice
    provenance_refs: list[str] = field(default_factory=list)  # e.g. cluster_123, or memory_slice_id
    included_evidence_ids: list[str] = field(default_factory=list)
    included_correction_ids: list[str] = field(default_factory=list)
    exclusion_rule_summary: str = ""
    excluded_ids: list[str] = field(default_factory=list)
    created_at_utc: str = ""
    row_count: int = 0
    memory_slice_id: str = ""  # M43: optional ref to memory substrate slice

    def to_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "candidate_id": self.candidate_id,
            "name": self.name,
            "provenance_source": self.provenance_source,
            "provenance_refs": list(self.provenance_refs),
            "included_evidence_ids": list(self.included_evidence_ids),
            "included_correction_ids": list(self.included_correction_ids),
            "exclusion_rule_summary": self.exclusion_rule_summary,
            "excluded_ids": list(self.excluded_ids),
            "created_at_utc": self.created_at_utc,
            "row_count": self.row_count,
            "memory_slice_id": self.memory_slice_id,
        }


@dataclass
class TrainingDistillationPath:
    """Descriptor for a training/distillation path type: scope, compute, risks, required evaluation.
    M42H.1: default_safety_profile_id and production_restrictions_summary for production-adjacent use."""
    path_id: str = ""  # e.g. prompt_config_only, routing_only, lightweight_distillation
    label: str = ""
    allowed_scope: str = ""
    compute_assumptions: str = ""
    risks: list[str] = field(default_factory=list)
    required_evaluation_before_promotion: list[str] = field(default_factory=list)
    default_safety_profile_id: str = ""  # recommended safety profile when path is used production-adjacent
    production_restrictions_summary: str = ""  # human-readable summary of local-training restrictions

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "label": self.label,
            "allowed_scope": self.allowed_scope,
            "compute_assumptions": self.compute_assumptions,
            "risks": list(self.risks),
            "required_evaluation_before_promotion": list(self.required_evaluation_before_promotion),
            "default_safety_profile_id": self.default_safety_profile_id,
            "production_restrictions_summary": self.production_restrictions_summary,
        }


# ----- M42H.1: Production-adjacent restrictions for local training paths -----


@dataclass
class ProductionAdjacentRestrictions:
    """Restrictions when a candidate or path is used production-adjacent (no silent promotion)."""
    require_council_before_supported: bool = True
    no_weight_changes_in_production_scope: bool = True  # no full finetune on supported surfaces without explicit gate
    max_slice_size: int = 0  # 0 = no hard limit from this profile
    experimental_only_until_council: bool = True
    allowed_path_ids: list[str] = field(default_factory=list)  # empty = all paths subject to this profile

    def to_dict(self) -> dict[str, Any]:
        return {
            "require_council_before_supported": self.require_council_before_supported,
            "no_weight_changes_in_production_scope": self.no_weight_changes_in_production_scope,
            "max_slice_size": self.max_slice_size,
            "experimental_only_until_council": self.experimental_only_until_council,
            "allowed_path_ids": list(self.allowed_path_ids),
        }


@dataclass
class CandidateTemplate:
    """Template for creating a candidate: evaluator, vertical specialist, routing, calmness, etc."""
    template_id: str = ""
    label: str = ""
    description: str = ""
    default_training_path_id: str = ""
    default_boundary: str = BOUNDARY_EXPERIMENTAL
    suggested_provenance_sources: list[str] = field(default_factory=list)
    default_safety_profile_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "label": self.label,
            "description": self.description,
            "default_training_path_id": self.default_training_path_id,
            "default_boundary": self.default_boundary,
            "suggested_provenance_sources": list(self.suggested_provenance_sources),
            "default_safety_profile_id": self.default_safety_profile_id,
        }


@dataclass
class DistillationSafetyProfile:
    """Safety profile for distillation/training: constraints and production-adjacent restrictions."""
    profile_id: str = ""
    label: str = ""
    description: str = ""
    allowed_path_ids: list[str] = field(default_factory=list)  # empty = all paths
    production_restrictions: ProductionAdjacentRestrictions = field(default_factory=ProductionAdjacentRestrictions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "description": self.description,
            "allowed_path_ids": list(self.allowed_path_ids),
            "production_restrictions": self.production_restrictions.to_dict(),
        }


@dataclass
class CandidateRuntimeVariant:
    """Runtime variant produced by a candidate model (e.g. config bundle, routing table, checkpoint ref)."""
    variant_id: str = ""
    candidate_id: str = ""
    kind: str = ""  # config | routing | checkpoint_ref | evaluator_ref
    ref: str = ""  # path or id
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "candidate_id": self.candidate_id,
            "kind": self.kind,
            "ref": self.ref,
            "created_at_utc": self.created_at_utc,
        }


@dataclass
class ExperimentLineage:
    """Lineage for a candidate: parent candidates, evidence sources, creation path."""
    candidate_id: str = ""
    parent_candidate_ids: list[str] = field(default_factory=list)
    evidence_source_type: str = ""  # issue_cluster | adaptation | correction_set | vertical_failure | council_disagreement | ...
    evidence_source_id: str = ""
    created_at_utc: str = ""
    created_by: str = ""  # cli | api | operator

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "parent_candidate_ids": list(self.parent_candidate_ids),
            "evidence_source_type": self.evidence_source_type,
            "evidence_source_id": self.evidence_source_id,
            "created_at_utc": self.created_at_utc,
            "created_by": self.created_by,
        }


@dataclass
class PromotionEligibility:
    """Whether and why a candidate is eligible for promotion."""
    candidate_id: str = ""
    eligible: bool = False
    required_evals_done: list[str] = field(default_factory=list)
    required_evals_pending: list[str] = field(default_factory=list)
    council_review_id: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "eligible": self.eligible,
            "required_evals_done": list(self.required_evals_done),
            "required_evals_pending": list(self.required_evals_pending),
            "council_review_id": self.council_review_id,
            "summary": self.summary,
        }


@dataclass
class RollbackPath:
    """How to roll back from this candidate (e.g. previous runtime or baseline)."""
    candidate_id: str = ""
    rollback_target_id: str = ""  # runtime id or baseline label
    rollback_target_kind: str = ""  # runtime | baseline | config_snapshot
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "rollback_target_id": self.rollback_target_id,
            "rollback_target_kind": self.rollback_target_kind,
            "notes": self.notes,
        }


@dataclass
class SupportedExperimentalBoundary:
    """Marks which surfaces/scope this candidate is allowed in: supported vs experimental only."""
    candidate_id: str = ""
    boundary: str = BOUNDARY_EXPERIMENTAL  # supported | experimental
    allowed_surface_ids: list[str] = field(default_factory=list)
    experimental_only_surface_ids: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "boundary": self.boundary,
            "allowed_surface_ids": list(self.allowed_surface_ids),
            "experimental_only_surface_ids": list(self.experimental_only_surface_ids),
            "summary": self.summary,
        }


@dataclass
class CandidateModel:
    """One candidate model experiment: from evidence -> dataset slice -> path -> reviewable result.
    M42H.1: template_id and safety_profile_id record template and distillation safety profile."""
    candidate_id: str = ""
    name: str = ""
    summary: str = ""
    status: str = CANDIDATE_STATUS_DRAFT
    evidence: StudioEvidenceBundle = field(default_factory=StudioEvidenceBundle)
    dataset_slice_id: str = ""
    training_path_id: str = ""  # e.g. prompt_config_only, lightweight_distillation
    runtime_variant_id: str = ""
    template_id: str = ""  # e.g. evaluator, vertical_specialist, routing, calmness
    safety_profile_id: str = ""  # e.g. strict_production_adjacent, experimental_only
    lineage: ExperimentLineage | None = None
    promotion_eligibility: PromotionEligibility | None = None
    rollback_path: RollbackPath | None = None
    boundary: SupportedExperimentalBoundary | None = None
    cohort_id: str = ""
    created_at_utc: str = ""
    updated_at_utc: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "name": self.name,
            "summary": self.summary,
            "status": self.status,
            "evidence": self.evidence.to_dict(),
            "dataset_slice_id": self.dataset_slice_id,
            "training_path_id": self.training_path_id,
            "runtime_variant_id": self.runtime_variant_id,
            "template_id": self.template_id,
            "safety_profile_id": self.safety_profile_id,
            "cohort_id": self.cohort_id,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            "extra": dict(self.extra),
        }
        if self.lineage:
            d["lineage"] = self.lineage.to_dict()
        if self.promotion_eligibility:
            d["promotion_eligibility"] = self.promotion_eligibility.to_dict()
        if self.rollback_path:
            d["rollback_path"] = self.rollback_path.to_dict()
        if self.boundary:
            d["boundary"] = self.boundary.to_dict()
        return d
