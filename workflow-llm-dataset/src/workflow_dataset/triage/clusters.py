"""
M38H.1: Issue clusters by subsystem, workflow, cohort.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

from workflow_dataset.triage.models import UserObservedIssue, IssueCluster, TriageStatus
from workflow_dataset.triage.store import list_issues
from workflow_dataset.triage.playbooks import get_playbook_for_cluster


def build_clusters_by_subsystem(
    repo_root: Path | str | None = None,
    cohort_id: str = "",
    include_resolved: bool = False,
) -> list[IssueCluster]:
    """Group issues by affected_subsystems (first subsystem) into clusters."""
    issues = list_issues(repo_root=repo_root, cohort_id=cohort_id, limit=200)
    if not include_resolved:
        issues = [i for i in issues if i.triage_status not in (TriageStatus.RESOLVED, TriageStatus.MITIGATED)]
    by_key: dict[str, list[UserObservedIssue]] = {}
    for i in issues:
        subs = i.affected_subsystems or []
        key = subs[0] if subs else "_no_subsystem"
        by_key.setdefault(key, []).append(i)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    clusters: list[IssueCluster] = []
    for subsystem, group in by_key.items():
        if not group:
            continue
        highest = min(group, key=lambda x: severity_order.get(x.severity, 2))
        cid = stable_id("cluster", "subsystem", subsystem, cohort_id or "all", prefix="cluster_")
        cl = IssueCluster(
            cluster_id=cid,
            cohort_id=cohort_id or "",
            subsystem=subsystem,
            workflow_or_context=highest.workflow_or_context or "",
            issue_ids=[i.issue_id for i in group],
            severity=highest.severity,
            summary=f"{subsystem}: {len(group)} issue(s)",
            playbook_id="",
            created_at_utc=utc_now_iso(),
        )
        pb = get_playbook_for_cluster(cl)
        cl.playbook_id = pb.playbook_id
        clusters.append(cl)
    return clusters


def build_clusters_by_workflow(
    repo_root: Path | str | None = None,
    cohort_id: str = "",
    include_resolved: bool = False,
) -> list[IssueCluster]:
    """Group issues by workflow_or_context."""
    issues = list_issues(repo_root=repo_root, cohort_id=cohort_id, limit=200)
    if not include_resolved:
        issues = [i for i in issues if i.triage_status not in (TriageStatus.RESOLVED, TriageStatus.MITIGATED)]
    by_key: dict[str, list[UserObservedIssue]] = {}
    for i in issues:
        key = (i.workflow_or_context or "_no_workflow").strip() or "_no_workflow"
        by_key.setdefault(key, []).append(i)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    clusters: list[IssueCluster] = []
    for workflow, group in by_key.items():
        if not group:
            continue
        highest = min(group, key=lambda x: severity_order.get(x.severity, 2))
        subs = highest.affected_subsystems or []
        cid = stable_id("cluster", "workflow", workflow, cohort_id or "all", prefix="cluster_")
        cl = IssueCluster(
            cluster_id=cid,
            cohort_id=cohort_id or "",
            subsystem=subs[0] if subs else "",
            workflow_or_context=workflow,
            issue_ids=[i.issue_id for i in group],
            severity=highest.severity,
            summary=f"Workflow {workflow}: {len(group)} issue(s)",
            playbook_id="",
            created_at_utc=utc_now_iso(),
        )
        pb = get_playbook_for_cluster(cl)
        cl.playbook_id = pb.playbook_id
        clusters.append(cl)
    return clusters


def build_clusters_by_cohort(
    repo_root: Path | str | None = None,
    cohort_id: str = "",
    include_resolved: bool = False,
) -> list[IssueCluster]:
    """One cluster per cohort (all issues in that cohort)."""
    issues = list_issues(repo_root=repo_root, cohort_id=cohort_id, limit=200)
    if not include_resolved:
        issues = [i for i in issues if i.triage_status not in (TriageStatus.RESOLVED, TriageStatus.MITIGATED)]
    if not issues:
        return []
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    highest = min(issues, key=lambda x: severity_order.get(x.severity, 2))
    cid = stable_id("cluster", "cohort", cohort_id or "all", prefix="cluster_")
    cl = IssueCluster(
        cluster_id=cid,
        cohort_id=cohort_id or "",
        subsystem="",
        workflow_or_context="",
        issue_ids=[i.issue_id for i in issues],
        severity=highest.severity,
        summary=f"Cohort {cohort_id or '(all)'}: {len(issues)} issue(s)",
        playbook_id="",
        created_at_utc=utc_now_iso(),
    )
    pb = get_playbook_for_cluster(cl)
    cl.playbook_id = pb.playbook_id
    return [cl]


def build_all_clusters(
    repo_root: Path | str | None = None,
    cohort_id: str = "",
    by: str = "subsystem",
) -> list[IssueCluster]:
    """Build clusters by subsystem | workflow | cohort."""
    if by == "workflow":
        return build_clusters_by_workflow(repo_root=repo_root, cohort_id=cohort_id)
    if by == "cohort":
        return build_clusters_by_cohort(repo_root=repo_root, cohort_id=cohort_id)
    return build_clusters_by_subsystem(repo_root=repo_root, cohort_id=cohort_id)
