"""
M44I–M44L Phase A: Explicit models for retrieval-grounded recommendation,
prior case, decision-rationale recall, memory-backed suggestions, weak-memory caution, memory-to-action linkage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievedPriorCase:
    """One retrieved prior case used to ground a recommendation."""
    unit_id: str = ""
    snippet: str = ""
    source: str = ""
    session_id: str = ""
    relevance_summary: str = ""
    confidence: float = 0.0  # 0–1

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "snippet": self.snippet,
            "source": self.source,
            "session_id": self.session_id,
            "relevance_summary": self.relevance_summary,
            "confidence": self.confidence,
        }


@dataclass
class DecisionRationaleRecall:
    """Recalled rationale from memory that influenced a decision."""
    rationale_id: str = ""
    summary: str = ""
    source_unit_ids: list[str] = field(default_factory=list)
    influence_strength: str = "low"  # low | medium | high

    def to_dict(self) -> dict[str, Any]:
        return {
            "rationale_id": self.rationale_id,
            "summary": self.summary,
            "source_unit_ids": self.source_unit_ids,
            "influence_strength": self.influence_strength,
        }


@dataclass
class WeakMemoryCaution:
    """Caution when memory was considered but confidence was low."""
    unit_id: str = ""
    reason_ignored: str = ""
    confidence_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "reason_ignored": self.reason_ignored,
            "confidence_score": self.confidence_score,
        }


@dataclass
class MemoryToActionLinkage:
    """Links a memory-backed recommendation to a product action (action card, queue item, project rec)."""
    recommendation_id: str = ""
    action_type: str = ""  # action_card | queue_item | project_recommendation
    action_id: str = ""
    link_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "action_type": self.action_type,
            "action_id": self.action_id,
            "link_summary": self.link_summary,
        }


@dataclass
class MemoryBackedNextStepSuggestion:
    """Memory-backed next-step suggestion (can feed assist queue or show as 'memory suggests')."""
    suggestion_id: str = ""
    title: str = ""
    description: str = ""
    project_id: str = ""
    prior_case: RetrievedPriorCase | None = None
    weak_caution: WeakMemoryCaution | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "prior_case": self.prior_case.to_dict() if self.prior_case else None,
            "weak_caution": self.weak_caution.to_dict() if self.weak_caution else None,
        }


@dataclass
class MemoryBackedOperatorFlowHint:
    """Memory-backed hint for operator-mode delegated responsibility context."""
    responsibility_id: str = ""
    hint_summary: str = ""
    prior_cases: list[RetrievedPriorCase] = field(default_factory=list)
    weak_cautions: list[WeakMemoryCaution] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "responsibility_id": self.responsibility_id,
            "hint_summary": self.hint_summary,
            "prior_cases": [p.to_dict() for p in self.prior_cases],
            "weak_cautions": [w.to_dict() for w in self.weak_cautions],
        }


@dataclass
class RetrievalGroundedRecommendation:
    """Full retrieval-grounded recommendation with prior cases, rationale, and optional weak-memory caution."""
    recommendation_id: str = ""
    kind: str = ""  # next_step | resume | planner_context | operator_hint | review_recall
    title: str = ""
    description: str = ""
    project_id: str = ""
    session_id: str = ""
    prior_cases: list[RetrievedPriorCase] = field(default_factory=list)
    rationale_recall: list[DecisionRationaleRecall] = field(default_factory=list)
    weak_cautions: list[WeakMemoryCaution] = field(default_factory=list)
    action_linkages: list[MemoryToActionLinkage] = field(default_factory=list)
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "kind": self.kind,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "prior_cases": [p.to_dict() for p in self.prior_cases],
            "rationale_recall": [r.to_dict() for r in self.rationale_recall],
            "weak_cautions": [w.to_dict() for w in self.weak_cautions],
            "action_linkages": [a.to_dict() for a in self.action_linkages],
            "created_at_utc": self.created_at_utc,
        }


# ----- M44L.1: Memory-grounded vertical playbooks + action packs -----


@dataclass
class ThisWorkedBeforeEntry:
    """Operator guidance backed by a prior successful case: 'this worked before in similar situations'."""
    guidance_id: str = ""
    situation_summary: str = ""
    what_worked: str = ""
    prior_case_unit_id: str = ""
    prior_case_snippet: str = ""
    confidence: float = 0.0
    reviewable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "guidance_id": self.guidance_id,
            "situation_summary": self.situation_summary,
            "what_worked": self.what_worked,
            "prior_case_unit_id": self.prior_case_unit_id,
            "prior_case_snippet": self.prior_case_snippet[:300],
            "confidence": self.confidence,
            "reviewable": self.reviewable,
        }


@dataclass
class MemoryGroundedPlaybook:
    """Memory-grounded vertical playbook: base playbook + prior successful cases + 'this worked before' operator guidance."""
    playbook_id: str = ""
    curated_pack_id: str = ""
    label: str = ""
    description: str = ""
    base_playbook_id: str = ""
    prior_successful_cases: list[RetrievedPriorCase] = field(default_factory=list)
    this_worked_before: list[ThisWorkedBeforeEntry] = field(default_factory=list)
    operator_guidance_from_memory: str = ""
    reviewable: bool = True
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "curated_pack_id": self.curated_pack_id,
            "label": self.label,
            "description": self.description,
            "base_playbook_id": self.base_playbook_id,
            "prior_successful_cases": [p.to_dict() for p in self.prior_successful_cases],
            "this_worked_before": [t.to_dict() for t in self.this_worked_before],
            "operator_guidance_from_memory": self.operator_guidance_from_memory,
            "reviewable": self.reviewable,
            "created_at_utc": self.created_at_utc,
        }


@dataclass
class MemoryGroundedAction:
    """Single action in a memory-grounded action pack; driven by prior successful cases."""
    action_id: str = ""
    label: str = ""
    command_hint: str = ""
    what_worked_summary: str = ""
    prior_case_unit_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reviewable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "label": self.label,
            "command_hint": self.command_hint,
            "what_worked_summary": self.what_worked_summary,
            "prior_case_unit_ids": list(self.prior_case_unit_ids),
            "confidence": self.confidence,
            "reviewable": self.reviewable,
        }


@dataclass
class MemoryGroundedActionPack:
    """Action pack driven by prior successful cases; reviewable defaults for operator."""
    action_pack_id: str = ""
    label: str = ""
    description: str = ""
    vertical_id: str = ""
    project_id: str = ""
    actions: list[MemoryGroundedAction] = field(default_factory=list)
    prior_successful_cases: list[RetrievedPriorCase] = field(default_factory=list)
    reviewable: bool = True
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_pack_id": self.action_pack_id,
            "label": self.label,
            "description": self.description,
            "vertical_id": self.vertical_id,
            "project_id": self.project_id,
            "actions": [a.to_dict() for a in self.actions],
            "prior_successful_cases": [p.to_dict() for p in self.prior_successful_cases],
            "reviewable": self.reviewable,
            "created_at_utc": self.created_at_utc,
        }
