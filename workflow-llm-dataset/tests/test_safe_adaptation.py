"""
M38I–M38L: Tests for safe adaptation and boundary manager — candidate creation,
boundary check, quarantine, accept/reject/apply, supported vs experimental enforcement.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.safe_adaptation.models import (
    AdaptationCandidate,
    AdaptationEvidenceBundle,
    CohortBoundaryCheck,
    QuarantineState,
    ReviewDecision,
    ADAPTATION_STATUS_PENDING,
    ADAPTATION_STATUS_ACCEPTED,
    ADAPTATION_STATUS_QUARANTINED,
)
from workflow_dataset.safe_adaptation.store import (
    save_candidate,
    load_candidate,
    list_candidates,
    update_review_status,
    append_quarantine,
    list_quarantined,
    append_decision,
    list_recent_decisions,
)
from workflow_dataset.safe_adaptation.boundary import (
    evaluate_boundary_check,
    classify_adaptation,
    affects_supported_surface,
    safe_for_cohort,
    must_quarantine,
    changes_trust_posture,
)
from workflow_dataset.safe_adaptation.review import (
    inspect_candidate,
    accept_candidate,
    reject_candidate,
    quarantine_candidate,
    apply_within_boundaries,
)
from workflow_dataset.safe_adaptation.candidates import create_candidate


def test_adaptation_candidate_creation(tmp_path):
    """Create and persist a candidate; load and list."""
    c = create_candidate(
        cohort_id="careful_first_user",
        affected_surface_ids=["workspace_home", "queue_summary"],
        target_type="output_style",
        target_id="prefer_bullets",
        after_value="bullets",
        before_value="paragraphs",
        risk_level="low",
        summary="Prefer bullet output on workspace_home",
        repo_root=tmp_path,
    )
    assert c.adaptation_id.startswith("adapt_")
    assert c.cohort_id == "careful_first_user"
    assert c.review_status == ADAPTATION_STATUS_PENDING
    loaded = load_candidate(c.adaptation_id, repo_root=tmp_path)
    assert loaded is not None
    assert loaded.target_type == "output_style"
    candidates = list_candidates(repo_root=tmp_path, cohort_id="careful_first_user")
    assert len(candidates) >= 1
    assert any(x.adaptation_id == c.adaptation_id for x in candidates)


def test_boundary_check_supported_surface(tmp_path):
    """Boundary check for candidate affecting supported surface (careful_first_user has workspace_home supported)."""
    c = create_candidate(
        cohort_id="careful_first_user",
        affected_surface_ids=["workspace_home"],
        target_type="preference",
        target_id="ui.density",
        after_value="compact",
        risk_level="low",
        repo_root=tmp_path,
    )
    check = evaluate_boundary_check(c, "careful_first_user")
    assert check.affects_supported_surface is True
    assert check.cohort_id == "careful_first_user"
    assert "supported" in str(check.reasons).lower() or len(check.reasons) >= 1


def test_boundary_check_experimental_only(tmp_path):
    """Candidate affecting only experimental surface is experimental_only."""
    c = create_candidate(
        cohort_id="careful_first_user",
        affected_surface_ids=["mission_control"],  # experimental for careful_first_user
        target_type="preference",
        target_id="panel_order",
        after_value=["queue", "timeline"],
        risk_level="low",
        repo_root=tmp_path,
    )
    check = evaluate_boundary_check(c, "careful_first_user")
    assert check.experimental_only is True or check.affects_experimental_surface is True


def test_quarantine_behavior(tmp_path):
    """Quarantine candidate and list quarantined."""
    c = create_candidate(
        cohort_id="careful_first_user",
        affected_surface_ids=["workspace_home"],
        target_type="preference",
        target_id="x",
        after_value="y",
        risk_level="low",
        repo_root=tmp_path,
    )
    out = quarantine_candidate(c.adaptation_id, reason="low_evidence", notes="Single session", repo_root=tmp_path)
    assert out.get("ok") is True
    assert out.get("review_status") == ADAPTATION_STATUS_QUARANTINED
    loaded = load_candidate(c.adaptation_id, repo_root=tmp_path)
    assert loaded.review_status == ADAPTATION_STATUS_QUARANTINED
    qlist = list_quarantined(repo_root=tmp_path, limit=10)
    assert any(q.candidate_id == c.adaptation_id for q in qlist)


def test_accept_reject_flow(tmp_path):
    """Accept candidate that is safe (enough evidence); reject another."""
    c = create_candidate(
        cohort_id="careful_first_user",
        affected_surface_ids=["workspace_home"],
        target_type="output_style",
        target_id="format",
        after_value="bullets",
        risk_level="low",
        evidence_ids=["ev_1", "ev_2"],  # enough evidence so safe_for_cohort passes
        repo_root=tmp_path,
    )
    acc = accept_candidate(c.adaptation_id, rationale="Approved for pilot", repo_root=tmp_path)
    assert acc.get("ok") is True
    loaded = load_candidate(c.adaptation_id, repo_root=tmp_path)
    assert loaded.review_status == ADAPTATION_STATUS_ACCEPTED

    c2 = create_candidate(
        cohort_id="careful_first_user",
        affected_surface_ids=["queue_summary"],
        target_type="preference",
        target_id="other",
        after_value="z",
        repo_root=tmp_path,
    )
    rej = reject_candidate(c2.adaptation_id, rationale="Out of scope", repo_root=tmp_path)
    assert rej.get("ok") is True
    loaded2 = load_candidate(c2.adaptation_id, repo_root=tmp_path)
    assert loaded2.review_status == "rejected"


def test_apply_within_boundaries(tmp_path):
    """Apply only accepted candidate; rejected/pending cannot be applied."""
    c = create_candidate(
        cohort_id="careful_first_user",
        affected_surface_ids=["workspace_home"],
        target_type="output_style",
        target_id="format",
        after_value="bullets",
        risk_level="low",
        evidence_ids=["ev_1", "ev_2"],
        repo_root=tmp_path,
    )
    apply_before = apply_within_boundaries(c.adaptation_id, repo_root=tmp_path)
    assert apply_before.get("ok") is False
    assert "not_accepted" in str(apply_before.get("error", ""))

    accept_candidate(c.adaptation_id, rationale="OK", repo_root=tmp_path)
    apply_after = apply_within_boundaries(c.adaptation_id, behavior_delta_summary="Applied bullets", repo_root=tmp_path)
    assert apply_after.get("ok") is True
    assert "allowed_surfaces" in apply_after or "behavior_delta_summary" in apply_after


def test_inspect_candidate(tmp_path):
    """Inspect returns candidate, boundary_check, safe_for_cohort."""
    c = create_candidate(
        cohort_id="careful_first_user",
        affected_surface_ids=["workspace_home"],
        target_type="preference",
        target_id="k",
        after_value="v",
        repo_root=tmp_path,
    )
    out = inspect_candidate(c.adaptation_id, repo_root=tmp_path)
    assert "error" not in out or out.get("error") != "candidate_not_found"
    assert "candidate" in out
    assert "boundary_check" in out
    assert "safe_for_cohort" in out


def test_low_evidence_quarantine(tmp_path):
    """Candidate with low evidence on supported surface should must_quarantine (or safe_for_cohort False)."""
    ev = AdaptationEvidenceBundle(evidence_ids=["ev_1"], evidence_count=1)
    c = AdaptationCandidate(
        adaptation_id="adapt_manual_test",
        cohort_id="careful_first_user",
        affected_surface_ids=["workspace_home"],
        surface_type="supported",
        target_type="preference",
        target_id="x",
        after_value="y",
        evidence=ev,
        risk_level="low",
        review_status=ADAPTATION_STATUS_PENDING,
        created_at_utc="2025-01-01T00:00:00Z",
        updated_at_utc="2025-01-01T00:00:00Z",
        summary="Low evidence",
    )
    save_candidate(c, repo_root=tmp_path)
    check = evaluate_boundary_check(c, "careful_first_user")
    # Low evidence + supported surface -> must_quarantine or not safe_for_cohort
    assert check.must_quarantine is True or check.safe_for_cohort is False


def test_supported_vs_experimental_enforcement(tmp_path):
    """classify_adaptation returns SupportedSurfaceAdaptation or ExperimentalSurfaceAdaptation or BlockedAdaptation."""
    c_supp = create_candidate(
        cohort_id="careful_first_user",
        affected_surface_ids=["workspace_home"],
        target_type="preference",
        target_id="a",
        after_value="b",
        repo_root=tmp_path,
    )
    cl = classify_adaptation(c_supp, "careful_first_user")
    assert cl is not None
    assert hasattr(cl, "candidate_id")
    assert cl.candidate_id == c_supp.adaptation_id
