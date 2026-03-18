"""
M23V: Tests for package/install readiness summary and report.
"""

from pathlib import Path

import pytest


def test_build_readiness_summary_structure(tmp_path: Path) -> None:
    """build_readiness_summary returns dict with expected keys."""
    from workflow_dataset.package_readiness.summary import build_readiness_summary
    summary = build_readiness_summary(tmp_path)
    assert isinstance(summary, dict)
    assert "current_machine_readiness" in summary
    assert "product_readiness" in summary
    assert "missing_runtime_prerequisites" in summary
    assert "ready_for_first_real_user_install" in summary
    assert "experimental" in summary
    assert "errors" in summary


def test_format_readiness_report(tmp_path: Path) -> None:
    """format_readiness_report produces string with expected sections."""
    from workflow_dataset.package_readiness.report import format_readiness_report
    report = format_readiness_report(repo_root=tmp_path)
    assert isinstance(report, str)
    assert "readiness" in report.lower()
    assert "machine" in report.lower() or "Machine" in report
    assert "First real-user install" in report or "first" in report.lower()
    assert "experimental" in report.lower() or "Experimental" in report
