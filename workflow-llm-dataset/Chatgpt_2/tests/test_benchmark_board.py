"""
M42I–M42L: Tests for benchmark board — models, slices, scorecard, pipeline, report.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.benchmark_board.models import (
    Scorecard,
    BenchmarkSlice,
    ComparisonDimension,
    PromotionRecommendation,
    RollbackRecommendation,
    DEFAULT_COMPARISON_DIMENSIONS,
)
from workflow_dataset.benchmark_board.slices import get_slice, list_slice_ids, BUILTIN_SLICES
from workflow_dataset.benchmark_board.scorecard import build_scorecard
from workflow_dataset.benchmark_board.store import (
    save_scorecard,
    load_scorecard,
    list_scorecards,
    get_quarantined,
    get_latest_promoted,
)
from workflow_dataset.benchmark_board.pipeline import (
    reject_candidate,
    quarantine_candidate,
    promote_experimental,
    rollback_to_prior,
)
from workflow_dataset.benchmark_board.report import build_benchmark_board_report


def test_benchmark_slices() -> None:
    ids = list_slice_ids()
    assert "ops_reporting" in ids
    assert "golden_path" in ids
    s = get_slice("ops_reporting")
    assert s is not None
    assert s.eval_suite == "ops_reporting"
    assert get_slice("nonexistent") is None


def test_build_scorecard_from_comparison() -> None:
    comp = {
        "baseline_id": "run_a",
        "candidate_id": "run_b",
        "recommendation": "promote",
        "thresholds_passed": True,
        "regressions": [],
        "improvements": ["overall_score"],
        "run_a_score": 0.4,
        "run_b_score": 0.7,
        "at_iso": "2025-01-01T12:00:00Z",
    }
    sc = build_scorecard(comp)
    assert sc.baseline_id == "run_a"
    assert sc.candidate_id == "run_b"
    assert sc.recommendation == "promote"
    assert sc.thresholds_passed is True
    assert sc.promotion_recommendation is not None
    assert sc.promotion_recommendation.recommend is True
    assert len(sc.dimensions) == len(DEFAULT_COMPARISON_DIMENSIONS)


def test_scorecard_revert_has_rollback_recommendation() -> None:
    comp = {
        "baseline_id": "base",
        "candidate_id": "cand",
        "recommendation": "revert",
        "thresholds_passed": False,
        "regressions": ["overall_score"],
        "improvements": [],
        "run_a_score": 0.8,
        "run_b_score": 0.3,
        "at_iso": "2025-01-01T12:00:00Z",
    }
    sc = build_scorecard(comp)
    assert sc.rollback_recommendation is not None
    assert sc.rollback_recommendation.recommend is True
    assert sc.rollback_recommendation.prior_id == "base"


def test_store_scorecard_and_list() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sc = build_scorecard({
            "baseline_id": "b1", "candidate_id": "c1", "recommendation": "hold",
            "thresholds_passed": False, "regressions": [], "improvements": [],
            "at_iso": "2025-01-01T12:00:00Z",
        })
        save_scorecard(sc.to_dict(), repo_root=root)
        loaded = load_scorecard(sc.scorecard_id, repo_root=root)
        assert loaded is not None
        assert loaded["candidate_id"] == "c1"
        listed = list_scorecards(limit=5, repo_root=root)
        assert len(listed) >= 1


def test_pipeline_reject_quarantine_promote_rollback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = reject_candidate("cand_1", reason="test reject", repo_root=root)
        assert out["decision"] == "reject"
        out = quarantine_candidate("cand_2", reason="test quarantine", repo_root=root)
        assert out["decision"] == "quarantine"
        q = get_quarantined(repo_root=root)
        assert "cand_2" in q
        out = promote_experimental("cand_3", reason="test promote", repo_root=root)
        assert out["scope"] == "experimental_only"
        latest_id, latest_scope = get_latest_promoted(repo_root=root)
        assert latest_id == "cand_3"
        out = rollback_to_prior("cand_3", "cand_0", reason="test rollback", repo_root=root)
        assert out["prior_id"] == "cand_0"


def test_report_no_data() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        r = build_benchmark_board_report(repo_root=root)
        assert "top_candidate_awaiting_decision" in r
        assert "latest_promoted_id" in r
        assert "quarantined_count" in r
        assert "next_benchmark_review_action" in r


# --- M42L.1 Promotion tracks + shadow-mode ---


def test_promotion_tracks() -> None:
    from workflow_dataset.benchmark_board import list_track_ids, get_track, BUILTIN_PROMOTION_TRACKS
    ids = list_track_ids()
    assert "experimental_only" in ids
    assert "limited_cohort" in ids
    assert "production_candidate" in ids
    t = get_track("limited_cohort")
    assert t is not None
    assert t.required_previous_track_id == "experimental_only"
    assert get_track("nonexistent") is None


def test_shadow_report_empty() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.benchmark_board import build_shadow_report
        r = build_shadow_report("cand_1", repo_root=root)
        assert r["candidate_id"] == "cand_1"
        assert r["total_runs"] == 0
        assert "operator_summary" in r


def test_shadow_report_with_runs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.benchmark_board.store import append_shadow_run
        append_shadow_run("cand_1", "prod_1", "cand_1_run", slice_id="ops", production_score=0.5, candidate_score=0.7, outcome="candidate_better", at_iso="2025-01-01T12:00:00Z", repo_root=root)
        from workflow_dataset.benchmark_board import build_shadow_report
        r = build_shadow_report("cand_1", repo_root=root)
        assert r["total_runs"] == 1
        assert r["candidate_better_count"] == 1
        assert r["avg_production_score"] == 0.5
        assert r["avg_candidate_score"] == 0.7


def test_production_vs_candidate_comparison() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.benchmark_board import build_production_vs_candidate_comparison
        r = build_production_vs_candidate_comparison(repo_root=root)
        assert "current_production_route_id" in r
        assert "operator_summary_text" in r
        assert "scorecard_summary" in r
        assert "shadow_summary" in r
