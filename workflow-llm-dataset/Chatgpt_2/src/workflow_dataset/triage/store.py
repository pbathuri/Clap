"""
M38E–M38H: Persist evidence and issues under data/local/triage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.triage.models import CohortEvidenceItem, UserObservedIssue, EvidenceKind, TriageStatus


TRIAGE_DIR = "data/local/triage"
EVIDENCE_FILE = "evidence.jsonl"
ISSUES_DIR = "issues"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _triage_root(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / TRIAGE_DIR


def _evidence_path(repo_root: Path | str | None) -> Path:
    return _triage_root(repo_root) / EVIDENCE_FILE


def _issue_path(issue_id: str, repo_root: Path | str | None) -> Path:
    return _triage_root(repo_root) / ISSUES_DIR / f"{issue_id}.json"


def append_evidence(item: CohortEvidenceItem, repo_root: Path | str | None = None) -> Path:
    """Append one evidence item (JSON line)."""
    path = _evidence_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = item.model_dump_json() + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
    return path


def list_evidence(
    repo_root: Path | str | None = None,
    cohort_id: str = "",
    project_id: str = "",
    kind: str = "",
    limit: int = 100,
) -> list[CohortEvidenceItem]:
    """Load evidence items; filter by cohort_id, project_id, kind."""
    path = _evidence_path(repo_root)
    if not path.exists():
        return []
    items: list[CohortEvidenceItem] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                ev = CohortEvidenceItem(**data)
                if cohort_id and ev.cohort_id != cohort_id:
                    continue
                if project_id and ev.project_id != project_id:
                    continue
                if kind and ev.kind.value != kind:
                    continue
                items.append(ev)
                if len(items) >= limit:
                    break
            except Exception:
                continue
    return items


def save_issue(issue: UserObservedIssue, repo_root: Path | str | None = None) -> Path:
    """Write issue to issues/<issue_id>.json."""
    root = _triage_root(repo_root)
    (root / ISSUES_DIR).mkdir(parents=True, exist_ok=True)
    path = _issue_path(issue.issue_id, repo_root)
    path.write_text(issue.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_issue(issue_id: str, repo_root: Path | str | None = None) -> UserObservedIssue | None:
    """Load one issue by id."""
    path = _issue_path(issue_id, repo_root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return UserObservedIssue(**data)
    except Exception:
        return None


def list_issues(
    repo_root: Path | str | None = None,
    cohort_id: str = "",
    status: str = "",
    limit: int = 50,
) -> list[UserObservedIssue]:
    """List issues; filter by cohort_id and triage_status."""
    root = _triage_root(repo_root) / ISSUES_DIR
    if not root.exists():
        return []
    issues: list[UserObservedIssue] = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            issue = UserObservedIssue(**data)
            if cohort_id and issue.cohort_id != cohort_id:
                continue
            if status and issue.triage_status.value != status:
                continue
            issues.append(issue)
            if len(issues) >= limit:
                break
        except Exception:
            continue
    return issues


def update_triage_status(
    issue_id: str,
    new_status: TriageStatus,
    repo_root: Path | str | None = None,
    resolved_at: str = "",
) -> UserObservedIssue | None:
    """Update issue triage status; set resolved_at_utc when RESOLVED."""
    issue = load_issue(issue_id, repo_root)
    if not issue:
        return None
    issue.triage_status = new_status
    issue.updated_at_utc = utc_now_iso()
    if new_status == TriageStatus.RESOLVED and resolved_at:
        issue.resolved_at_utc = resolved_at
    elif new_status == TriageStatus.RESOLVED:
        issue.resolved_at_utc = issue.updated_at_utc
    save_issue(issue, repo_root)
    return issue
