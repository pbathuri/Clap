"""
M30L.1: Launch profiles and rollout gates — gate evaluation, profile allowed, report structure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.release_readiness.models import LaunchProfile, RolloutGate
from workflow_dataset.release_readiness.gates import (
    GATES,
    GATE_ENV_REQUIRED_OK,
    GATE_ACCEPTANCE_PASS,
    GATE_FIRST_USER_READY,
    GATE_RELEASE_READINESS_NOT_BLOCKED,
    GATE_ROLLOUT_STAGE_READY,
    GATE_TRUST_APPROVAL_READY,
    evaluate_gate,
    list_gates,
    get_gate,
)
from workflow_dataset.release_readiness.profiles import (
    PROFILES,
    PROFILE_DEMO,
    PROFILE_INTERNAL_PILOT,
    PROFILE_CAREFUL_FIRST_USER,
    PROFILE_BROADER_CONTROLLED_PILOT,
    evaluate_all_gates,
    is_profile_allowed,
    build_launch_profiles_report,
    build_rollout_gate_report,
    format_launch_profiles_report,
    format_rollout_gate_report,
    list_profiles,
    get_profile,
)


def test_rollout_gate_to_dict():
    g = RolloutGate(gate_id="x", label="X", description="X gate")
    d = g.to_dict()
    assert d["gate_id"] == "x"
    assert d["label"] == "X"
    assert d["description"] == "X gate"


def test_launch_profile_to_dict():
    p = LaunchProfile(profile_id="demo", label="Demo", required_gate_ids=["g1", "g2"])
    d = p.to_dict()
    assert d["profile_id"] == "demo"
    assert d["required_gate_ids"] == ["g1", "g2"]


def test_gates_registry_has_expected_ids():
    expected = {
        GATE_ENV_REQUIRED_OK,
        GATE_ACCEPTANCE_PASS,
        GATE_FIRST_USER_READY,
        GATE_RELEASE_READINESS_NOT_BLOCKED,
        GATE_ROLLOUT_STAGE_READY,
        GATE_TRUST_APPROVAL_READY,
    }
    assert set(GATES.keys()) == expected


def test_profiles_registry_has_four_profiles():
    assert set(PROFILES.keys()) == {
        PROFILE_DEMO,
        PROFILE_INTERNAL_PILOT,
        PROFILE_CAREFUL_FIRST_USER,
        PROFILE_BROADER_CONTROLLED_PILOT,
    }


def test_demo_profile_requires_two_gates():
    p = PROFILES[PROFILE_DEMO]
    assert GATE_ROLLOUT_STAGE_READY in p.required_gate_ids
    assert GATE_ACCEPTANCE_PASS in p.required_gate_ids
    assert len(p.required_gate_ids) == 2


def test_evaluate_gate_returns_passed_and_detail(tmp_path: Path):
    r = evaluate_gate(GATE_RELEASE_READINESS_NOT_BLOCKED, tmp_path)
    assert "passed" in r
    assert "detail" in r
    assert isinstance(r["passed"], bool)


def test_evaluate_all_gates_returns_dict_per_gate(tmp_path: Path):
    results = evaluate_all_gates(tmp_path)
    assert set(results.keys()) == set(GATES.keys())
    for gid, r in results.items():
        assert "passed" in r and "detail" in r


def test_is_profile_allowed_unknown_profile():
    allowed, passed, failed = is_profile_allowed("unknown_profile", gate_results={})
    assert allowed is False
    assert "unknown profile" in failed[0]


def test_is_profile_allowed_with_mock_gate_results():
    # All required gates pass -> allowed
    gate_results = {
        GATE_ROLLOUT_STAGE_READY: {"passed": True, "detail": "ok"},
        GATE_ACCEPTANCE_PASS: {"passed": True, "detail": "ok"},
    }
    allowed, passed, failed = is_profile_allowed(PROFILE_DEMO, gate_results=gate_results)
    assert allowed is True
    assert set(passed) == {GATE_ROLLOUT_STAGE_READY, GATE_ACCEPTANCE_PASS}
    assert failed == []


def test_is_profile_allowed_fails_when_gate_fails():
    gate_results = {
        GATE_ROLLOUT_STAGE_READY: {"passed": False, "detail": "not ready"},
        GATE_ACCEPTANCE_PASS: {"passed": True, "detail": "ok"},
    }
    allowed, passed, failed = is_profile_allowed(PROFILE_DEMO, gate_results=gate_results)
    assert allowed is False
    assert GATE_ROLLOUT_STAGE_READY in failed
    assert GATE_ACCEPTANCE_PASS in passed


def test_build_launch_profiles_report_structure(tmp_path: Path):
    report = build_launch_profiles_report(tmp_path)
    assert "gate_results" in report
    assert "profiles" in report
    assert len(report["profiles"]) == 4
    for p in report["profiles"]:
        assert "profile_id" in p
        assert "allowed" in p
        assert "gates_passed" in p
        assert "gates_failed" in p
        assert "required_gate_ids" in p


def test_build_rollout_gate_report_structure(tmp_path: Path):
    report = build_rollout_gate_report(tmp_path)
    assert "gates" in report
    assert "profiles_summary" in report
    for pid, p in PROFILES.items():
        summary = next((s for s in report["profiles_summary"] if s["profile_id"] == pid), None)
        assert summary is not None
        assert "allowed" in summary


def test_build_rollout_gate_report_with_profile(tmp_path: Path):
    report = build_rollout_gate_report(tmp_path, profile_id=PROFILE_DEMO)
    assert "gates" in report
    assert "profile" in report
    pr = report["profile"]
    assert pr["profile_id"] == PROFILE_DEMO
    assert "allowed" in pr
    assert "gate_details" in pr
    assert set(pr["gate_details"].keys()) == set(PROFILES[PROFILE_DEMO].required_gate_ids)


def test_format_launch_profiles_report_contains_allowed(tmp_path: Path):
    report = build_launch_profiles_report(tmp_path)
    text = format_launch_profiles_report(report)
    assert "Launch profiles" in text
    assert PROFILE_DEMO in text
    assert "allowed" in text or "not allowed" in text


def test_format_rollout_gate_report_contains_gates(tmp_path: Path):
    report = build_rollout_gate_report(tmp_path)
    text = format_rollout_gate_report(report)
    assert "Rollout gates" in text
    assert GATE_ENV_REQUIRED_OK in text or "env_required_ok" in text


def test_list_gates_returns_dicts():
    gates = list_gates()
    assert len(gates) == len(GATES)
    for g in gates:
        assert "gate_id" in g
        assert "label" in g


def test_list_profiles_returns_dicts():
    profiles = list_profiles()
    assert len(profiles) == 4
    for p in profiles:
        assert "profile_id" in p
        assert "required_gate_ids" in p


def test_get_gate_get_profile():
    assert get_gate("nonexistent_gate") is None
    assert get_gate(GATE_ACCEPTANCE_PASS) is not None
    assert get_profile("nonexistent") is None
    assert get_profile(PROFILE_DEMO) is not None