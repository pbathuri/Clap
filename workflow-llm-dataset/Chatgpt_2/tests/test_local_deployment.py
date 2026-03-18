"""
M23R: Tests for packaged local deployment — profile, install-check, first-run.
"""

from pathlib import Path

import pytest


def test_get_deployment_dir(tmp_path: Path) -> None:
    """get_deployment_dir returns path under repo."""
    from workflow_dataset.local_deployment import get_deployment_dir
    d = get_deployment_dir(tmp_path)
    assert d == tmp_path / "data/local/deployment"


def test_build_local_deployment_profile_structure(tmp_path: Path) -> None:
    """build_local_deployment_profile returns dict with expected keys."""
    from workflow_dataset.local_deployment import build_local_deployment_profile
    profile = build_local_deployment_profile(tmp_path)
    assert isinstance(profile, dict)
    assert "version" in profile
    assert "generated_at" in profile
    assert "repo_root" in profile
    assert "edge_profile" in profile
    assert "readiness" in profile
    assert "trust_summary" in profile
    assert "product_surfaces" in profile
    assert "errors" in profile


def test_write_deployment_profile(tmp_path: Path) -> None:
    """write_deployment_profile creates dir and JSON file."""
    from workflow_dataset.local_deployment import build_local_deployment_profile, write_deployment_profile, get_deployment_dir
    profile = build_local_deployment_profile(tmp_path)
    path = write_deployment_profile(tmp_path, profile=profile, write_report_md=True)
    assert path.exists()
    assert path.suffix == ".json"
    assert path.parent == get_deployment_dir(tmp_path)
    data = __import__("json").loads(path.read_text(encoding="utf-8"))
    assert data.get("repo_root") == str(tmp_path)
    report_path = path.parent / "local_deployment_report.md"
    assert report_path.exists()
    assert "Local deployment" in report_path.read_text(encoding="utf-8")


def test_run_install_check_structure(tmp_path: Path) -> None:
    """run_install_check returns passed, checks, missing_prereqs."""
    from workflow_dataset.local_deployment import run_install_check
    result = run_install_check(tmp_path)
    assert "passed" in result
    assert "checks" in result
    assert "missing_prereqs" in result
    assert "summary" in result
    assert isinstance(result["checks"], list)


def test_format_install_check_report(tmp_path: Path) -> None:
    """format_install_check_report produces Install check and Checks sections."""
    from workflow_dataset.local_deployment.install_check import run_install_check, format_install_check_report
    result = run_install_check(tmp_path)
    report = format_install_check_report(result)
    assert "Install check" in report
    assert "Checks" in report
    assert "Validation only" in report or "No changes" in report


def test_run_first_run_structure(tmp_path: Path) -> None:
    """run_first_run returns install_check_passed, created_dirs, first_run_summary, report_text."""
    from workflow_dataset.local_deployment import run_first_run
    result = run_first_run(tmp_path, skip_onboarding=True)
    assert "install_check_passed" in result
    assert "created_dirs" in result
    assert "first_run_summary" in result
    assert "report_text" in result
    assert isinstance(result["report_text"], str)
    assert "First-run" in result["report_text"] or "first" in result["report_text"].lower()


def test_format_deployment_report(tmp_path: Path) -> None:
    """format_deployment_report produces markdown with Runtime, Readiness, Trust, Product surfaces."""
    from workflow_dataset.local_deployment.profile import build_local_deployment_profile, format_deployment_report
    profile = build_local_deployment_profile(tmp_path)
    report = format_deployment_report(profile)
    assert "Local deployment" in report
    assert "Runtime" in report
    assert "Readiness" in report
    assert "Trust" in report
    assert "Product surfaces" in report
