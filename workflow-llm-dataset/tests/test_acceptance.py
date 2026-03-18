"""M24C: Tests for acceptance harness — scenario definitions, runner, classification, report, storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.acceptance.scenarios import (
    list_scenarios,
    get_scenario,
    AcceptanceScenario,
)
from workflow_dataset.acceptance.runner import run_scenario, classify_outcome
from workflow_dataset.acceptance.report import format_acceptance_report
from workflow_dataset.acceptance.storage import save_run, load_latest_run, list_runs
from workflow_dataset.acceptance.journeys import run_journey_steps


def test_scenario_definitions() -> None:
    ids = list_scenarios()
    assert "founder_first_run" in ids
    assert "analyst_first_run" in ids
    assert "developer_first_run" in ids
    assert "document_worker_first_run" in ids


def test_get_scenario() -> None:
    s = get_scenario("founder_first_run")
    assert s is not None
    assert s.scenario_id == "founder_first_run"
    assert s.starter_kit_id == "founder_ops_starter"
    assert "install_readiness" in s.first_value_steps
    assert get_scenario("nonexistent") is None


def test_classify_outcome_fail_unknown_scenario() -> None:
    outcome, reasons = classify_outcome("nonexistent", [])
    assert outcome == "fail"
    assert "not found" in reasons[0].lower()


def test_classify_outcome_blocked_when_install_fails() -> None:
    steps_results = [
        {"step_id": "install_readiness", "actual": {"passed": False, "missing_prereqs": ["config missing"]}},
        {"step_id": "bootstrap_profile", "actual": {"profile_exists": False}},
        {"step_id": "select_pack", "actual": {"requested_kit_found": True}},
        {"step_id": "run_first_simulate", "actual": {"runnable": True}},
    ]
    outcome, reasons = classify_outcome("founder_first_run", steps_results)
    assert outcome == "blocked"
    assert any("install" in r.lower() or "prereq" in r.lower() for r in reasons)


def test_classify_outcome_partial_when_profile_missing() -> None:
    steps_results = [
        {"step_id": "install_readiness", "actual": {"passed": True}},
        {"step_id": "bootstrap_profile", "actual": {"profile_exists": False}},
        {"step_id": "onboard_approvals", "actual": {}},
        {"step_id": "select_pack", "actual": {"requested_kit_found": True, "missing_prerequisites": []}},
        {"step_id": "run_first_simulate", "actual": {"runnable": True}},
        {"step_id": "inspect_trust", "actual": {}},
        {"step_id": "inspect_inbox", "actual": {}},
    ]
    outcome, reasons = classify_outcome("founder_first_run", steps_results)
    assert outcome == "partial"
    assert any("profile" in r.lower() or "bootstrap" in r.lower() for r in reasons)


def test_run_scenario_returns_structure(tmp_path: Path) -> None:
    result = run_scenario("founder_first_run", repo_root=tmp_path, report_only=True)
    assert result["scenario_id"] == "founder_first_run"
    assert result["outcome"] in ("pass", "partial", "blocked", "fail")
    assert "steps_results" in result
    assert "reasons" in result
    assert "ready_for_trial" in result
    assert isinstance(result["ready_for_trial"], bool)


def test_format_acceptance_report() -> None:
    run_result = {
        "scenario_id": "founder_first_run",
        "scenario_name": "Founder first run",
        "outcome": "partial",
        "reasons": ["Bootstrap profile not yet created."],
        "steps_results": [{"step_id": "install_readiness", "actual": {"passed": True}}],
        "ready_for_trial": False,
    }
    report = format_acceptance_report(run_result)
    assert "Acceptance report" in report
    assert "founder" in report.lower()
    assert "partial" in report
    assert "Ready for real-user trial" in report
    assert "No" in report


def test_save_and_load_run(tmp_path: Path) -> None:
    run_result = {
        "scenario_id": "founder_first_run",
        "outcome": "partial",
        "reasons": [],
        "steps_results": [],
        "ready_for_trial": False,
    }
    path = save_run(run_result, repo_root=tmp_path)
    assert path.exists()
    loaded = load_latest_run(tmp_path)
    assert loaded is not None
    assert loaded.get("scenario_id") == "founder_first_run"
    assert loaded.get("outcome") == "partial"


def test_list_runs(tmp_path: Path) -> None:
    save_run({"scenario_id": "analyst_first_run", "outcome": "pass", "reasons": [], "steps_results": [], "ready_for_trial": True}, repo_root=tmp_path)
    runs = list_runs(tmp_path, limit=5)
    assert len(runs) >= 1
    assert any(r.get("scenario_id") == "analyst_first_run" for r in runs)


def test_journey_steps_run(tmp_path: Path) -> None:
    results = run_journey_steps("founder_first_run", tmp_path, step_ids=["install_readiness", "bootstrap_profile"])
    assert len(results) == 2
    assert results[0]["step_id"] == "install_readiness"
    assert "actual" in results[0]
    assert results[1]["step_id"] == "bootstrap_profile"
