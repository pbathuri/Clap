"""M23W: Environment health — dependency checks, no installs."""

from __future__ import annotations

import pytest

from workflow_dataset.validation.env_health import (
    check_environment_health,
    format_health_report,
)


def test_check_environment_health_returns_dict(tmp_path):
    """check_environment_health returns dict with required_ok, optional_ok, incubator_present."""
    health = check_environment_health(tmp_path)
    assert isinstance(health, dict)
    assert "required_ok" in health
    assert "optional_ok" in health
    assert "python_version" in health
    assert "required_deps" in health
    assert "optional_deps" in health
    assert "incubator_present" in health


def test_required_deps_include_pydantic(tmp_path):
    """Required deps list includes pydantic."""
    health = check_environment_health(tmp_path)
    names = [d.get("name") for d in health.get("required_deps", [])]
    assert "pydantic" in names


def test_incubator_present_after_stub(tmp_path):
    """incubator_present is True when incubator package is available (M23W stub)."""
    health = check_environment_health(tmp_path)
    assert health.get("incubator_present") is True


def test_format_health_report(tmp_path):
    """format_health_report returns non-empty string."""
    health = check_environment_health(tmp_path)
    report = format_health_report(health)
    assert isinstance(report, str)
    assert "Environment health" in report or "health" in report.lower()
    assert "Python" in report
