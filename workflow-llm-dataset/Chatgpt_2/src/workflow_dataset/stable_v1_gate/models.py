"""
M50I–M50L: Stable v1 readiness gate — models for final evidence, blockers, warnings, and release decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StableV1Recommendation(str, Enum):
    """Final stable-v1 release recommendation."""
    APPROVED = "stable_v1_approved"
    APPROVED_NARROW = "stable_v1_approved_narrow"
    REPAIR_REQUIRED = "not_yet_repair_required"
    SCOPE_NARROW = "not_yet_scope_narrow"


@dataclass
class GateBlocker:
    """Stable-v1 gate blocker: must resolve before stable v1 can be approved."""
    id: str
    summary: str
    source: str = ""
    remediation_hint: str = ""
    severity: str = "blocker"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "source": self.source,
            "remediation_hint": self.remediation_hint,
            "severity": self.severity,
        }


@dataclass
class GateWarning:
    """Stable-v1 gate warning: may lead to narrow or repair; does not alone block approval."""
    id: str
    summary: str
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "summary": self.summary, "source": self.source}


@dataclass
class FinalEvidenceBundle:
    """Final evidence bundle for stable-v1 readiness: contract, production cut, release/reliability/support, governance, migration, sustained health, vertical value, drift/repair."""
    v1_contract_summary: str = ""
    production_cut_frozen: bool = False
    production_cut_vertical_id: str = ""
    release_readiness_status: str = ""
    launch_recommended_decision: str = ""
    stability_recommended_decision: str = ""
    v1_ops_posture_summary: str = ""
    migration_continuity_readiness: str = ""
    deploy_health_summary: str = ""
    sustained_health_summary: str = ""
    vertical_value_retention: str = ""
    drift_repair_summary: str = ""
    raw_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "v1_contract_summary": self.v1_contract_summary,
            "production_cut_frozen": self.production_cut_frozen,
            "production_cut_vertical_id": self.production_cut_vertical_id,
            "release_readiness_status": self.release_readiness_status,
            "launch_recommended_decision": self.launch_recommended_decision,
            "stability_recommended_decision": self.stability_recommended_decision,
            "v1_ops_posture_summary": self.v1_ops_posture_summary,
            "migration_continuity_readiness": self.migration_continuity_readiness,
            "deploy_health_summary": self.deploy_health_summary,
            "sustained_health_summary": self.sustained_health_summary,
            "vertical_value_retention": self.vertical_value_retention,
            "drift_repair_summary": self.drift_repair_summary,
            "raw_snapshot": dict(self.raw_snapshot),
        }


@dataclass
class StableV1ReadinessGate:
    """Result of evaluating the stable-v1 gate: passed or not, with blockers and warnings."""
    passed: bool
    blockers: list[GateBlocker] = field(default_factory=list)
    warnings: list[GateWarning] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": [w.to_dict() for w in self.warnings],
            "summary": self.summary,
        }


@dataclass
class ConfidenceSummary:
    """Confidence and rationale summary for the final decision."""
    confidence: str = "medium"  # low | medium | high
    rationale: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    strongest_evidence_for: str = ""
    strongest_evidence_against: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "strongest_evidence_for": self.strongest_evidence_for,
            "strongest_evidence_against": self.strongest_evidence_against,
        }


@dataclass
class StableV1Decision:
    """Final stable-v1 release decision: recommendation, confidence, conditions, next action."""
    recommendation: str  # StableV1Recommendation value
    recommendation_label: str = ""
    confidence_summary: ConfidenceSummary = field(default_factory=ConfidenceSummary)
    narrow_condition: str = ""  # when APPROVED_NARROW
    next_required_action: str = ""
    generated_at_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation": self.recommendation,
            "recommendation_label": self.recommendation_label,
            "confidence_summary": self.confidence_summary.to_dict(),
            "narrow_condition": self.narrow_condition,
            "next_required_action": self.next_required_action,
            "generated_at_iso": self.generated_at_iso,
        }


@dataclass
class StableV1Report:
    """Full stable-v1 report: evidence, gate, decision, explain."""
    evidence: FinalEvidenceBundle
    gate: StableV1ReadinessGate
    decision: StableV1Decision
    explain: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence": self.evidence.to_dict(),
            "gate": self.gate.to_dict(),
            "decision": self.decision.to_dict(),
            "explain": self.explain,
        }


# ----- M50L.1 Post-v1 watch state + roadmap carry-forward -----


@dataclass
class PostV1WatchStateSummary:
    """Post-v1 watch-state summary: what to monitor after stable-v1 approval; experimental/deferred remains."""
    stable_v1_recommendation: str = ""
    narrow_conditions_in_effect: list[str] = field(default_factory=list)
    gate_warnings_summary: str = ""
    experimental_summary: str = ""
    deferred_summary: str = ""
    next_review_action: str = ""
    generated_at_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "stable_v1_recommendation": self.stable_v1_recommendation,
            "narrow_conditions_in_effect": list(self.narrow_conditions_in_effect),
            "gate_warnings_summary": self.gate_warnings_summary,
            "experimental_summary": self.experimental_summary,
            "deferred_summary": self.deferred_summary,
            "next_review_action": self.next_review_action,
            "generated_at_iso": self.generated_at_iso,
        }


@dataclass
class RoadmapCarryForwardItem:
    """Single item for work intentionally left beyond v1: experimental, deferred, or roadmap."""
    item_id: str
    label: str
    category: str = "deferred"  # experimental | deferred | roadmap
    rationale: str = ""
    when_to_revisit: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "label": self.label,
            "category": self.category,
            "rationale": self.rationale,
            "when_to_revisit": self.when_to_revisit,
            "source": self.source,
        }


@dataclass
class RoadmapCarryForwardPack:
    """Pack of items intentionally left beyond v1; summary of what remains experimental/deferred."""
    pack_id: str = "roadmap_carry_forward_pack"
    generated_at_iso: str = ""
    items: list[RoadmapCarryForwardItem] = field(default_factory=list)
    experimental_count: int = 0
    deferred_count: int = 0
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "generated_at_iso": self.generated_at_iso,
            "items": [i.to_dict() for i in self.items],
            "experimental_count": self.experimental_count,
            "deferred_count": self.deferred_count,
            "summary": self.summary,
        }
