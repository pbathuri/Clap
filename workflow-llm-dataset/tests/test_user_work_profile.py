"""M23U: Tests for user work profile — create, save, load, show."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.onboarding.user_work_profile import (
    UserWorkProfile,
    build_default_user_work_profile,
    load_user_work_profile,
    save_user_work_profile,
    bootstrap_user_work_profile,
    get_user_work_profile_path,
)


def test_build_default_profile(tmp_path: Path) -> None:
    profile = build_default_user_work_profile(tmp_path)
    assert isinstance(profile, UserWorkProfile)
    assert profile.field == ""
    assert profile.risk_safety_posture == "conservative"
    assert profile.preferred_automation_degree == "simulate_first"


def test_save_and_load_profile(tmp_path: Path) -> None:
    profile = UserWorkProfile(
        field="operations",
        job_family="office_admin",
        risk_safety_posture="moderate",
    )
    path = save_user_work_profile(profile, tmp_path)
    assert path.exists()
    loaded = load_user_work_profile(tmp_path)
    assert loaded is not None
    assert loaded.field == "operations"
    assert loaded.job_family == "office_admin"
    assert loaded.risk_safety_posture == "moderate"


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert load_user_work_profile(tmp_path) is None


def test_bootstrap_creates_or_updates(tmp_path: Path) -> None:
    p = bootstrap_user_work_profile(tmp_path, field="founder_ops", job_family="founder")
    assert p.field == "founder_ops"
    assert p.job_family == "founder"
    assert load_user_work_profile(tmp_path) is not None
    p2 = bootstrap_user_work_profile(tmp_path, field="operations")
    assert p2.field == "operations"


def test_get_user_work_profile_path(tmp_path: Path) -> None:
    path = get_user_work_profile_path(tmp_path)
    assert path.name == "user_work_profile.yaml"
    assert "onboarding" in str(path)
