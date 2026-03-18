"""
M42I–M42L: Benchmark board and promotion/rollback pipeline — local-first comparison and disciplined promotion.
M42L.1: Promotion tracks, shadow-mode evaluation, production-vs-candidate comparison.
"""

from __future__ import annotations

from workflow_dataset.benchmark_board.models import (
    BenchmarkBoard,
    BenchmarkSlice,
    BaselineModel,
    CandidateModel,
    Scorecard,
    ComparisonDimension,
    BenchmarkDisagreementNote,
    PromotionRecommendation,
    RollbackRecommendation,
    PromotionTrack,
    DEFAULT_COMPARISON_DIMENSIONS,
)
from workflow_dataset.benchmark_board.slices import get_slice, list_slice_ids, BUILTIN_SLICES
from workflow_dataset.benchmark_board.tracks import get_track, list_track_ids, scope_to_track_id, BUILTIN_PROMOTION_TRACKS
from workflow_dataset.benchmark_board.compare import run_baseline_vs_candidate
from workflow_dataset.benchmark_board.scorecard import build_scorecard
from workflow_dataset.benchmark_board.store import (
    save_scorecard,
    load_scorecard,
    list_scorecards,
    get_quarantined,
    get_latest_promoted,
    list_promotion_history,
    list_rollback_history,
    append_shadow_run,
    list_shadow_runs,
)
from workflow_dataset.benchmark_board.pipeline import (
    reject_candidate,
    quarantine_candidate,
    promote_experimental,
    promote_limited_cohort,
    promote_production_safe,
    rollback_to_prior,
)
from workflow_dataset.benchmark_board.report import build_benchmark_board_report, build_production_vs_candidate_comparison
from workflow_dataset.benchmark_board.shadow import build_shadow_report, record_shadow_run

__all__ = [
    "BenchmarkBoard",
    "BenchmarkSlice",
    "BaselineModel",
    "CandidateModel",
    "Scorecard",
    "ComparisonDimension",
    "BenchmarkDisagreementNote",
    "PromotionRecommendation",
    "RollbackRecommendation",
    "DEFAULT_COMPARISON_DIMENSIONS",
    "get_slice",
    "list_slice_ids",
    "BUILTIN_SLICES",
    "run_baseline_vs_candidate",
    "build_scorecard",
    "save_scorecard",
    "load_scorecard",
    "list_scorecards",
    "get_quarantined",
    "get_latest_promoted",
    "list_promotion_history",
    "list_rollback_history",
    "reject_candidate",
    "quarantine_candidate",
    "promote_experimental",
    "promote_limited_cohort",
    "promote_production_safe",
    "rollback_to_prior",
    "build_benchmark_board_report",
    "PromotionTrack",
    "get_track",
    "list_track_ids",
    "scope_to_track_id",
    "BUILTIN_PROMOTION_TRACKS",
    "append_shadow_run",
    "list_shadow_runs",
    "build_shadow_report",
    "record_shadow_run",
    "build_production_vs_candidate_comparison",
]
