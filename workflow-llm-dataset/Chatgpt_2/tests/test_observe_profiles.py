"""
Tests for M31D.1 observation profiles and retention policies.
"""

from __future__ import annotations

import pytest

from workflow_dataset.observe.profiles import (
    ObservationProfile,
    RetentionPolicy,
    get_observation_profiles,
    get_profile,
    list_profile_ids,
    get_retention_policy_for_profile,
    format_retention_policy_output,
)


def test_list_profile_ids() -> None:
    ids = list_profile_ids()
    assert "minimal" in ids
    assert "standard" in ids
    assert "teaching-heavy" in ids
    assert "document-heavy" in ids
    assert "developer-focused" in ids
    assert len(ids) == 5


def test_get_observation_profiles() -> None:
    profiles = get_observation_profiles()
    for pid in list_profile_ids():
        assert pid in profiles
        p = profiles[pid]
        assert isinstance(p, ObservationProfile)
        assert p.profile_id == pid
        assert p.enabled_sources
        assert p.metadata_depth in ("observe_only", "rich_metadata")
        assert p.retention_global_default_days >= 0
        assert p.suitable_user_types or p.suitable_workflow_types


def test_minimal_profile() -> None:
    p = get_profile("minimal")
    assert p is not None
    assert p.enabled_sources == ["file"]
    assert p.retention_overrides_days.get("file") == 14
    assert "privacy-first" in " ".join(p.suitable_user_types).lower()


def test_standard_profile() -> None:
    p = get_profile("standard")
    assert p is not None
    assert "file" in p.enabled_sources
    assert "app" in p.enabled_sources
    assert "calendar" in p.enabled_sources
    assert p.metadata_depth == "observe_only"


def test_teaching_heavy_profile() -> None:
    p = get_profile("teaching-heavy")
    assert p is not None
    assert "teaching" in p.enabled_sources
    assert p.retention_overrides_days.get("teaching") == 365


def test_developer_focused_profile() -> None:
    p = get_profile("developer-focused")
    assert p is not None
    assert "terminal" in p.enabled_sources
    assert p.retention_overrides_days.get("terminal") == 14


def test_get_profile_unknown() -> None:
    assert get_profile("unknown-profile") is None


def test_get_retention_policy_for_profile() -> None:
    policy = get_retention_policy_for_profile("standard")
    assert policy is not None
    assert policy.profile_id == "standard"
    assert policy.global_default_days == 90
    assert "file" in policy.per_source_days
    assert policy.summary


def test_retention_policy_minimal() -> None:
    policy = get_retention_policy_for_profile("minimal")
    assert policy is not None
    assert policy.per_source_days.get("file") == 14


def test_retention_policy_teaching_heavy() -> None:
    policy = get_retention_policy_for_profile("teaching-heavy")
    assert policy is not None
    assert policy.per_source_days.get("teaching") == 365


def test_retention_policy_unknown() -> None:
    assert get_retention_policy_for_profile("nonexistent") is None


def test_format_retention_policy_output() -> None:
    policy = get_retention_policy_for_profile("standard")
    assert policy is not None
    out = format_retention_policy_output(policy)
    assert out["profile_id"] == "standard"
    assert "per_source_retention_days" in out
    assert "per_source_max_events_per_day" in out
    assert "summary" in out
