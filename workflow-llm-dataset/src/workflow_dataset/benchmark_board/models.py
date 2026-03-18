"""
M42I–M42L: Benchmark board model — slices, baseline/candidate, scorecard, comparison dimensions,
disagreement, promotion/rollback recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Comparison dimensions (align with council perspectives where useful)
DIMENSION_TASK_SUCCESS = "task_success"
DIMENSION_SAFETY_TRUST = "safety_trust"
DIMENSION_SUPPORTABILITY = "supportability"
DIMENSION_RELIABILITY = "reliability"
DIMENSION_LATENCY_BURDEN = "latency_runtime_burden"
DIMENSION_OPERATOR_BURDEN = "operator_burden"
DIMENSION_COHORT_COMPATIBILITY = "cohort_compatibility"

DEFAULT_COMPARISON_DIMENSIONS = [
    DIMENSION_TASK_SUCCESS,
    DIMENSION_SAFETY_TRUST,
    DIMENSION_SUPPORTABILITY,
    DIMENSION_RELIABILITY,
    DIMENSION_LATENCY_BURDEN,
    DIMENSION_OPERATOR_BURDEN,
    DIMENSION_COHORT_COMPATIBILITY,
]


@dataclass
class BenchmarkSlice:
    """A local eval slice (suite or reliability path) used in comparisons."""
    slice_id: str
    name: str
    description: str = ""
    eval_suite: str = ""       # eval suite name
    reliability_path_id: str = ""  # or reliability path id
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "name": self.name,
            "description": self.description,
            "eval_suite": self.eval_suite,
            "reliability_path_id": self.reliability_path_id,
            "label": self.label or self.name,
        }


@dataclass
class BaselineModel:
    """Baseline model or run identifier for comparison."""
    baseline_id: str           # run_id or logical id e.g. prod_current
    label: str = ""
    run_id: str = ""          # resolved run_id if applicable

    def to_dict(self) -> dict[str, Any]:
        return {"baseline_id": self.baseline_id, "label": self.label, "run_id": self.run_id or self.baseline_id}


@dataclass
class CandidateModel:
    """Candidate model or run identifier for comparison."""
    candidate_id: str          # run_id or logical id e.g. cand_123
    label: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, "label": self.label, "run_id": self.run_id or self.candidate_id}


@dataclass
class ComparisonDimension:
    """One dimension in a scorecard (score 0–1, pass threshold, detail)."""
    dimension_id: str
    score: float = 0.0
    pass_threshold: bool = False
    detail: str = ""
    baseline_value: float | None = None
    candidate_value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension_id": self.dimension_id,
            "score": self.score,
            "pass_threshold": self.pass_threshold,
            "detail": self.detail,
            "baseline_value": self.baseline_value,
            "candidate_value": self.candidate_value,
        }


@dataclass
class BenchmarkDisagreementNote:
    """Note of disagreement or unstable outcome between dimensions or vs recommendation."""
    note_id: str
    description: str
    dimension_ids: list[str] = field(default_factory=list)
    severity: str = "medium"  # low | medium | high

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "description": self.description,
            "dimension_ids": list(self.dimension_ids),
            "severity": self.severity,
        }


@dataclass
class PromotionRecommendation:
    """Recommendation to promote (scope: experimental_only | limited_cohort | production_safe)."""
    recommend: bool
    scope: str = "experimental_only"  # experimental_only | limited_cohort | production_safe
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"recommend": self.recommend, "scope": self.scope, "reason": self.reason}


@dataclass
class RollbackRecommendation:
    """Recommendation to roll back to a prior model/run."""
    recommend: bool
    prior_id: str = ""         # run_id or baseline_id to roll back to
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"recommend": self.recommend, "prior_id": self.prior_id, "reason": self.reason}


@dataclass
class Scorecard:
    """Compact promotion-ready scorecard: baseline vs candidate, dimensions, recommendation. M43: optional memory_slice_ids."""
    scorecard_id: str
    baseline_id: str
    candidate_id: str
    slice_ids: list[str] = field(default_factory=list)
    memory_slice_ids: list[str] = field(default_factory=list)  # M43: memory-backed slice refs used in this comparison
    dimensions: list[ComparisonDimension] = field(default_factory=list)
    disagreement_notes: list[BenchmarkDisagreementNote] = field(default_factory=list)
    promotion_recommendation: PromotionRecommendation | None = None
    rollback_recommendation: RollbackRecommendation | None = None
    recommendation: str = ""    # promote | hold | refine | revert
    thresholds_passed: bool = False
    regressions: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    at_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scorecard_id": self.scorecard_id,
            "baseline_id": self.baseline_id,
            "candidate_id": self.candidate_id,
            "slice_ids": list(self.slice_ids),
            "memory_slice_ids": list(self.memory_slice_ids),
            "dimensions": [d.to_dict() for d in self.dimensions],
            "disagreement_notes": [n.to_dict() for n in self.disagreement_notes],
            "promotion_recommendation": self.promotion_recommendation.to_dict() if self.promotion_recommendation else None,
            "rollback_recommendation": self.rollback_recommendation.to_dict() if self.rollback_recommendation else None,
            "recommendation": self.recommendation,
            "thresholds_passed": self.thresholds_passed,
            "regressions": list(self.regressions),
            "improvements": list(self.improvements),
            "at_iso": self.at_iso,
        }


@dataclass
class BenchmarkBoard:
    """Logical benchmark board: id, label, slice ids (optional)."""
    board_id: str = "default"
    label: str = "Default benchmark board"
    slice_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"board_id": self.board_id, "label": self.label, "slice_ids": list(self.slice_ids)}


# --- M42L.1 Promotion tracks + shadow-mode ---


@dataclass
class PromotionTrack:
    """A promotion track: experimental-only, limited cohort, production-candidate, etc."""
    track_id: str = ""
    name: str = ""
    description: str = ""
    order_index: int = 0          # 0 = first (experimental), 1 = limited, 2 = production_candidate
    required_previous_track_id: str = ""  # must have passed this track before (e.g. limited requires experimental)
    gates_description: str = ""   # operator-facing: what is checked to advance to this track

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "name": self.name,
            "description": self.description,
            "order_index": self.order_index,
            "required_previous_track_id": self.required_previous_track_id,
            "gates_description": self.gates_description,
        }
