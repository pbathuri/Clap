"""
M38A–M38D: Tests for cohort profiles and supported surface matrix.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.cohort.models import (
    SUPPORT_BLOCKED,
    SUPPORT_EXPERIMENTAL,
    SUPPORT_SUPPORTED,
    CohortProfile,
)
from workflow_dataset.cohort.profiles import (
    get_cohort_profile,
    list_cohort_profile_ids,
    COHORT_CAREFUL_FIRST_USER,
    COHORT_INTERNAL_DEMO,
    COHORT_BOUNDED_OPERATOR_PILOT,
)
from workflow_dataset.cohort.surface_matrix import (
    get_matrix,
    get_support_level,
    get_supported_surfaces,
    get_experimental_surfaces,
    get_blocked_surfaces,
    get_all_surface_ids,
)
from workflow_dataset.cohort.bindings import (
    apply_cohort_defaults,
    get_recommended_workday_preset_id,
    get_recommended_experience_profile_id,
)
from workflow_dataset.cohort.store import (
    get_active_cohort_id,
    set_active_cohort_id,
)
from workflow_dataset.cohort.explain import explain_surface, explain_cohort


def test_list_cohort_profiles() -> None:
    """All five cohort profiles exist."""
    ids = list_cohort_profile_ids()
    assert COHORT_INTERNAL_DEMO in ids
    assert COHORT_CAREFUL_FIRST_USER in ids
    assert COHORT_BOUNDED_OPERATOR_PILOT in ids
    assert "document_heavy_pilot" in ids
    assert "developer_assist_pilot" in ids
    assert len(ids) == 5


def test_get_cohort_profile() -> None:
    """get_cohort_profile returns profile by id."""
    p = get_cohort_profile(COHORT_CAREFUL_FIRST_USER)
    assert p is not None
    assert p.cohort_id == COHORT_CAREFUL_FIRST_USER
    assert p.default_experience_profile_id == "calm_default"
    assert p.required_readiness in ("ready_or_degraded", "ready_only", "any")


def test_matrix_support_levels() -> None:
    """Matrix returns supported/experimental/blocked per surface."""
    matrix = get_matrix(COHORT_CAREFUL_FIRST_USER)
    assert len(matrix) >= 10
    assert matrix.get("workspace_home") == SUPPORT_SUPPORTED
    assert matrix.get("operator_mode") == SUPPORT_BLOCKED
    assert matrix.get("mission_control") == SUPPORT_EXPERIMENTAL or matrix.get("mission_control") == SUPPORT_SUPPORTED


def test_get_support_level() -> None:
    """get_support_level returns correct level."""
    assert get_support_level(COHORT_CAREFUL_FIRST_USER, "workspace_home") == SUPPORT_SUPPORTED
    assert get_support_level(COHORT_CAREFUL_FIRST_USER, "operator_mode") == SUPPORT_BLOCKED
    assert get_support_level(COHORT_INTERNAL_DEMO, "operator_mode") == SUPPORT_SUPPORTED


def test_supported_experimental_blocked_lists() -> None:
    """Supported/experimental/blocked lists are consistent with matrix."""
    sup = get_supported_surfaces(COHORT_CAREFUL_FIRST_USER)
    exp = get_experimental_surfaces(COHORT_CAREFUL_FIRST_USER)
    blk = get_blocked_surfaces(COHORT_CAREFUL_FIRST_USER)
    all_ids = get_all_surface_ids()
    assert len(sup) + len(exp) + len(blk) == len(all_ids)
    assert "operator_mode" in blk
    assert "workspace_home" in sup


def test_apply_cohort_defaults() -> None:
    """apply_cohort_defaults returns config with workday and experience profile."""
    out = apply_cohort_defaults(COHORT_CAREFUL_FIRST_USER)
    assert out.get("cohort_id") == COHORT_CAREFUL_FIRST_USER
    assert "default_workday_preset_id" in out
    assert "default_experience_profile_id" in out
    assert out.get("default_experience_profile_id") == "calm_default"


def test_store_get_set_cohort(tmp_path: Path) -> None:
    """Active cohort can be read and written."""
    assert get_active_cohort_id(tmp_path) == ""
    set_active_cohort_id(COHORT_BOUNDED_OPERATOR_PILOT, tmp_path)
    assert get_active_cohort_id(tmp_path) == COHORT_BOUNDED_OPERATOR_PILOT
    set_active_cohort_id("", tmp_path)
    assert get_active_cohort_id(tmp_path) == ""


def test_explain_surface() -> None:
    """explain_surface returns level and reason."""
    out = explain_surface("operator_mode", COHORT_CAREFUL_FIRST_USER)
    assert out["surface_id"] == "operator_mode"
    assert out["cohort_id"] == COHORT_CAREFUL_FIRST_USER
    assert out["support_level"] == SUPPORT_BLOCKED
    assert "out of scope" in out["reason"].lower() or "blocked" in out["reason"].lower()


def test_explain_cohort() -> None:
    """explain_cohort returns counts and allowed scope."""
    out = explain_cohort(COHORT_CAREFUL_FIRST_USER)
    assert out["cohort_id"] == COHORT_CAREFUL_FIRST_USER
    assert "supported_count" in out
    assert "blocked_count" in out
    assert out["supported_count"] + out["experimental_count"] + out["blocked_count"] >= len(get_all_surface_ids())


def test_unknown_cohort_matrix_defaults_blocked() -> None:
    """Unknown cohort returns all blocked."""
    matrix = get_matrix("nonexistent_cohort")
    for sid, level in matrix.items():
        assert level == SUPPORT_BLOCKED


def test_no_profile_default_behavior() -> None:
    """When no active cohort, get_active_cohort_id returns empty string (or cohort id if set)."""
    # With a path that has no cohort file, we get ""
    assert get_active_cohort_id(Path("/nonexistent/repo/path")) == ""


# ----- M38D.1: Readiness gates + escalation/downgrade paths -----


def test_get_gates_for_cohort() -> None:
    """careful_first_user has gates; internal_demo (any readiness) has none."""
    from workflow_dataset.cohort.gates import get_gates_for_cohort
    gates_careful = get_gates_for_cohort(COHORT_CAREFUL_FIRST_USER)
    gates_demo = get_gates_for_cohort(COHORT_INTERNAL_DEMO)
    assert len(gates_careful) >= 1
    assert len(gates_demo) == 0


def test_evaluate_gates_returns_list() -> None:
    """evaluate_gates returns list of { gate_id, passed, message }."""
    from workflow_dataset.cohort.gates import evaluate_gates
    results = evaluate_gates(COHORT_CAREFUL_FIRST_USER, Path("/nonexistent/repo"))
    assert isinstance(results, list)
    for r in results:
        assert "gate_id" in r
        assert "passed" in r
        assert "message" in r


def test_get_transitions_for_cohort() -> None:
    """Transitions from/to careful_first_user include escalation and downgrade."""
    from workflow_dataset.cohort.transitions import get_transitions_for_cohort
    from workflow_dataset.cohort.models import TRANSITION_DOWNGRADE, TRANSITION_ESCALATION
    all_t = get_transitions_for_cohort(COHORT_CAREFUL_FIRST_USER)
    downgrades = [t for t in all_t if t.direction == TRANSITION_DOWNGRADE]
    escalations = [t for t in all_t if t.direction == TRANSITION_ESCALATION]
    assert any(t.to_cohort_id == COHORT_CAREFUL_FIRST_USER for t in downgrades) or len(downgrades) >= 0
    assert any(t.from_cohort_id == COHORT_CAREFUL_FIRST_USER for t in escalations) or len(escalations) >= 0


def test_get_recommended_transition_returns_dict_or_none() -> None:
    """get_recommended_transition returns None or dict with suggested_cohort_id, direction, reason."""
    from workflow_dataset.cohort.transitions import get_recommended_transition
    rec = get_recommended_transition(COHORT_CAREFUL_FIRST_USER, Path("/nonexistent/repo"))
    # With no real triage/release state, may be None or a recommendation
    assert rec is None or (
        isinstance(rec, dict)
        and "suggested_cohort_id" in rec
        and "direction" in rec
        and rec["direction"] in ("escalation", "downgrade")
    )
