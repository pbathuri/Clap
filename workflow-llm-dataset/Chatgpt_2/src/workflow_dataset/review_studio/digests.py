"""
M29L.1: Digest views — morning summary, end-of-day summary, project-specific summary, rollout/support summary.
Extends review studio; does not rebuild it. Each digest: what changed, what is blocked, what needs approval, most important next intervention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.review_studio.timeline import build_timeline
from workflow_dataset.review_studio.inbox import build_inbox
from workflow_dataset.review_studio.store import load_inbox_snapshot


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


@dataclass
class DigestView:
    """One digest view: sections as lists of strings for display."""
    digest_type: str = ""  # morning | end_of_day | project | rollout_support
    generated_at: str = ""
    title: str = ""
    what_changed: list[str] = field(default_factory=list)
    what_is_blocked: list[str] = field(default_factory=list)
    what_needs_approval: list[str] = field(default_factory=list)
    most_important_intervention: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def _gather_common(
    repo_root: Path,
    project_id: str = "",
    timeline_limit: int = 25,
) -> tuple[list[str], list[str], list[str], str]:
    """Shared: recent timeline as what_changed, inbox blocked/approval, top intervention."""
    what_changed: list[str] = []
    what_is_blocked: list[str] = []
    what_needs_approval: list[str] = []
    most_important = ""

    try:
        events = build_timeline(repo_root=repo_root, project_id=project_id or "", limit=timeline_limit)
        for e in events[:15]:
            what_changed.append(f"  [{e.kind}] {(e.timestamp_utc or '')[:16]} — {e.summary[:70]}")
    except Exception as ex:
        what_changed.append(f"  (timeline error: {ex})")

    try:
        items = build_inbox(repo_root=repo_root, status="pending", limit=50)
        snapshot = load_inbox_snapshot(repo_root)
        for i in items:
            if i.kind == "blocked_run":
                what_is_blocked.append(f"  Run blocked: {i.source_ref} — {i.summary[:50]}")
            elif i.kind == "stalled_intervention":
                what_is_blocked.append(f"  Stalled: {i.source_ref}")
            elif i.kind == "approval_queue":
                what_needs_approval.append(f"  {i.summary[:60]} (queue_id={i.source_ref})")
        if items:
            most_important = items[0].summary[:80] if items[0].summary else (snapshot.get("oldest_item_id") or items[0].item_id)
        else:
            most_important = snapshot.get("oldest_item_id") or "(no pending items)"
    except Exception as ex:
        what_needs_approval.append(f"  (inbox error: {ex})")

    return what_changed, what_is_blocked, what_needs_approval, most_important


def build_morning_summary(
    repo_root: Path | str | None = None,
    timeline_limit: int = 25,
) -> DigestView:
    """Morning summary: what changed (recent activity), blocked, needs approval, top intervention."""
    root = _repo_root(repo_root)
    what_changed, what_blocked, what_approval, top = _gather_common(root, timeline_limit=timeline_limit)
    return DigestView(
        digest_type="morning",
        generated_at=utc_now_iso(),
        title="Morning summary",
        what_changed=what_changed if what_changed else ["  (no recent activity)"],
        what_is_blocked=what_blocked if what_blocked else ["  (none)"],
        what_needs_approval=what_approval if what_approval else ["  (none)"],
        most_important_intervention=top or "Review inbox: workflow-dataset inbox list",
        details={"timeline_limit": timeline_limit},
    )


def build_end_of_day_summary(
    repo_root: Path | str | None = None,
    timeline_limit: int = 40,
) -> DigestView:
    """End-of-day summary: same structure, framed for wrap-up."""
    root = _repo_root(repo_root)
    what_changed, what_blocked, what_approval, top = _gather_common(root, timeline_limit=timeline_limit)
    return DigestView(
        digest_type="end_of_day",
        generated_at=utc_now_iso(),
        title="End-of-day summary",
        what_changed=what_changed if what_changed else ["  (no activity in window)"],
        what_is_blocked=what_blocked if what_blocked else ["  (none)"],
        what_needs_approval=what_approval if what_approval else ["  (none)"],
        most_important_intervention=top or "No pending interventions; good to wrap.",
        details={"timeline_limit": timeline_limit},
    )


def build_project_summary(
    project_id: str,
    repo_root: Path | str | None = None,
    timeline_limit: int = 30,
) -> DigestView:
    """Project-specific summary: timeline and inbox filtered by project where applicable."""
    root = _repo_root(repo_root)
    what_changed, what_blocked, what_approval, top = _gather_common(root, project_id=project_id, timeline_limit=timeline_limit)
    # Filter approval/blocked to project-related if we have entity_refs
    try:
        items = build_inbox(repo_root=root, status="pending", limit=50)
        project_approval = [f"  {i.summary[:60]}" for i in items if i.entity_refs.get("project_id") == project_id or (not i.entity_refs.get("project_id") and i.kind == "approval_queue")]
        if project_approval:
            what_approval = project_approval
        project_blocked = [f"  {i.summary[:60]}" for i in items if i.entity_refs.get("project_id") == project_id and i.kind in ("blocked_run", "stalled_intervention")]
        if project_blocked:
            what_blocked = project_blocked
    except Exception:
        pass
    return DigestView(
        digest_type="project",
        generated_at=utc_now_iso(),
        title=f"Project summary: {project_id}",
        what_changed=what_changed if what_changed else ["  (no project activity in window)"],
        what_is_blocked=what_blocked if what_blocked else ["  (none)"],
        what_needs_approval=what_approval if what_approval else ["  (none)"],
        most_important_intervention=top or f"Review project: workflow-dataset timeline project --id {project_id}",
        details={"project_id": project_id, "timeline_limit": timeline_limit},
    )


def build_rollout_support_summary(
    repo_root: Path | str | None = None,
) -> DigestView:
    """Rollout/support summary: product state, staging, rollout readiness, support signals; plus common blocked/approval/intervention."""
    root = _repo_root(repo_root)
    what_changed, what_blocked, what_approval, top = _gather_common(root, timeline_limit=20)
    what_changed_rollout: list[str] = []
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        state = get_mission_control_state(root)
        product = state.get("product_state") or {}
        staging = product.get("staging") or {}
        what_changed_rollout.append(f"  Staging: {staging.get('staged_count', 0)} item(s) staged")
        what_changed_rollout.append(f"  Review package: {product.get('review_package') or {}}")
    except Exception as ex:
        what_changed_rollout.append(f"  (product state: {ex})")
    try:
        from workflow_dataset.rollout.readiness import build_rollout_readiness_report
        readiness = build_rollout_readiness_report(root)
        if readiness:
            what_changed_rollout.append(f"  Rollout: {str(readiness.get('summary', readiness))[:80]}")
    except Exception:
        pass
    return DigestView(
        digest_type="rollout_support",
        generated_at=utc_now_iso(),
        title="Rollout / support summary",
        what_changed=what_changed_rollout + what_changed[:8] if what_changed_rollout else what_changed,
        what_is_blocked=what_blocked if what_blocked else ["  (none)"],
        what_needs_approval=what_approval if what_approval else ["  (none)"],
        most_important_intervention=top or "Review staging and inbox: workflow-dataset review queue-status; workflow-dataset inbox list",
        details={},
    )


def format_digest_view(digest: DigestView) -> str:
    """Plain-text format for CLI."""
    lines = [
        f"# {digest.title}",
        f"Generated: {digest.generated_at[:19]}",
        "",
        "## What changed",
        *digest.what_changed,
        "",
        "## What is blocked",
        *digest.what_is_blocked,
        "",
        "## What needs approval",
        *digest.what_needs_approval,
        "",
        "## Most important intervention next",
        f"  {digest.most_important_intervention}",
        "",
    ]
    if digest.errors:
        lines.append("## Errors")
        lines.extend(f"  {e}" for e in digest.errors)
    return "\n".join(lines)
