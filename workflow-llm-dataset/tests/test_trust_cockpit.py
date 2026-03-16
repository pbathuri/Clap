"""
M23V: Tests for trust cockpit and release gates.
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
