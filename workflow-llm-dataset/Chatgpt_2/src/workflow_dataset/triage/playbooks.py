"""
M38H.1: Mitigation playbooks and operator "do now" guidance; links to support/recovery/readiness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.triage.models import MitigationPlaybook, OperatorDoNow, IssueCluster, UserObservedIssue


def get_default_playbooks() -> list[MitigationPlaybook]:
    """Built-in mitigation playbooks with links to support/recovery/readiness."""
    return [
        MitigationPlaybook(
            playbook_id="executor_blocked",
            label="Executor / run blocked",
            description="Issues involving executor, run blocked, or step failure.",
            steps=[
                "Run: workflow-dataset recovery suggest --subsystem executor",
                "Run: workflow-dataset reliability run --id <path_id> to reproduce",
                "Check automation-inbox and review-studio for related items",
            ],
            operator_do_now=OperatorDoNow(
                guidance="Check recovery guide for executor; run reliability to reproduce.",
                link_support="workflow-dataset release triage",
                link_recovery="workflow-dataset recovery suggest --subsystem executor",
                link_readiness="workflow-dataset release report",
                commands=["recovery suggest --subsystem executor", "reliability run"],
            ),
            link_support="workflow-dataset release triage",
            link_recovery="workflow-dataset recovery suggest --subsystem executor",
            link_readiness="workflow-dataset release report",
            related_subsystems=["executor", "supervised_loop", "background_run"],
            when_to_use="Executor step failed, run blocked, or automation handoff.",
        ),
        MitigationPlaybook(
            playbook_id="install_upgrade",
            label="Install or upgrade failure",
            description="Pack install, upgrade, or migration issues.",
            steps=[
                "Run: workflow-dataset recovery guide --case failed_upgrade",
                "Run: workflow-dataset package install-check",
                "Review release readiness and supportability",
            ],
            operator_do_now=OperatorDoNow(
                guidance="Run recovery guide for failed upgrade; then install-check.",
                link_support="workflow-dataset release triage",
                link_recovery="workflow-dataset recovery guide --case failed_upgrade",
                link_readiness="workflow-dataset release report",
                commands=["recovery guide --case failed_upgrade", "package install-check"],
            ),
            link_support="workflow-dataset release triage",
            link_recovery="workflow-dataset recovery guide --case failed_upgrade",
            link_readiness="workflow-dataset release report",
            related_subsystems=["install", "distribution", "packs"],
            when_to_use="Install check fails, upgrade or migration errors.",
        ),
        MitigationPlaybook(
            playbook_id="approval_policy",
            label="Approval or policy blocked",
            description="Trust, approval registry, or policy blocking execution.",
            steps=[
                "Run: workflow-dataset trust status (or trust cockpit)",
                "Run: workflow-dataset recovery guide --case blocked_approval_policy",
                "Review approvals and human_policy",
            ],
            operator_do_now=OperatorDoNow(
                guidance="Check trust status and recovery guide for blocked approval.",
                link_support="workflow-dataset release triage",
                link_recovery="workflow-dataset recovery guide --case blocked_approval_policy",
                link_readiness="workflow-dataset release report",
                commands=["trust status", "recovery guide --case blocked_approval_policy"],
            ),
            link_support="workflow-dataset release triage",
            link_recovery="workflow-dataset recovery guide --case blocked_approval_policy",
            link_readiness="workflow-dataset release report",
            related_subsystems=["trust", "inbox", "human_policy"],
            when_to_use="Approval registry missing or policy blocks execution.",
        ),
        MitigationPlaybook(
            playbook_id="general_support",
            label="General supportability triage",
            description="Run release triage and supportability report.",
            steps=[
                "Run: workflow-dataset release triage",
                "Run: workflow-dataset release report",
                "Run: workflow-dataset recovery suggest (no --case) for suggested playbook",
            ],
            operator_do_now=OperatorDoNow(
                guidance="Run release triage and recovery suggest for next steps.",
                link_support="workflow-dataset release triage",
                link_recovery="workflow-dataset recovery suggest",
                link_readiness="workflow-dataset release report",
                commands=["release triage", "release report", "recovery suggest"],
            ),
            link_support="workflow-dataset release triage",
            link_recovery="workflow-dataset recovery suggest",
            link_readiness="workflow-dataset release report",
            related_subsystems=[],
            when_to_use="Unclear subsystem or need full supportability view.",
        ),
    ]


def get_playbook_for_subsystem(subsystem: str) -> MitigationPlaybook | None:
    """Return first playbook whose related_subsystems include subsystem."""
    for p in get_default_playbooks():
        if subsystem and subsystem in p.related_subsystems:
            return p
    return None


def get_playbook_for_issue(issue: UserObservedIssue) -> MitigationPlaybook:
    """Suggest playbook from issue's affected_subsystems or route_target."""
    subs = issue.affected_subsystems or []
    for s in subs:
        pb = get_playbook_for_subsystem(s)
        if pb:
            return pb
    if issue.route_target == "reliability":
        for p in get_default_playbooks():
            if p.playbook_id == "executor_blocked":
                return p
    return get_default_playbooks()[-1]  # general_support


def get_playbook_for_cluster(cluster: IssueCluster) -> MitigationPlaybook:
    """Suggest playbook from cluster's subsystem."""
    if cluster.subsystem:
        pb = get_playbook_for_subsystem(cluster.subsystem)
        if pb:
            return pb
    return get_default_playbooks()[-1]


def get_operator_do_now_for_issue(issue: UserObservedIssue) -> OperatorDoNow:
    """Operator guidance and links for this issue."""
    playbook = get_playbook_for_issue(issue)
    return playbook.operator_do_now


def get_operator_do_now_for_cluster(cluster: IssueCluster) -> OperatorDoNow:
    """Operator guidance and links for this cluster."""
    playbook = get_playbook_for_cluster(cluster)
    return playbook.operator_do_now


def list_playbook_ids() -> list[str]:
    """Return all default playbook ids."""
    return [p.playbook_id for p in get_default_playbooks()]


def get_playbook(playbook_id: str) -> MitigationPlaybook | None:
    """Get playbook by id."""
    for p in get_default_playbooks():
        if p.playbook_id == playbook_id:
            return p
    return None
