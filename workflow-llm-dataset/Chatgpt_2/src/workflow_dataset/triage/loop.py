"""
M38E–M38H: Triage loop — surface evidence, group related, state transitions, route.
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

from workflow_dataset.triage.models import (
    UserObservedIssue,
    TriageStatus,
    SupportabilityImpact,
    ReproducibilityNote,
    OperatorNotes,
)
from workflow_dataset.triage.store import list_evidence, list_issues, load_issue, save_issue, update_triage_status


def surface_new_evidence(
    repo_root: Path | str | None = None,
    cohort_id: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return evidence not yet linked to any issue (by cohort)."""
    evidence = list_evidence(repo_root=repo_root, cohort_id=cohort_id, limit=limit * 2)
    issues = list_issues(repo_root=repo_root, cohort_id=cohort_id, limit=200)
    linked: set[str] = set()
    for i in issues:
        linked.update(i.evidence_ids)
    return [e.model_dump() for e in evidence if e.evidence_id not in linked][:limit]


def group_duplicates_or_related(
    issues: list[UserObservedIssue],
    by_summary_similarity: bool = False,
) -> dict[str, list[str]]:
    """Group issue_ids by same summary prefix or cohort+severity. Returns group_key -> [issue_id]."""
    groups: dict[str, list[str]] = {}
    for i in issues:
        key = f"{i.cohort_id}:{i.severity}:{(i.summary or '')[:40]}"
        groups.setdefault(key, []).append(i.issue_id)
    return {k: v for k, v in groups.items() if len(v) > 1}


def create_issue_from_evidence(
    evidence_ids: list[str],
    cohort_id: str = "",
    summary: str = "",
    severity: str = "medium",
    route_target: str = "supportability",
    repo_root: Path | str | None = None,
) -> UserObservedIssue:
    """Create a new issue linked to evidence."""
    now = utc_now_iso()
    issue_id = stable_id("issue", cohort_id, ",".join(evidence_ids[:3]), now, prefix="issue_")
    issue = UserObservedIssue(
        issue_id=issue_id,
        cohort_id=cohort_id,
        evidence_ids=evidence_ids,
        summary=summary[:500] or f"Issue from {len(evidence_ids)} evidence item(s)",
        severity=severity,
        triage_status=TriageStatus.NEW,
        route_target=route_target or "supportability",
        created_at_utc=now,
        updated_at_utc=now,
    )
    save_issue(issue, repo_root)
    return issue


def route_issue(issue_id: str, target: str, repo_root: Path | str | None = None) -> UserObservedIssue | None:
    """Set route_target to supportability | reliability | product."""
    issue = load_issue(issue_id, repo_root)
    if not issue:
        return None
    if target in ("supportability", "reliability", "product"):
        issue.route_target = target
        issue.updated_at_utc = utc_now_iso()
        save_issue(issue, repo_root)
    return issue


def mark_reproduced(
    issue_id: str,
    steps_summary: str = "",
    steps_detail: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> UserObservedIssue | None:
    """Set reproducibility note and status to REPRODUCED."""
    issue = load_issue(issue_id, repo_root)
    if not issue:
        return None
    issue.reproducibility_note = ReproducibilityNote(
        steps_summary=steps_summary,
        steps_detail=steps_detail or [],
        reproducible=True,
    )
    issue.reproducibility = "yes"
    issue.updated_at_utc = utc_now_iso()
    save_issue(issue, repo_root)
    return update_triage_status(issue_id, TriageStatus.REPRODUCED, repo_root)


def mark_resolved(issue_id: str, repo_root: Path | str | None = None) -> UserObservedIssue | None:
    """Set status to RESOLVED and resolved_at_utc."""
    return update_triage_status(issue_id, TriageStatus.RESOLVED, repo_root)


def mark_investigated(issue_id: str, repo_root: Path | str | None = None) -> UserObservedIssue | None:
    """Set status to INVESTIGATED."""
    return update_triage_status(issue_id, TriageStatus.INVESTIGATED, repo_root)


def mark_mitigated(issue_id: str, repo_root: Path | str | None = None) -> UserObservedIssue | None:
    """Set status to MITIGATED."""
    return update_triage_status(issue_id, TriageStatus.MITIGATED, repo_root)


def mark_blocked(issue_id: str, repo_root: Path | str | None = None) -> UserObservedIssue | None:
    """Set status to BLOCKED."""
    return update_triage_status(issue_id, TriageStatus.BLOCKED, repo_root)
