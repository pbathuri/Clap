"""M30E–M30H: Tests for reliability harness, golden paths, classification, recovery playbooks, report."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.reliability.models import GoldenPathScenario, ReliabilityRunResult, RecoveryCase
from workflow_dataset.reliability.golden_paths import list_path_ids, get_path, BUILTIN_GOLDEN_PATHS
from workflow_dataset.reliability.harness import (
    classify_run_result,
    run_golden_path,
    OUTCOMES,
)
from workflow_dataset.reliability.store import save_run, load_latest_run, list_runs, get_reliability_dir, get_runs_dir
from workflow_dataset.reliability.report import format_reliability_report
from workflow_dataset.reliability.recovery_playbooks import (
    RECOVERY_CASES,
    list_recovery_cases,
    get_recovery_case,
    suggest_recovery,
    get_recovery_guide,
)


def test_golden_path_definitions() -> None:
    ids = list_path_ids()
    assert "golden_first_run" in ids
    assert "project_plan_approve_simulate" in ids
    assert "pack_install_behavior_query" in ids
    assert "recovery_blocked_upgrade" in ids
    assert "review_inbox_approve_progress" in ids
    assert len(ids) >= 5


def test_get_path() -> None:
    p = get_path("golden_first_run")
    assert p is not None
    assert p.path_id == "golden_first_run"
    assert "install_readiness" in p.step_ids
    assert get_path("nonexistent") is None


def test_classify_pass() -> None:
    path = get_path("golden_first_run")
    assert path is not None
    steps_results = [
        {"step_id": "install_readiness", "actual": {"passed": True}},
        {"step_id": "bootstrap_profile", "actual": {"profile_exists": True}},
        {"step_id": "onboard_approvals", "actual": {}},
        {"step_id": "select_pack", "actual": {"requested_kit_found": True}},
        {"step_id": "run_first_simulate", "actual": {"runnable": True}},
        {"step_id": "inspect_trust", "actual": {}},
        {"step_id": "inspect_inbox", "actual": {}},
    ]
    outcome, fail_idx, subsystem, reasons = classify_run_result(path, steps_results)
    assert outcome == "pass"
    assert fail_idx is None
    assert subsystem is None
    assert "All steps met" in " ".join(reasons)


def test_classify_blocked_install() -> None:
    path = get_path("golden_first_run")
    assert path is not None
    steps_results = [
        {"step_id": "install_readiness", "actual": {"passed": False}},
        {"step_id": "bootstrap_profile", "actual": {}},
    ]
    outcome, fail_idx, subsystem, reasons = classify_run_result(path, steps_results)
    assert outcome == "blocked"
    assert fail_idx == 0
    assert "install" in (subsystem or "").lower() or any("install" in r.lower() for r in reasons)


def test_classify_fail_error_in_step() -> None:
    path = get_path("pack_install_behavior_query")
    assert path is not None
    steps_results = [
        {"step_id": "install_readiness", "actual": {"passed": True}},
        {"step_id": "pack_registry_ready", "actual": {"error": "Registry not found"}},
    ]
    outcome, fail_idx, subsystem, reasons = classify_run_result(path, steps_results)
    assert outcome == "fail"
    assert fail_idx == 1
    assert "error" in " ".join(reasons).lower() or "Registry" in " ".join(reasons)


def test_run_golden_path_unknown_id() -> None:
    result = run_golden_path("nonexistent_path_id", save=False)
    assert result["outcome"] == "fail"
    assert "not found" in " ".join(result.get("reasons", [])).lower()


def test_run_golden_path_returns_structure(tmp_path: Path) -> None:
    result = run_golden_path("golden_first_run", repo_root=tmp_path, save=False)
    assert result["path_id"] == "golden_first_run"
    assert result["outcome"] in OUTCOMES
    assert "steps_results" in result
    assert "reasons" in result
    assert "failure_step_index" in result
    assert "subsystem" in result


def test_store_save_load_list(tmp_path: Path) -> None:
    run_result = {
        "run_id": "rel_test_001",
        "path_id": "golden_first_run",
        "path_name": "Clean install → onboard",
        "outcome": "pass",
        "failure_step_index": None,
        "failure_step_id": None,
        "subsystem": None,
        "reasons": ["All steps met."],
        "steps_results": [{"step_id": "install_readiness", "actual": {"passed": True}}],
        "timestamp": "2025-01-01T00:00:00",
    }
    saved = save_run(run_result, repo_root=tmp_path)
    assert saved.exists()
    latest = load_latest_run(tmp_path)
    assert latest is not None
    assert latest["run_id"] == "rel_test_001"
    assert latest["outcome"] == "pass"
    runs = list_runs(tmp_path, limit=5)
    assert len(runs) >= 1
    assert runs[0]["path_id"] == "golden_first_run"


def test_format_reliability_report() -> None:
    run_result = {
        "run_id": "rel_1",
        "path_id": "golden_first_run",
        "path_name": "First run",
        "outcome": "blocked",
        "subsystem": "install",
        "reasons": ["Install check did not pass."],
        "timestamp": "2025-01-01T00:00:00",
    }
    text = format_reliability_report(run_result)
    assert "golden_first_run" in text
    assert "blocked" in text
    assert "Install" in text
    assert format_reliability_report(None) == "No reliability run found."


def test_recovery_cases() -> None:
    cases = list_recovery_cases()
    assert "broken_pack_state" in cases
    assert "failed_upgrade" in cases
    assert "missing_runtime_capability" in cases
    assert "blocked_approval_policy" in cases
    assert "stuck_project_session_agent" in cases
    assert "invalid_workspace_state" in cases


def test_get_recovery_case() -> None:
    c = get_recovery_case("broken_pack_state")
    assert c is not None
    assert c.case_id == "broken_pack_state"
    assert "pack" in c.name.lower()
    assert len(c.steps_guide) >= 1
    assert get_recovery_case("nonexistent") is None


def test_suggest_recovery_by_case() -> None:
    result = suggest_recovery(case_id="failed_upgrade")
    assert "error" not in result
    assert result.get("case_id") == "failed_upgrade"
    assert "when_to_use" in result
    assert "steps_guide" in result


def test_suggest_recovery_by_subsystem() -> None:
    result = suggest_recovery(subsystem="packs")
    assert "error" not in result
    assert result.get("case_id") in list_recovery_cases()
    assert "steps_guide" in result


def test_suggest_recovery_nonexistent_case() -> None:
    result = suggest_recovery(case_id="nonexistent_case")
    assert result.get("error") is not None


def test_get_recovery_guide() -> None:
    text = get_recovery_guide("broken_pack_state")
    assert "broken_pack_state" in text
    assert "When to use" in text
    assert "Steps" in text
    assert "workflow-dataset" in text
    guide_missing = get_recovery_guide("nonexistent")
    assert "not found" in guide_missing.lower() or "nonexistent" in guide_missing


# ----- M30H.1 Degraded mode profiles + fallback matrix -----
from workflow_dataset.reliability.models import DegradedModeProfile, FallbackRule
from workflow_dataset.reliability.degraded_profiles import (
    list_profile_ids,
    get_profile as get_degraded_profile,
    resolve_profile_for_subsystem,
    resolve_profile_for_unavailable_subsystems,
    profile_to_dict,
)
from workflow_dataset.reliability.fallback_matrix import (
    list_subsystems_with_fallback,
    get_fallback_rules,
    build_fallback_matrix_output,
    format_fallback_matrix_text,
)
from workflow_dataset.reliability.report import format_degraded_profile


def test_degraded_profile_definitions() -> None:
    ids = list_profile_ids()
    assert "install_blocked" in ids
    assert "packs_unavailable" in ids
    assert "approval_blocked" in ids
    assert "workspace_degraded" in ids
    assert "full_degraded" in ids


def test_get_degraded_profile() -> None:
    p = get_degraded_profile("packs_unavailable")
    assert p is not None
    assert p.profile_id == "packs_unavailable"
    assert "packs" in p.disabled_subsystems
    assert "still_works" in profile_to_dict(p)
    assert p.operator_explanation
    assert get_degraded_profile("nonexistent") is None


def test_resolve_profile_for_subsystem() -> None:
    p = resolve_profile_for_subsystem("install")
    assert p is not None
    assert "install" in p.disabled_subsystems
    p2 = resolve_profile_for_subsystem("packs")
    assert p2 is not None
    assert "packs" in p2.disabled_subsystems


def test_resolve_profile_for_unavailable_subsystems() -> None:
    p = resolve_profile_for_unavailable_subsystems(["workspace"])
    assert p is not None
    assert p.profile_id == "workspace_degraded"
    p2 = resolve_profile_for_unavailable_subsystems(["unknown_sub"])
    assert p2 is not None
    assert p2.profile_id == "full_degraded"


def test_format_degraded_profile() -> None:
    p = get_degraded_profile("approval_blocked")
    assert p is not None
    text = format_degraded_profile(profile_to_dict(p))
    assert "approval_blocked" in text
    assert "Still works" in text
    assert "Disabled flows" in text
    assert "Operator explanation" in text


def test_fallback_matrix_subsystems() -> None:
    subs = list_subsystems_with_fallback()
    assert "install" in subs
    assert "packs" in subs
    assert "trust" in subs
    assert "workspace" in subs


def test_get_fallback_rules() -> None:
    rules = get_fallback_rules("packs")
    assert len(rules) >= 1
    assert rules[0].when_subsystem_unavailable == "packs"
    assert rules[0].disable_flows
    assert rules[0].fallback_capability
    assert rules[0].operator_explanation
    assert get_fallback_rules("nonexistent") == []


def test_build_fallback_matrix_output() -> None:
    full = build_fallback_matrix_output(subsystem_filter=None)
    assert "matrix" in full
    assert "subsystems" in full
    assert "packs" in full["subsystems"]
    assert "packs" in full["matrix"]
    single = build_fallback_matrix_output(subsystem_filter="trust")
    assert single["subsystems"] == ["trust"]
    assert "trust" in single["matrix"]


def test_format_fallback_matrix_text() -> None:
    out = build_fallback_matrix_output(subsystem_filter="install")
    text = format_fallback_matrix_text(out)
    assert "install" in text
    assert "Unavailable" in text or "unavailable" in text
    assert "Disable" in text or "Fallback" in text
