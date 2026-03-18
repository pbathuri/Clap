"""
M38E–M38H: Tests for cohort evidence and issue triage.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.triage.models import (
    CohortEvidenceItem,
    UserObservedIssue,
    EvidenceKind,
    TriageStatus,
    SupportabilityImpact,
)
from workflow_dataset.triage.store import (
    append_evidence,
    list_evidence,
    save_issue,
    load_issue,
    list_issues,
    update_triage_status,
)
from workflow_dataset.triage.evidence import create_evidence_from_session, create_evidence_from_readiness_blocker
from workflow_dataset.triage.classification import classify_severity, apply_classification
from workflow_dataset.triage.loop import (
    group_duplicates_or_related,
    create_issue_from_evidence,
    mark_resolved,
    mark_reproduced,
    surface_new_evidence,
)
from workflow_dataset.triage.health import build_cohort_health_summary


def test_evidence_item_creation(tmp_path):
    ev = CohortEvidenceItem(
        evidence_id="ev_test1",
        cohort_id="cohort_a",
        session_id="s1",
        kind=EvidenceKind.SESSION_FEEDBACK,
        summary="Blocking issue in session",
        created_at_utc="2025-01-01T00:00:00Z",
    )
    append_evidence(ev, repo_root=tmp_path)
    items = list_evidence(repo_root=tmp_path, cohort_id="cohort_a")
    assert len(items) == 1
    assert items[0].evidence_id == "ev_test1"


def test_create_evidence_from_session(tmp_path):
    create_evidence_from_session(
        session_id="s2",
        cohort_id="c1",
        blocking_issues=["timeout"],
        degraded_mode=True,
        repo_root=tmp_path,
    )
    items = list_evidence(repo_root=tmp_path, cohort_id="c1")
    assert len(items) >= 1
    assert items[0].kind in (EvidenceKind.SESSION_FEEDBACK, EvidenceKind.DEGRADED_MODE)


def test_issue_save_load(tmp_path):
    issue = UserObservedIssue(
        issue_id="issue_abc",
        cohort_id="c1",
        evidence_ids=["ev_1"],
        severity="high",
        triage_status=TriageStatus.NEW,
        summary="Test issue",
    )
    save_issue(issue, repo_root=tmp_path)
    loaded = load_issue("issue_abc", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.severity == "high"
    assert loaded.triage_status == TriageStatus.NEW


def test_issue_classification():
    issue = UserObservedIssue(issue_id="i1", cohort_id="c1", severity="medium")
    apply_classification(issue, severity="high", supported_surface=True, session_count_affected=2)
    assert issue.severity == "high"
    assert issue.supportability.supported_surface_involved is True
    assert issue.cohort_impact is not None


def test_classify_severity():
    assert classify_severity(1, "fail", False) == "critical"
    assert classify_severity(0, "pass", False) == "low"


def test_group_duplicates():
    issues = [
        UserObservedIssue(issue_id="a", cohort_id="c1", severity="high", summary="Same summary here"),
        UserObservedIssue(issue_id="b", cohort_id="c1", severity="high", summary="Same summary here"),
    ]
    groups = group_duplicates_or_related(issues)
    assert len(groups) >= 1
    for v in groups.values():
        assert len(v) >= 2


def test_triage_state_transitions(tmp_path):
    issue = UserObservedIssue(
        issue_id="issue_trans",
        cohort_id="c1",
        evidence_ids=[],
        triage_status=TriageStatus.NEW,
    )
    save_issue(issue, tmp_path)
    updated = update_triage_status("issue_trans", TriageStatus.REPRODUCED, repo_root=tmp_path)
    assert updated is not None
    assert updated.triage_status == TriageStatus.REPRODUCED
    resolved = mark_resolved("issue_trans", repo_root=tmp_path)
    assert resolved is not None
    assert resolved.triage_status == TriageStatus.RESOLVED
    assert resolved.resolved_at_utc != ""


def test_create_issue_from_evidence(tmp_path):
    create_evidence_from_session("s1", cohort_id="c1", repo_root=tmp_path)
    items = list_evidence(repo_root=tmp_path, cohort_id="c1", limit=1)
    if not items:
        pytest.skip("no evidence")
    ev_ids = [items[0].evidence_id]
    issue = create_issue_from_evidence(ev_ids, cohort_id="c1", summary="From evidence", repo_root=tmp_path)
    assert issue.issue_id.startswith("issue_")
    assert issue.evidence_ids == ev_ids
    loaded = load_issue(issue.issue_id, repo_root=tmp_path)
    assert loaded is not None


def test_cohort_health_no_issues(tmp_path):
    report = build_cohort_health_summary(repo_root=tmp_path)
    assert report["open_issue_count"] == 0
    assert "highest_severity" in report
    assert "recommended_mitigation" in report


def test_cohort_health_with_issue(tmp_path):
    issue = UserObservedIssue(
        issue_id="issue_health",
        cohort_id="c1",
        severity="high",
        triage_status=TriageStatus.NEW,
        summary="Open issue",
    )
    save_issue(issue, tmp_path)
    report = build_cohort_health_summary(repo_root=tmp_path)
    assert report["open_issue_count"] >= 1
    assert report["highest_severity"] in ("high", "critical", "medium", "low")


def test_surface_new_evidence(tmp_path):
    create_evidence_from_session("s1", cohort_id="c1", repo_root=tmp_path)
    surfaced = surface_new_evidence(repo_root=tmp_path, cohort_id="c1")
    assert isinstance(surfaced, list)


def test_mark_reproduced(tmp_path):
    issue = UserObservedIssue(issue_id="issue_rep", cohort_id="c1", triage_status=TriageStatus.NEW)
    save_issue(issue, tmp_path)
    out = mark_reproduced("issue_rep", steps_summary="Step 1, 2, 3", repo_root=tmp_path)
    assert out is not None
    assert out.reproducibility_note is not None
    assert out.reproducibility_note.reproducible is True


# ----- M38H.1 Issue clusters + mitigation playbooks -----
def test_build_clusters_by_subsystem(tmp_path):
    from workflow_dataset.triage.clusters import build_clusters_by_subsystem
    issue = UserObservedIssue(issue_id="i1", cohort_id="c1", affected_subsystems=["executor"], severity="high", triage_status=TriageStatus.NEW)
    save_issue(issue, tmp_path)
    clusters = build_clusters_by_subsystem(repo_root=tmp_path, cohort_id="")
    assert isinstance(clusters, list)
    if clusters:
        assert clusters[0].subsystem in ("executor", "_no_subsystem")
        assert clusters[0].playbook_id in ("executor_blocked", "general_support", "")


def test_build_clusters_by_cohort(tmp_path):
    from workflow_dataset.triage.clusters import build_clusters_by_cohort
    issue = UserObservedIssue(issue_id="i2", cohort_id="c1", triage_status=TriageStatus.NEW)
    save_issue(issue, tmp_path)
    clusters = build_clusters_by_cohort(repo_root=tmp_path, cohort_id="c1")
    assert isinstance(clusters, list)


def test_get_playbook_for_subsystem():
    from workflow_dataset.triage.playbooks import get_playbook_for_subsystem, get_playbook
    pb = get_playbook_for_subsystem("executor")
    assert pb is not None
    assert pb.playbook_id == "executor_blocked"
    assert pb.operator_do_now.guidance != ""
    assert "recovery" in pb.link_recovery.lower() or "recovery" in str(pb.operator_do_now.link_recovery).lower()


def test_get_playbook_for_issue():
    from workflow_dataset.triage.playbooks import get_playbook_for_issue
    issue = UserObservedIssue(issue_id="x", affected_subsystems=["trust"])
    pb = get_playbook_for_issue(issue)
    assert pb is not None
    assert pb.playbook_id in ("approval_policy", "general_support", "executor_blocked", "install_upgrade")


def test_health_includes_clusters_and_links(tmp_path):
    issue = UserObservedIssue(issue_id="ih", cohort_id="c1", affected_subsystems=["executor"], triage_status=TriageStatus.NEW)
    save_issue(issue, tmp_path)
    report = build_cohort_health_summary(repo_root=tmp_path)
    assert "clusters_by_subsystem" in report
    assert "operator_do_now" in report
    assert "link_support" in report
    assert "link_recovery" in report
    assert "link_readiness" in report
