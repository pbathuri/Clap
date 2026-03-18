"""
M34I–M34L: Recurring outcome digests for automation — morning, project, blocked, approval-followup.
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
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]

from workflow_dataset.automation_inbox.models import RecurringDigest
from workflow_dataset.automation_inbox.collect import collect_from_background_runs


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_morning_automation_digest(
    repo_root: Path | str | None = None,
    runs_limit: int = 30,
) -> RecurringDigest:
    """Morning automation digest: what completed, what blocked/failed, most important follow-up."""
    root = _repo_root(repo_root)
    items = collect_from_background_runs(repo_root=root, limit=runs_limit, include_decided=False)
    completed: list[str] = []
    blocked_or_failed: list[str] = []
    for i in items:
        if i.kind == "automation_result":
            completed.append(f"  {i.run_id}: {(i.outcome_summary or 'ok')[:60]}")
        elif i.kind in ("blocked_automation", "failed_suppressed_automation"):
            blocked_or_failed.append(f"  {i.run_id}: {i.summary[:70]}")
    most_important = ""
    for i in items:
        if i.kind in ("blocked_automation", "failed_suppressed_automation") and i.priority in ("high", "urgent"):
            most_important = f"Review blocked/failed: workflow-dataset automation-inbox show --id {i.item_id}"
            break
    if not most_important and items:
        most_important = f"Review automation inbox: workflow-dataset automation-inbox list"
    if not most_important:
        most_important = "No automation follow-up needed."
    digest_id = stable_id("digest", "morning_automation", utc_now_iso()[:10], prefix="dig_")
    return RecurringDigest(
        digest_id=digest_id,
        digest_type="morning_automation",
        generated_at=utc_now_iso(),
        title="Morning automation digest",
        completed_runs=completed if completed else ["  (no completed runs in window)"],
        blocked_or_failed=blocked_or_failed if blocked_or_failed else ["  (none)"],
        approval_follow_ups=[],  # Could integrate with review_studio approval queue
        most_important_follow_up=most_important,
        details={"runs_limit": runs_limit},
    )


def build_project_automation_digest(
    project_id: str,
    repo_root: Path | str | None = None,
    runs_limit: int = 30,
) -> RecurringDigest:
    """Project-specific automation digest (filter by project_id where available)."""
    root = _repo_root(repo_root)
    items = collect_from_background_runs(repo_root=root, limit=runs_limit, include_decided=False)
    completed: list[str] = []
    blocked_or_failed: list[str] = []
    for i in items:
        if i.project_id != project_id and project_id not in (i.entity_refs.get("project_id") or ""):
            continue
        if i.kind == "automation_result":
            completed.append(f"  {i.run_id}: {(i.outcome_summary or 'ok')[:60]}")
        elif i.kind in ("blocked_automation", "failed_suppressed_automation"):
            blocked_or_failed.append(f"  {i.run_id}: {i.summary[:70]}")
    most_important = f"Review project automations: workflow-dataset automation-digest project --id {project_id}"
    digest_id = stable_id("digest", "project_automation", project_id, utc_now_iso()[:10], prefix="dig_")
    return RecurringDigest(
        digest_id=digest_id,
        digest_type="project_automation",
        generated_at=utc_now_iso(),
        title=f"Project automation digest: {project_id}",
        completed_runs=completed if completed else ["  (no project runs in window)"],
        blocked_or_failed=blocked_or_failed if blocked_or_failed else ["  (none)"],
        approval_follow_ups=[],
        most_important_follow_up=most_important,
        details={"project_id": project_id, "runs_limit": runs_limit},
    )


def build_blocked_automation_digest(
    repo_root: Path | str | None = None,
    limit: int = 20,
) -> RecurringDigest:
    """Digest of blocked/failed automations only."""
    root = _repo_root(repo_root)
    items = collect_from_background_runs(repo_root=root, limit=limit * 2, include_decided=False)
    blocked_or_failed: list[str] = []
    for i in items:
        if i.kind in ("blocked_automation", "failed_suppressed_automation"):
            blocked_or_failed.append(f"  [{i.run_id}] {i.summary[:70]}")
    most_important = "workflow-dataset automation-inbox list" if blocked_or_failed else "No blocked automations."
    digest_id = stable_id("digest", "blocked_automation", utc_now_iso()[:16], prefix="dig_")
    return RecurringDigest(
        digest_id=digest_id,
        digest_type="blocked_automation",
        generated_at=utc_now_iso(),
        title="Blocked automation digest",
        completed_runs=[],
        blocked_or_failed=blocked_or_failed if blocked_or_failed else ["  (none)"],
        approval_follow_ups=[],
        most_important_follow_up=most_important,
        details={"limit": limit},
    )


def build_approval_followup_digest(
    repo_root: Path | str | None = None,
) -> RecurringDigest:
    """Digest of items needing approval follow-up (bridge to review_studio approval queue)."""
    root = _repo_root(repo_root)
    approval_follow_ups: list[str] = []
    try:
        from workflow_dataset.review_studio.inbox import build_inbox
        inbox = build_inbox(repo_root=root, status="pending", limit=30)
        for i in inbox:
            if i.kind == "approval_queue":
                approval_follow_ups.append(f"  {i.source_ref}: {i.summary[:60]}")
    except Exception:
        pass
    most_important = "workflow-dataset inbox list" if approval_follow_ups else "No approval follow-ups."
    digest_id = stable_id("digest", "approval_followup", utc_now_iso()[:10], prefix="dig_")
    return RecurringDigest(
        digest_id=digest_id,
        digest_type="approval_followup",
        generated_at=utc_now_iso(),
        title="Approval follow-up digest",
        completed_runs=[],
        blocked_or_failed=[],
        approval_follow_ups=approval_follow_ups if approval_follow_ups else ["  (none)"],
        most_important_follow_up=most_important,
        details={},
    )


def format_digest(digest: RecurringDigest) -> str:
    """Plain-text format for CLI."""
    lines = [
        f"# {digest.title}",
        f"Generated: {digest.generated_at[:19]}",
        "",
        "## Completed runs",
        *digest.completed_runs,
        "",
        "## Blocked or failed",
        *digest.blocked_or_failed,
        "",
        "## Approval follow-ups",
        *digest.approval_follow_ups,
        "",
        "## Most important follow-up",
        f"  {digest.most_important_follow_up}",
        "",
    ]
    if digest.errors:
        lines.append("## Errors")
        lines.extend(f"  {e}" for e in digest.errors)
    return "\n".join(lines)
