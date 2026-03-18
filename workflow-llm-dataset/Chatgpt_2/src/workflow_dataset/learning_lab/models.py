"""
M41A–M41D: Local learning lab models — pattern mapping, improvement experiment, evidence, rollback, approved scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Adoption types for external pattern mapping
ADOPT_DIRECT_CONCEPTUAL = "direct_conceptual_fit"
ADOPT_PARTIAL = "partial_fit"
REJECT = "reject"

# Experiment outcome
OUTCOME_PENDING = "pending"
OUTCOME_REJECTED = "rejected"
OUTCOME_QUARANTINED = "quarantined"
OUTCOME_PROMOTED = "promoted"

# Experiment source
SOURCE_ISSUE_CLUSTER = "issue_cluster"
SOURCE_REPEATED_CORRECTION = "repeated_correction"
SOURCE_ACCEPTED_ADAPTATION = "accepted_adaptation"

# M41D.1: Learning profile ids
PROFILE_CONSERVATIVE = "conservative"
PROFILE_BALANCED = "balanced"
PROFILE_RESEARCH_HEAVY = "research_heavy"

# M41D.1: Experiment template types (safe experiment categories)
TEMPLATE_PROMPT_TUNING = "prompt_tuning"
TEMPLATE_ROUTING_CHANGES = "routing_changes"
TEMPLATE_QUEUE_TUNING = "queue_tuning"
TEMPLATE_TRUST_THRESHOLD_TUNING = "trust_threshold_tuning"

# M41D.1: Environment for safety boundaries (local_only vs production_adjacent)
ENV_LOCAL_ONLY = "local_only"
ENV_PRODUCTION_ADJACENT = "production_adjacent"


@dataclass
class PatternMapping:
    """Reference repo → extracted pattern → current-repo target; adoption type and rationale."""
    reference_repo: str = ""  # e.g. karpathy/autoresearch
    extracted_pattern: str = ""  # e.g. "experiment loop: modify → run → compare → keep/discard"
    current_target_subsystem: str = ""  # e.g. learning_lab.experiments
    adoption_type: str = ADOPT_PARTIAL  # direct_conceptual_fit | partial_fit | reject
    rationale: str = ""
    local_first_compatible: bool = True
    production_cut_compatible: bool = True
    trust_review_implications: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_repo": self.reference_repo,
            "extracted_pattern": self.extracted_pattern,
            "current_target_subsystem": self.current_target_subsystem,
            "adoption_type": self.adoption_type,
            "rationale": self.rationale,
            "local_first_compatible": self.local_first_compatible,
            "production_cut_compatible": self.production_cut_compatible,
            "trust_review_implications": self.trust_review_implications,
        }


@dataclass
class LocalLearningSlice:
    """Local dataset slice used for an experiment (ids or filter description). M43: optional memory_slice_id for memory-backed slice."""
    slice_id: str = ""
    description: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    correction_ids: list[str] = field(default_factory=list)
    issue_ids: list[str] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)  # eval runs for before/after
    memory_slice_id: str = ""  # M43: optional ref to memory substrate slice (e.g. mem_exp_xxx, mem_cand_xxx)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "description": self.description,
            "evidence_ids": list(self.evidence_ids),
            "correction_ids": list(self.correction_ids),
            "issue_ids": list(self.issue_ids),
            "run_ids": list(self.run_ids),
            "memory_slice_id": self.memory_slice_id,
        }


@dataclass
class ExperimentEvidenceBundle:
    """Evidence bundle reference for an improvement experiment."""
    evidence_ids: list[str] = field(default_factory=list)
    correction_ids: list[str] = field(default_factory=list)
    session_ids: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_ids": list(self.evidence_ids),
            "correction_ids": list(self.correction_ids),
            "session_ids": list(self.session_ids),
            "summary": self.summary,
        }


@dataclass
class RollbackableChangeSet:
    """Record of change set that can be reverted (reference only; actual revert via corrections/safe_adaptation)."""
    change_set_id: str = ""
    description: str = ""
    target_type: str = ""  # e.g. specialization_params, adaptation
    target_id: str = ""
    applied_at_utc: str = ""
    revertible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_set_id": self.change_set_id,
            "description": self.description,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "applied_at_utc": self.applied_at_utc,
            "revertible": self.revertible,
        }


@dataclass
class ApprovedLearningScope:
    """Optional approved learning scope for experiments (metadata only)."""
    scope_id: str = ""
    label: str = ""
    description: str = ""
    allowed_sources: list[str] = field(default_factory=list)  # issue_cluster, repeated_correction, accepted_adaptation
    allowed_subsystems: list[str] = field(default_factory=list)
    max_experiments_pending: int = 10

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_id": self.scope_id,
            "label": self.label,
            "description": self.description,
            "allowed_sources": list(self.allowed_sources),
            "allowed_subsystems": list(self.allowed_subsystems),
            "max_experiments_pending": self.max_experiments_pending,
        }


@dataclass
class LearningProfile:
    """M41D.1: Learning profile — conservative, balanced, or research-heavy; constrains experiments and prod-adjacent use."""
    profile_id: str = ""
    label: str = ""
    description: str = ""
    max_pending_experiments: int = 10
    allow_production_adjacent: bool = False
    allowed_template_ids: list[str] = field(default_factory=list)  # empty = all allowed in local_only
    production_adjacent_template_ids: list[str] = field(default_factory=list)  # templates allowed in prod-adjacent
    safety_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "description": self.description,
            "max_pending_experiments": self.max_pending_experiments,
            "allow_production_adjacent": self.allow_production_adjacent,
            "allowed_template_ids": list(self.allowed_template_ids),
            "production_adjacent_template_ids": list(self.production_adjacent_template_ids),
            "safety_notes": self.safety_notes,
        }


@dataclass
class ExperimentTemplate:
    """M41D.1: Safe experiment template — prompt_tuning, routing_changes, queue_tuning, trust_threshold_tuning."""
    template_id: str = ""
    label: str = ""
    description: str = ""
    experiment_type: str = ""  # prompt_tuning | routing_changes | queue_tuning | trust_threshold_tuning
    allowed_subsystems: list[str] = field(default_factory=list)
    production_adjacent_allowed: bool = False
    safety_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "label": self.label,
            "description": self.description,
            "experiment_type": self.experiment_type,
            "allowed_subsystems": list(self.allowed_subsystems),
            "production_adjacent_allowed": self.production_adjacent_allowed,
            "safety_notes": self.safety_notes,
        }


@dataclass
class ImprovementExperiment:
    """Single improvement experiment: source, slice, status, outcome, evidence."""
    experiment_id: str = ""
    source_type: str = ""  # issue_cluster | repeated_correction | accepted_adaptation
    source_ref: str = ""  # cluster_id, correction_ids hash, adaptation_id
    label: str = ""
    created_at_utc: str = ""
    status: str = OUTCOME_PENDING  # pending | rejected | quarantined | promoted
    status_reason: str = ""
    local_slice: LocalLearningSlice | None = None
    evidence_bundle: ExperimentEvidenceBundle | None = None
    comparison_summary: str = ""  # before/after or N/A
    rollbackable_changes: list[RollbackableChangeSet] = field(default_factory=list)
    approved_scope_id: str = ""
    profile_id: str = ""  # M41D.1: learning profile when created
    template_id: str = ""  # M41D.1: experiment template (prompt_tuning, routing_changes, etc.)

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "label": self.label,
            "created_at_utc": self.created_at_utc,
            "status": self.status,
            "status_reason": self.status_reason,
            "local_slice": self.local_slice.to_dict() if self.local_slice else None,
            "evidence_bundle": self.evidence_bundle.to_dict() if self.evidence_bundle else None,
            "comparison_summary": self.comparison_summary,
            "rollbackable_changes": [c.to_dict() for c in self.rollbackable_changes],
            "approved_scope_id": self.approved_scope_id,
            "profile_id": self.profile_id,
            "template_id": self.template_id,
        }
