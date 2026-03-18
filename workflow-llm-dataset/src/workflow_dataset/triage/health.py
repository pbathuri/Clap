"""
M38E–M38H: Cohort health summary for mission control and reports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.triage.store import list_issues, list_evidence
from workflow_dataset.triage.loop import group_duplicates_or_related
from workflow_dataset.triage.models import TriageStatus
from workflow_dataset.triage.clusters import build_all_clusters
from workflow_dataset.triage.playbooks import get_playbook_for_cluster, get_operator_do_now_for_cluster


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_cohort_health_summary(
    repo_root: Path | str | None = None,
    cohort_id: str = "",
) -> dict[str, Any]:
    """
    Per-cohort (or all) health: open issue count, highest severity, repeated cluster,
    unresolved supported-surface count, recommended mitigation or downgrade.
    """
    root = _root(repo_root)
    issues = list_issues(repo_root=root, cohort_id=cohort_id, limit=200)
    evidence = list_evidence(repo_root=root, cohort_id=cohort_id, limit=500)
    unresolved = [i for i in issues if i.triage_status not in (TriageStatus.RESOLVED, TriageStatus.MITIGATED)]
    open_count = len(unresolved)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    highest = ""
    if unresolved:
        highest = min(unresolved, key=lambda x: severity_order.get(x.severity, 2)).severity
    groups = group_duplicates_or_related(unresolved)
    repeated_cluster: list[list[str]] = list(groups.values())[:5]
    supported_surface_unresolved = sum(
        1 for i in unresolved
        if getattr(i.supportability, "supported_surface_involved", False)
    )
    recommended_mitigation = ""
    recommended_downgrade = False
    if open_count == 0:
        recommended_mitigation = "No open issues; continue monitoring."
    elif highest == "critical":
        recommended_mitigation = "Address critical issue(s) before expanding cohort."
        recommended_downgrade = any(
            getattr(i.cohort_impact, "should_downgrade", False) for i in unresolved if i.cohort_impact
        )
    elif highest == "high":
        recommended_mitigation = "Triage high-severity issues; consider pausing new sessions until investigated."
    else:
        recommended_mitigation = "Review open issues; no pause recommended."
    # M38H.1: clusters by subsystem and operator do-now / links
    clusters_by_subsystem = build_all_clusters(repo_root=root, cohort_id=cohort_id, by="subsystem")
    operator_do_now = ""
    link_support = ""
    link_recovery = ""
    link_readiness = ""
    next_action_links: list[dict[str, str]] = []
    if clusters_by_subsystem:
        top_cluster = min(clusters_by_subsystem, key=lambda c: severity_order.get(c.severity, 2))
        do_now = get_operator_do_now_for_cluster(top_cluster)
        operator_do_now = do_now.guidance
        link_support = do_now.link_support
        link_recovery = do_now.link_recovery
        link_readiness = do_now.link_readiness
        if link_support or link_recovery or link_readiness:
            next_action_links = [
                {"label": "support", "command": link_support or ""},
                {"label": "recovery", "command": link_recovery or ""},
                {"label": "readiness", "command": link_readiness or ""},
            ]
    return {
        "cohort_id": cohort_id or "(all)",
        "open_issue_count": open_count,
        "total_issue_count": len(issues),
        "evidence_count": len(evidence),
        "highest_severity": highest or "none",
        "repeated_issue_clusters": repeated_cluster,
        "unresolved_supported_surface_count": supported_surface_unresolved,
        "recommended_mitigation": recommended_mitigation,
        "recommended_downgrade": recommended_downgrade,
        "clusters_by_subsystem": [c.model_dump() for c in clusters_by_subsystem[:10]],
        "operator_do_now": operator_do_now,
        "link_support": link_support,
        "link_recovery": link_recovery,
        "link_readiness": link_readiness,
        "next_action_links": next_action_links,
    }
