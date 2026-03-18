"""
M23V/M23Q: Tests for trust cockpit, release gates, readiness report.
"""

from pathlib import Path

import pytest


def test_build_trust_cockpit_structure(tmp_path: Path) -> None:
    """build_trust_cockpit returns dict with expected keys."""
    from workflow_dataset.trust.cockpit import build_trust_cockpit
    cockpit = build_trust_cockpit(tmp_path)
    assert isinstance(cockpit, dict)
    assert "benchmark_trust" in cockpit
    assert "approval_readiness" in cockpit
    assert "job_macro_trust_state" in cockpit
    assert "unresolved_corrections" in cockpit
    assert "release_gate_status" in cockpit
    assert "errors" in cockpit
    assert "release_gate_checks" in cockpit
    assert "safe_to_expand" in cockpit
    assert "safe_to_expand_reasons" in cockpit


def test_format_trust_cockpit(tmp_path: Path) -> None:
    """format_trust_cockpit produces string with expected sections."""
    from workflow_dataset.trust.report import format_trust_cockpit
    report = format_trust_cockpit(repo_root=tmp_path)
    assert isinstance(report, str)
    assert "Trust" in report or "cockpit" in report.lower()
    assert "Benchmark" in report or "benchmark" in report.lower()
    assert "Approval" in report or "approval" in report.lower()
    assert "Operator-controlled" in report


def test_format_release_gates(tmp_path: Path) -> None:
    """format_release_gates produces string with release gate info."""
    from workflow_dataset.trust.report import format_release_gates
    report = format_release_gates(repo_root=tmp_path)
    assert isinstance(report, str)
    assert "Release gates" in report or "Release" in report
    assert "Unreviewed" in report or "Staged" in report
    assert "Safe to expand" in report or "safe to expand" in report.lower()


def test_evaluate_release_gates() -> None:
    """evaluate_release_gates returns list of gate checks."""
    from workflow_dataset.trust.release_gates import evaluate_release_gates
    cockpit = {
        "benchmark_trust": {"regressions": [], "latest_run_id": "r1", "latest_outcome": "pass"},
        "approval_readiness": {"registry_exists": False},
        "unresolved_corrections": {"proposed_updates_count": 0, "review_recommended_ids": []},
        "release_gate_status": {"release_readiness_report_exists": False},
    }
    checks = evaluate_release_gates(cockpit)
    assert len(checks) >= 4
    gate_ids = [c["gate_id"] for c in checks]
    assert "no_regressions" in gate_ids
    assert "approval_registry_ready" in gate_ids
    for c in checks:
        assert "name" in c and "passed" in c and "message" in c


def test_safe_to_expand_critical_gates() -> None:
    """safe_to_expand is False when critical gates fail."""
    from workflow_dataset.trust.release_gates import evaluate_release_gates, safe_to_expand
    cockpit = {
        "benchmark_trust": {"regressions": ["r2 vs r1"]},
        "approval_readiness": {"registry_exists": False},
        "unresolved_corrections": {},
        "release_gate_status": {},
    }
    cockpit["release_gate_checks"] = evaluate_release_gates(cockpit)
    result = safe_to_expand(cockpit)
    assert result["safe"] is False
    assert "no_regressions" in result["failed_gates"] or "approval_registry_ready" in result["failed_gates"]
    assert result["critical_failed"]


def test_safe_to_expand_all_pass() -> None:
    """safe_to_expand is True when no regressions and registry present."""
    from workflow_dataset.trust.release_gates import evaluate_release_gates, safe_to_expand
    cockpit = {
        "benchmark_trust": {"regressions": [], "latest_run_id": "r1"},
        "approval_readiness": {"registry_exists": True},
        "unresolved_corrections": {"proposed_updates_count": 0},
        "release_gate_status": {},
    }
    cockpit["release_gate_checks"] = evaluate_release_gates(cockpit)
    result = safe_to_expand(cockpit)
    assert result["safe"] is True
    assert not result["critical_failed"]


def test_trust_schema_from_cockpit_dict() -> None:
    """TrustCockpit.from_cockpit_dict builds from cockpit dict."""
    from workflow_dataset.trust.schema import TrustCockpit, GateCheck
    cockpit = {
        "benchmark_trust": {"latest_run_id": "r1", "regressions": []},
        "approval_readiness": {"registry_exists": True},
        "job_macro_trust_state": {"total_jobs": 5},
        "unresolved_corrections": {"proposed_updates_count": 0},
        "release_gate_status": {"staged_count": 0},
        "errors": [],
        "release_gate_checks": [{"gate_id": "g1", "name": "Test", "passed": True, "message": "ok"}],
        "safe_to_expand": True,
        "safe_to_expand_reasons": ["all good"],
    }
    tc = TrustCockpit.from_cockpit_dict(cockpit)
    assert tc.benchmark_trust.latest_run_id == "r1"
    assert tc.approval_readiness.registry_exists is True
    assert tc.safe_to_expand is True
    assert len(tc.release_gate_checks) == 1
    assert tc.release_gate_checks[0].name == "Test"


def test_format_readiness_report(tmp_path: Path) -> None:
    """format_readiness_report produces Safe to expand and gate checks."""
    from workflow_dataset.trust.report import format_readiness_report
    report = format_readiness_report(repo_root=tmp_path)
    assert isinstance(report, str)
    assert "Safe to expand" in report or "safe to expand" in report.lower()
    assert "Release gate checks" in report or "gate checks" in report.lower()
    assert "Advisory" in report
