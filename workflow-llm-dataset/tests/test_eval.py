"""
M21X: Tests for eval harness and benchmark board.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_eval_config_paths(tmp_path: Path) -> None:
    from workflow_dataset.eval.config import get_eval_root, get_cases_dir, get_runs_dir
    root = get_eval_root(tmp_path)
    assert root == tmp_path
    assert (get_cases_dir(tmp_path).name == "cases")
    assert (get_runs_dir(tmp_path).name == "runs")


def test_case_format_load_save(tmp_path: Path) -> None:
    from workflow_dataset.eval.case_format import add_case, load_case, list_cases, _find_case_by_id
    add_case(
        case_id="test_case",
        workflow="weekly_status",
        task_context="Test context.",
        root=tmp_path,
    )
    cases = list_cases(tmp_path)
    assert len(cases) == 1
    assert cases[0]["case_id"] == "test_case"
    assert cases[0]["workflow"] == "weekly_status"
    found = _find_case_by_id(tmp_path / "cases", "test_case")
    assert found and found["case_id"] == "test_case"


def test_seed_default_cases(tmp_path: Path) -> None:
    from workflow_dataset.eval.case_format import seed_default_cases, load_suite
    cases = seed_default_cases(tmp_path)
    assert len(cases) == 4
    suite = load_suite("ops_reporting_core", tmp_path)
    assert len(suite) == 4
    assert (tmp_path / "suites" / "ops_reporting_core.json").exists()


def test_seed_expanded_cases(tmp_path: Path) -> None:
    """E2: Expanded case library has 12 cases and suite ops_reporting_expanded."""
    from workflow_dataset.eval.case_format import seed_expanded_cases, load_suite
    cases = seed_expanded_cases(tmp_path)
    assert len(cases) == 12
    suite = load_suite("ops_reporting_expanded", tmp_path)
    assert len(suite) == 12
    workflows = {c["workflow"] for c in cases}
    assert "weekly_status" in workflows
    assert "status_action_bundle" in workflows
    assert "stakeholder_update_bundle" in workflows
    assert "ops_reporting_workspace" in workflows
    assert (tmp_path / "suites" / "ops_reporting_expanded.json").exists()


def test_score_artifact_heuristic() -> None:
    from workflow_dataset.eval.scoring import score_artifact_heuristic, SCORE_DIMENSIONS
    out = "**Summary** Done. **Wins** X. **Blockers** Blocked by Y. **Risks** Schedule risk. **Next steps** 1. Follow up."
    scores = score_artifact_heuristic(out, "weekly_status")
    assert "relevance" in scores
    assert scores["relevance"] >= 0
    assert scores["completeness"] >= 0
    assert "blocker_quality" in scores
    assert "risk_quality" in scores
    assert "next_step_specificity" in scores
    assert "honesty" in scores
    for d in SCORE_DIMENSIONS:
        assert d in scores


def test_thresholds_check_run_against_thresholds() -> None:
    """E2: check_run_against_thresholds returns passed and by_workflow with floors."""
    from workflow_dataset.eval.thresholds import (
        check_run_against_thresholds,
        get_thresholds,
        FLOOR_TO_DIMENSION,
    )
    # Cases with decent heuristic scores (e.g. relevance/completeness present)
    cases = [
        {
            "workflow": "weekly_status",
            "scores": {
                "artifacts": {
                    "weekly_status.md": {
                        "relevance": 0.7,
                        "completeness": 0.6,
                        "next_step_specificity": 0.5,
                        "stakeholder_readability": 0.5,
                    },
                },
            },
        },
    ]
    out = check_run_against_thresholds(cases)
    assert "passed" in out and "by_workflow" in out
    assert out["by_workflow"]["weekly_status"]["passed"] is True
    th = get_thresholds("weekly_status")
    assert "relevance_floor" in th and "specificity_floor" in th
    assert FLOOR_TO_DIMENSION["specificity_floor"] == "next_step_specificity"


def test_thresholds_fail_when_below_floor() -> None:
    """When scores are below floors, passed is False and floors_failed listed."""
    from workflow_dataset.eval.thresholds import check_run_against_thresholds
    cases = [
        {
            "workflow": "weekly_status",
            "scores": {
                "artifacts": {
                    "weekly_status.md": {
                        "relevance": 0.1,
                        "completeness": 0.1,
                        "next_step_specificity": 0.1,
                        "stakeholder_readability": 0.1,
                    },
                },
            },
        },
    ]
    out = check_run_against_thresholds(cases)
    assert out["passed"] is False
    assert len(out["by_workflow"]["weekly_status"]["floors_failed"]) >= 1


def test_board_list_runs_empty(tmp_path: Path) -> None:
    from workflow_dataset.eval.board import list_runs
    runs = list_runs(limit=5, root=tmp_path)
    assert runs == []


def test_compare_latest_vs_best_no_runs(tmp_path: Path) -> None:
    """E2: compare_latest_vs_best returns error when no runs."""
    from workflow_dataset.eval.board import compare_latest_vs_best
    out = compare_latest_vs_best(suite_name="x", limit_runs=5, root=tmp_path)
    assert out.get("error") == "No runs found"


def test_compare_latest_vs_best_single_run(tmp_path: Path) -> None:
    """E2: When only one run, comparison note is latest_is_best and recommendation from thresholds."""
    from workflow_dataset.eval.board import compare_latest_vs_best, get_run
    from workflow_dataset.eval.config import get_runs_dir
    from workflow_dataset.eval.scoring import score_run
    get_runs_dir(tmp_path)
    run_path = tmp_path / "runs" / "only"
    run_path.mkdir(parents=True)
    (run_path / "c1").mkdir()
    (run_path / "c1" / "weekly_status.md").write_text(
        "**Summary** Ok. **Wins** A. **Blockers** B. **Risks** Low. **Next steps** 1. X.",
        encoding="utf-8",
    )
    manifest = {
        "run_id": "only",
        "suite": "test",
        "timestamp": "2026-01-01T00:00:00Z",
        "cases": [
            {"case_id": "c1", "workflow": "weekly_status", "output_dir": str(run_path / "c1")},
        ],
        "run_path": str(run_path),
    }
    (run_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    score_run(run_path)
    out = compare_latest_vs_best(limit_runs=5, root=tmp_path)
    assert out.get("run_b") == "only"
    assert out.get("comparison_note") == "latest_is_best"
    assert out.get("recommendation") in ("promote", "hold")
    assert "thresholds_passed" in out


def test_compare_runs_missing() -> None:
    from workflow_dataset.eval.board import compare_runs
    out = compare_runs("nonexistent_a", "nonexistent_b")
    assert out.get("error")


def test_compare_runs_resolve_latest_previous(tmp_path: Path) -> None:
    """compare-runs with --run previous --run latest resolves aliases via list_runs (latest=first, previous=second)."""
    from workflow_dataset.eval.board import compare_runs, resolve_run_id
    from workflow_dataset.eval.config import get_runs_dir
    from workflow_dataset.eval.scoring import score_run
    get_runs_dir(tmp_path).mkdir(parents=True, exist_ok=True)
    for rid, ts in [("r_old", "2026-01-14T10:00:00Z"), ("r_new", "2026-01-15T10:00:00Z")]:
        run_path = tmp_path / "runs" / rid
        run_path.mkdir(parents=True)
        (run_path / "c1").mkdir()
        (run_path / "c1" / "weekly_status.md").write_text("**Summary** Ok. **Blockers** X.", encoding="utf-8")
        manifest = {"run_id": rid, "suite": "test", "timestamp": ts, "cases": [{"case_id": "c1", "workflow": "weekly_status", "output_dir": str(run_path / "c1")}], "run_path": str(run_path)}
        (run_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        score_run(run_path)
    latest = resolve_run_id("latest", tmp_path)
    previous = resolve_run_id("previous", tmp_path)
    assert latest == "r_new"
    assert previous == "r_old"
    out = compare_runs(previous, latest, root=tmp_path)
    assert out["run_a"] == "r_old" and out["run_b"] == "r_new"
    assert "recommendation" in out


def test_compare_runs_two_fake_runs(tmp_path: Path) -> None:
    from workflow_dataset.eval.board import compare_runs
    from workflow_dataset.eval.config import get_eval_root
    get_eval_root(tmp_path)  # ensure eval root exists
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True)
    for rid in ("run1", "run2"):
        run_path = runs_dir / rid
        run_path.mkdir()
        manifest = {
            "run_id": rid,
            "suite": "test",
            "timestamp": "2025-01-01T00:00:00Z",
            "cases": [
                {"case_id": "c1", "workflow": "weekly_status", "output_dir": str(run_path / "c1")},
            ],
            "run_path": str(run_path),
        }
        (run_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (run_path / "c1").mkdir()
        (run_path / "c1" / "weekly_status.md").write_text("**Summary** Ok. **Wins** A. **Blockers** B.", encoding="utf-8")
    from workflow_dataset.eval.scoring import score_run
    score_run(runs_dir / "run1")
    score_run(runs_dir / "run2")
    out = compare_runs("run1", "run2", root=tmp_path)
    assert "run_a" in out and out["run_a"] == "run1"
    assert "run_b" in out and out["run_b"] == "run2"
    assert "recommendation" in out
    assert "thresholds_passed" in out
    assert "regressions" in out and "improvements" in out


def test_run_case_single_case(tmp_path: Path) -> None:
    """run_case runs one case and returns run_id, run_path, suite single."""
    from workflow_dataset.eval.case_format import add_case
    from workflow_dataset.eval.harness import run_case
    add_case(
        case_id="single_test_case",
        workflow="weekly_status",
        task_context="Single case test.",
        root=tmp_path,
    )
    # Run without real LLM may fail on missing config/base_model or import; we only check error or success shape
    result = run_case("single_test_case", root=tmp_path)
    if result.get("error"):
        assert isinstance(result["error"], str) and len(result["error"]) > 0
    else:
        assert result.get("run_id")
        assert result.get("run_path")
        assert result.get("suite") == "single"


def test_board_write_report(tmp_path: Path) -> None:
    from workflow_dataset.eval.board import write_board_report
    report = {
        "suite": "ops_reporting_core",
        "latest_run_id": "abc123",
        "latest_timestamp": "2025-03-15T12:00:00Z",
        "best_run_id": "abc123",
        "recommendation": "hold",
        "comparison_with_previous": {"regressions": [], "improvements": []},
        "workflows_tested": ["weekly_status"],
    }
    p_json = tmp_path / "board.json"
    write_board_report(report, p_json, format="json")
    assert p_json.exists()
    loaded = json.loads(p_json.read_text(encoding="utf-8"))
    assert loaded["recommendation"] == "hold"
    p_md = tmp_path / "board.md"
    write_board_report(report, p_md, format="md")
    assert p_md.exists()
    assert "Benchmark board" in p_md.read_text(encoding="utf-8")


# ----- E3: Operator rating + reconciliation -----


def test_save_operator_rating_and_score_run_case(tmp_path: Path) -> None:
    """Operator rating is stored per case and included in score_run_case output."""
    from workflow_dataset.eval.config import get_eval_root, get_runs_dir
    from workflow_dataset.eval.scoring import save_operator_rating, score_run_case
    get_eval_root(tmp_path)
    runs_dir = get_runs_dir(tmp_path)
    run_path = runs_dir / "rate_run"
    run_path.mkdir(parents=True)
    case_dir = run_path / "c1"
    case_dir.mkdir()
    (case_dir / "weekly_status.md").write_text("**Summary** Ok. **Blockers** X.", encoding="utf-8")
    save_operator_rating("rate_run", "c1", {"overall": 4, "notes": "good"}, root=tmp_path)
    assert (case_dir / "operator_rating.json").exists()
    case_spec = {"case_id": "c1", "workflow": "weekly_status"}
    out = score_run_case(case_dir, case_spec)
    assert "artifacts" in out and "operator_rating" in out
    assert any(k.endswith(".md") for k in out["artifacts"])
    assert out.get("operator_rating") == {"overall": 4, "notes": "good"}


def test_get_run_scores_breakdown_heuristic_only(tmp_path: Path) -> None:
    """Breakdown has heuristic_score; operator_score and model_judge_score None when absent."""
    from workflow_dataset.eval.reconciliation import get_run_scores_breakdown
    manifest = {
        "run_id": "r1",
        "cases": [
            {
                "case_id": "c1",
                "scores": {
                    "artifacts": {"weekly_status.md": {"relevance": 0.8, "completeness": 0.6}},
                    "operator_rating": None,
                },
            },
        ],
    }
    out = get_run_scores_breakdown(manifest)
    assert out["heuristic_score"] > 0
    assert out["operator_score"] is None
    assert out["model_judge_score"] is None
    assert len(out["per_case"]) == 1
    assert out["per_case"][0]["case_id"] == "c1"
    assert out["per_case"][0]["operator_score"] is None


def test_get_run_scores_breakdown_with_operator(tmp_path: Path) -> None:
    """Breakdown includes operator_score when operator_rating present (overall 1-5 -> 0-1)."""
    from workflow_dataset.eval.reconciliation import get_run_scores_breakdown
    manifest = {
        "run_id": "r1",
        "cases": [
            {
                "case_id": "c1",
                "scores": {
                    "artifacts": {"weekly_status.md": {"relevance": 0.7}},
                    "operator_rating": {"overall": 5, "notes": "ship"},
                },
            },
        ],
    }
    out = get_run_scores_breakdown(manifest)
    assert out["operator_score"] is not None
    assert out["operator_score"] == 1.0  # 5 -> 1.0
    assert out["per_case"][0]["operator_score"] == 1.0


def test_reconcile_run_single_verdict_and_reasons() -> None:
    """Reconcile returns verdict (promote|hold|refine|revert), reasons, and separated scores."""
    from workflow_dataset.eval.reconciliation import reconcile_run
    manifest = {
        "run_id": "rec1",
        "cases": [
            {
                "case_id": "c1",
                "scores": {
                    "artifacts": {"w.md": {d: 0.8 for d in ("relevance", "completeness", "blocker_quality")}},
                    "operator_rating": {"overall": 4},
                },
            },
        ],
    }
    out = reconcile_run(manifest, comparison=None)
    assert out["run_id"] == "rec1"
    assert out["verdict"] in ("promote", "hold", "refine", "revert")
    assert "reasons" in out and len(out["reasons"]) >= 1
    assert "heuristic_score" in out and "operator_score" in out
    assert "Verdict:" in out["reasons"][-1] or "verdict" in out["reasons"][-1].lower()


def test_reconcile_run_with_comparison() -> None:
    """Reconcile with comparison uses regressions/improvements and can nudge verdict."""
    from workflow_dataset.eval.reconciliation import reconcile_run
    manifest = {
        "run_id": "rec2",
        "cases": [
            {
                "case_id": "c1",
                "scores": {
                    "artifacts": {"w.md": {d: 0.7 for d in ("relevance", "completeness")}},
                    "operator_rating": None,
                },
            },
        ],
    }
    comparison = {"regressions": ["blocker_quality"], "improvements": ["relevance"], "recommendation": "refine"}
    out = reconcile_run(manifest, comparison=comparison)
    assert out["verdict"] == "refine"
    assert "Regressions" in " ".join(out["reasons"]) or "regressions" in " ".join(out["reasons"]).lower()


# ----- E4: Benchmark trend view -----


def test_trend_report_no_runs(tmp_path: Path) -> None:
    """Trend report with no runs returns no_runs and empty lists."""
    from workflow_dataset.eval.trend import trend_report
    out = trend_report(limit_runs=5, root=tmp_path)
    assert out["trend_over_runs"] == "no_runs"
    assert out["recent_run_ids"] == []
    assert out["best_workflows"] == []
    assert out["worst_workflows"] == []
    assert out["top_regression_risk"] is None
    assert out["top_improvement_opportunity"] is None


def test_trend_report_single_run(tmp_path: Path) -> None:
    """Trend with one run: stable, best/worst workflows from that run."""
    from workflow_dataset.eval.config import get_eval_root, get_runs_dir
    from workflow_dataset.eval.scoring import score_run
    from workflow_dataset.eval.trend import trend_report
    get_eval_root(tmp_path)
    runs_dir = get_runs_dir(tmp_path)
    run_path = runs_dir / "trend_run"
    run_path.mkdir(parents=True)
    (run_path / "c1").mkdir()
    (run_path / "c1" / "weekly_status.md").write_text("**Summary** Ok. **Blockers** Y.", encoding="utf-8")
    manifest = {
        "run_id": "trend_run",
        "suite": "test",
        "timestamp": "2026-01-15T12:00:00Z",
        "cases": [
            {"case_id": "c1", "workflow": "weekly_status", "output_dir": str(run_path / "c1")},
        ],
        "run_path": str(run_path),
    }
    (run_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    score_run(run_path)
    out = trend_report(limit_runs=5, root=tmp_path)
    assert out["trend_over_runs"] == "stable"
    assert out["recent_run_ids"] == ["trend_run"]
    assert len(out["run_scores"]) == 1
    assert out["run_scores"][0]["run_id"] == "trend_run"
    assert "best_workflows" in out and "worst_workflows" in out
    assert out["top_regression_risk"] is None
    assert out["top_improvement_opportunity"] is None


def test_trend_report_two_runs_regression_and_improvement(tmp_path: Path) -> None:
    """Two runs with different scores yield trend and top regression/improvement from comparison."""
    from workflow_dataset.eval.config import get_eval_root, get_runs_dir
    from workflow_dataset.eval.scoring import score_run
    from workflow_dataset.eval.trend import trend_report
    get_eval_root(tmp_path)
    runs_dir = get_runs_dir(tmp_path)
    for rid, ts, content in [
        ("run_old", "2026-01-14T10:00:00Z", "**Summary** Old. **Blockers** X. **Risks** Schedule risk."),
        ("run_new", "2026-01-15T10:00:00Z", "**Summary** New. **Wins** Y. **Blockers** Blocked by Z. **Next steps** 1. Follow up."),
    ]:
        run_path = runs_dir / rid
        run_path.mkdir(parents=True)
        (run_path / "c1").mkdir()
        (run_path / "c1" / "weekly_status.md").write_text(content, encoding="utf-8")
        manifest = {
            "run_id": rid,
            "suite": "test",
            "timestamp": ts,
            "cases": [{"case_id": "c1", "workflow": "weekly_status", "output_dir": str(run_path / "c1")}],
            "run_path": str(run_path),
        }
        (run_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        score_run(run_path)
    out = trend_report(limit_runs=5, root=tmp_path)
    assert out["trend_over_runs"] in ("improving", "stable", "declining")
    assert len(out["recent_run_ids"]) == 2
    assert len(out["run_scores"]) == 2
    assert "best_workflows" in out and "worst_workflows" in out
    # May or may not have top_regression_risk / top_improvement_opportunity depending on deltas
    assert "top_regression_risk" in out
    assert "top_improvement_opportunity" in out


def test_trend_aggregate_by_workflow(tmp_path: Path) -> None:
    """Best/worst workflows are per-workflow means from latest run."""
    from workflow_dataset.eval.trend import _aggregate_by_workflow
    cases = [
        {"workflow": "weekly_status", "scores": {"artifacts": {"a.md": {"relevance": 0.8, "completeness": 0.6}}}},
        {"workflow": "weekly_status", "scores": {"artifacts": {"b.md": {"relevance": 0.9, "completeness": 0.7}}}},
        {"workflow": "stakeholder_update_bundle", "scores": {"artifacts": {"c.md": {"relevance": 0.3, "completeness": 0.2}}}},
    ]
    by_wf = _aggregate_by_workflow(cases)
    assert "weekly_status" in by_wf and "stakeholder_update_bundle" in by_wf
    assert by_wf["weekly_status"] > by_wf["stakeholder_update_bundle"]


def test_write_trend_report(tmp_path: Path) -> None:
    """write_trend_report writes JSON and MD."""
    from workflow_dataset.eval.trend import write_trend_report
    report = {
        "suite": "test",
        "trend_over_runs": "stable",
        "recent_run_ids": ["r1"],
        "run_scores": [{"run_id": "r1", "timestamp": "2026-01-01T00:00:00Z", "mean_score": 0.5}],
        "best_workflows": [{"workflow": "weekly_status", "mean_score": 0.6, "run_id": "r1"}],
        "worst_workflows": [{"workflow": "other", "mean_score": 0.3, "run_id": "r1"}],
        "top_regression_risk": {"type": "dimension", "name": "blocker_quality", "delta": -0.1, "run_a": "r0", "run_b": "r1"},
        "top_improvement_opportunity": {"type": "dimension", "name": "relevance", "delta": 0.15, "run_a": "r0", "run_b": "r1"},
        "comparison": None,
        "latest_run_id": "r1",
        "latest_timestamp": "2026-01-01T00:00:00Z",
    }
    p_json = tmp_path / "trend.json"
    write_trend_report(report, p_json, format="json")
    assert p_json.exists()
    data = json.loads(p_json.read_text(encoding="utf-8"))
    assert data["trend_over_runs"] == "stable"
    assert "best_workflows" in data
    p_md = tmp_path / "trend.md"
    write_trend_report(report, p_md, format="md")
    assert p_md.exists()
    text = p_md.read_text(encoding="utf-8")
    assert "Benchmark trend" in text and "Top regression risk" in text and "Top improvement opportunity" in text


def test_board_report_includes_reconciliation(tmp_path: Path) -> None:
    """Board report includes reconciliation for latest run when runs exist."""
    from workflow_dataset.eval.board import board_report, get_run
    from workflow_dataset.eval.config import get_eval_root, get_runs_dir
    from workflow_dataset.eval.scoring import score_run
    get_eval_root(tmp_path)
    runs_dir = get_runs_dir(tmp_path)
    run_path = runs_dir / "br_run"
    run_path.mkdir(parents=True)
    (run_path / "c1").mkdir()
    (run_path / "c1" / "weekly_status.md").write_text("**Summary** Done. **Blockers** Y.", encoding="utf-8")
    manifest = {
        "run_id": "br_run",
        "suite": "test",
        "timestamp": "2026-01-01T00:00:00Z",
        "cases": [
            {"case_id": "c1", "workflow": "weekly_status", "output_dir": str(run_path / "c1")},
        ],
        "run_path": str(run_path),
    }
    (run_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    score_run(run_path)
    report = board_report(limit_runs=5, root=tmp_path)
    assert report.get("latest_run_id") == "br_run"
    assert "reconciliation" in report
    assert "thresholds_passed" in report
    recon = report["reconciliation"]
    assert recon is not None
    assert recon.get("verdict") in ("promote", "hold", "refine", "revert")
    assert "heuristic_score" in recon and "reasons" in recon


def test_eval_reconcile_cli(tmp_path: Path) -> None:
    """CLI: workflow-dataset eval reconcile <run_id> prints verdict and reasons; API contract always asserted."""
    from workflow_dataset.eval.board import get_run
    from workflow_dataset.eval.config import get_eval_root, get_runs_dir
    from workflow_dataset.eval.scoring import score_run
    from workflow_dataset.eval.reconciliation import reconcile_run
    get_eval_root(tmp_path)
    runs_dir = get_runs_dir(tmp_path)
    run_path = runs_dir / "cli_rec"
    run_path.mkdir(parents=True)
    (run_path / "c1").mkdir()
    (run_path / "c1" / "weekly_status.md").write_text("**Summary** Ok. **Blockers** Z.", encoding="utf-8")
    manifest = {
        "run_id": "cli_rec",
        "suite": "test",
        "timestamp": "2026-01-01T00:00:00Z",
        "cases": [
            {"case_id": "c1", "workflow": "weekly_status", "output_dir": str(run_path / "c1")},
        ],
        "run_path": str(run_path),
    }
    (run_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    score_run(run_path)
    # API contract: reconcile_run returns verdict and separated scores
    manifest = get_run("cli_rec", tmp_path)
    assert manifest is not None
    recon = reconcile_run(manifest, comparison=None)
    assert recon["verdict"] in ("promote", "hold", "refine", "revert")
    assert "heuristic_score" in recon
    assert "reasons" in recon and len(recon["reasons"]) >= 1
    # CLI invocation when app is importable
    try:
        from typer.testing import CliRunner
        from workflow_dataset.cli import app
        runner = CliRunner()
        result = runner.invoke(app, ["eval", "reconcile", "cli_rec", "--eval-root", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert "Verdict:" in result.output or "verdict" in result.output.lower()
        assert "heuristic_score" in result.output or "Heuristic" in result.output
    except ImportError:
        pass  # full CLI deps (e.g. yaml) not installed; API test above suffices
