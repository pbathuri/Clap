"""
M50A: v1 contract model — stable v1 contract, v1 core/advanced/quarantined/excluded, workflow contract, support commitment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class V1CoreSurface:
    """Surface in v1 core: fully supported, users may rely on it."""
    surface_id: str = ""
    label: str = ""
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"surface_id": self.surface_id, "label": self.label, "rationale": self.rationale}


@dataclass
class V1SupportedAdvancedSurface:
    """Surface in v1 advanced: supported but optional or power-user."""
    surface_id: str = ""
    label: str = ""
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"surface_id": self.surface_id, "label": self.label, "rationale": self.rationale}


@dataclass
class QuarantinedExperimentalSurface:
    """Surface quarantined as experimental: not in v1 supported set."""
    surface_id: str = ""
    label: str = ""
    reveal_rule: str = "on_demand"
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "label": self.label,
            "reveal_rule": self.reveal_rule,
            "rationale": self.rationale,
        }


@dataclass
class ExcludedSurface:
    """Surface excluded from v1: out of scope, blocked, or non-core."""
    surface_id: str = ""
    label: str = ""
    reason: str = ""  # out_of_scope | blocked | non_core

    def to_dict(self) -> dict[str, Any]:
        return {"surface_id": self.surface_id, "label": self.label, "reason": self.reason}


@dataclass
class StableWorkflowContract:
    """Stable workflow set for v1: which workflows are in scope."""
    workflow_ids: list[str] = field(default_factory=list)
    path_id: str = ""
    label: str = ""
    description: str = ""
    excluded_workflow_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_ids": list(self.workflow_ids),
            "path_id": self.path_id,
            "label": self.label,
            "description": self.description,
            "excluded_workflow_ids": list(self.excluded_workflow_ids),
        }


@dataclass
class SupportedOperatingPosture:
    """Required trust/governance and operating posture for v1."""
    trust_preset_id: str = ""
    review_gates_default: list[str] = field(default_factory=list)
    audit_posture: str = ""
    operator_mode_usage: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trust_preset_id": self.trust_preset_id,
            "review_gates_default": list(self.review_gates_default),
            "audit_posture": self.audit_posture,
            "operator_mode_usage": self.operator_mode_usage,
            "description": self.description,
        }


@dataclass
class SupportCommitmentNote:
    """What is supported for v1 and what is not."""
    summary: str = ""
    in_scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    last_updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "in_scope": list(self.in_scope),
            "out_of_scope": list(self.out_of_scope),
            "last_updated_utc": self.last_updated_utc,
        }


@dataclass
class StableV1Contract:
    """Final stable v1 product contract: core, advanced, quarantined, excluded, workflows, posture, support."""
    contract_id: str = "stable_v1_contract"
    vertical_id: str = ""
    vertical_label: str = ""
    frozen_at_utc: str = ""
    v1_core_surfaces: list[V1CoreSurface] = field(default_factory=list)
    v1_advanced_surfaces: list[V1SupportedAdvancedSurface] = field(default_factory=list)
    quarantined_surfaces: list[QuarantinedExperimentalSurface] = field(default_factory=list)
    excluded_surfaces: list[ExcludedSurface] = field(default_factory=list)
    stable_workflow_contract: StableWorkflowContract | None = None
    supported_operating_posture: SupportedOperatingPosture | None = None
    support_commitment_note: SupportCommitmentNote | None = None
    migration_support_expectation: str = ""  # e.g. continuity bundle + migration restore supported
    has_active_cut: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "vertical_id": self.vertical_id,
            "vertical_label": self.vertical_label,
            "frozen_at_utc": self.frozen_at_utc,
            "v1_core_surfaces": [s.to_dict() for s in self.v1_core_surfaces],
            "v1_advanced_surfaces": [s.to_dict() for s in self.v1_advanced_surfaces],
            "quarantined_surfaces": [s.to_dict() for s in self.quarantined_surfaces],
            "excluded_surfaces": [s.to_dict() for s in self.excluded_surfaces],
            "stable_workflow_contract": self.stable_workflow_contract.to_dict() if self.stable_workflow_contract else None,
            "supported_operating_posture": self.supported_operating_posture.to_dict() if self.supported_operating_posture else None,
            "support_commitment_note": self.support_commitment_note.to_dict() if self.support_commitment_note else None,
            "migration_support_expectation": self.migration_support_expectation,
            "has_active_cut": self.has_active_cut,
        }


# ----- M50D.1 Stable vs experimental communication packs -----


@dataclass
class SafeToRelyOnItem:
    """Single item in the 'safe to rely on' list for operator communication."""
    item_id: str = ""
    label: str = ""
    one_liner: str = ""
    category: str = ""  # surface | workflow | support | migration

    def to_dict(self) -> dict[str, Any]:
        return {"item_id": self.item_id, "label": self.label, "one_liner": self.one_liner, "category": self.category}


@dataclass
class DoNotRelyOnItem:
    """Single item in the 'do not rely on / exploratory' list."""
    item_id: str = ""
    label: str = ""
    one_liner: str = ""
    category: str = ""  # quarantined | excluded | experimental

    def to_dict(self) -> dict[str, Any]:
        return {"item_id": self.item_id, "label": self.label, "one_liner": self.one_liner, "category": self.category}


@dataclass
class StableV1CommunicationPack:
    """Stable-v1 communication pack: what is safe to rely on vs what remains exploratory. M50D.1."""
    pack_id: str = "stable_v1_communication_pack"
    generated_at_utc: str = ""
    headline: str = ""
    safe_to_rely_on: list[SafeToRelyOnItem] = field(default_factory=list)
    do_not_rely_on: list[DoNotRelyOnItem] = field(default_factory=list)
    stable_surfaces_summary: str = ""
    stable_workflows_summary: str = ""
    support_commitment_one_liner: str = ""
    exploratory_summary_one_liner: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "generated_at_utc": self.generated_at_utc,
            "headline": self.headline,
            "safe_to_rely_on": [s.to_dict() for s in self.safe_to_rely_on],
            "do_not_rely_on": [d.to_dict() for d in self.do_not_rely_on],
            "stable_surfaces_summary": self.stable_surfaces_summary,
            "stable_workflows_summary": self.stable_workflows_summary,
            "support_commitment_one_liner": self.support_commitment_one_liner,
            "exploratory_summary_one_liner": self.exploratory_summary_one_liner,
        }


@dataclass
class ExperimentalQuarantineSummary:
    """Summary of quarantined/experimental surfaces for operator communication. M50D.1."""
    summary_id: str = "experimental_quarantine_summary"
    generated_at_utc: str = ""
    headline: str = ""
    one_liner: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)  # surface_id, label, why_exploratory, reveal_rule
    count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "generated_at_utc": self.generated_at_utc,
            "headline": self.headline,
            "one_liner": self.one_liner,
            "items": list(self.items),
            "count": self.count,
        }
