"""
M34L.1: Morning briefs + resume-work continuity cards.

Build morning brief cards, continuity cards, "what happened while you were away"
summaries, and direct handoff into workspace/project/action.
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

from workflow_dataset.automation_inbox.models import (
    MorningBriefCard,
    ResumeWorkContinuityCard,
    HandoffTarget,
    HANDOFF_WORKSPACE,
    HANDOFF_PROJECT,
    HANDOFF_ACTION,
)
from workflow_dataset.automation_inbox.collect import collect_from_background_runs
from workflow_dataset.automation_inbox.digests import build_morning_automation_digest


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_what_happened_summary(
    repo_root: Path | str | None = None,
    automation_limit: int = 20,
    timeline_limit: int = 15,
) -> list[str]:
    """What happened while you were away: automation outcomes + recent timeline events."""
    root = _repo_root(repo_root)
    lines: list[str] = []

    items = collect_from_background_runs(repo_root=root, limit=automation_limit, include_decided=False)
    for i in items:
        if i.kind == "automation_result":
            lines.append(f"  Completed: {i.run_id} — {(i.outcome_summary or 'ok')[:50]}")
        elif i.kind in ("blocked_automation", "failed_suppressed_automation"):
            lines.append(f"  Blocked/failed: {i.run_id} — {i.summary[:55]}")
    try:
        from workflow_dataset.review_studio.timeline import build_timeline
        events = build_timeline(repo_root=root, limit=timeline_limit)
        for e in events[:10]:
            lines.append(f"  [{e.kind}] {(e.timestamp_utc or '')[:16]} — {e.summary[:50]}")
    except Exception:
        pass
    return lines if lines else ["  (no recent activity)"]


def get_recommended_handoff(repo_root: Path | str | None = None) -> HandoffTarget | None:
    """Most relevant next handoff: blocked automation > approval queue > inbox > default."""
    root = _repo_root(repo_root)

    items = collect_from_background_runs(repo_root=root, limit=30, include_decided=False)
    for i in items:
        if i.kind in ("blocked_automation", "failed_suppressed_automation"):
            return HandoffTarget(
                label="Review blocked automation",
                target_type=HANDOFF_ACTION,
                view="automation_inbox",
                command=f"workflow-dataset automation-inbox show --id {i.item_id}",
                ref=i.item_id,
            )
    try:
        from workflow_dataset.review_studio.inbox import build_inbox
        inbox = build_inbox(repo_root=root, status="pending", limit=20)
        for i in inbox:
            if i.kind == "approval_queue":
                return HandoffTarget(
                    label="Review approval queue",
                    target_type=HANDOFF_ACTION,
                    view="inbox",
                    command="workflow-dataset inbox list",
                    ref=i.source_ref,
                )
            if i.kind == "blocked_run":
                return HandoffTarget(
                    label="Review blocked run",
                    target_type=HANDOFF_ACTION,
                    view="inbox",
                    command="workflow-dataset inbox list",
                    ref=i.source_ref,
                )
    except Exception:
        pass
    if items:
        return HandoffTarget(
            label="Review automation inbox",
            target_type=HANDOFF_ACTION,
            view="automation_inbox",
            command="workflow-dataset automation-inbox list",
            ref="",
        )
    return HandoffTarget(
        label="Open inbox",
        target_type=HANDOFF_ACTION,
        view="inbox",
        command="workflow-dataset inbox list",
        ref="",
    )


def build_morning_brief(
    repo_root: Path | str | None = None,
    automation_limit: int = 25,
    timeline_limit: int = 15,
) -> MorningBriefCard:
    """Build morning brief card: what happened while away, top next action, handoff."""
    root = _repo_root(repo_root)
    what = build_what_happened_summary(repo_root=root, automation_limit=automation_limit, timeline_limit=timeline_limit)
    digest = build_morning_automation_digest(repo_root=root, runs_limit=automation_limit)
    top_next = digest.most_important_follow_up or "Review inbox: workflow-dataset inbox list"
    handoff = get_recommended_handoff(repo_root=root)
    brief_id = stable_id("brief", "morning", utc_now_iso()[:10], prefix="brief_")
    return MorningBriefCard(
        brief_id=brief_id,
        generated_at=utc_now_iso(),
        title="Morning brief",
        what_happened_while_away=what,
        top_next_action=top_next,
        handoff=handoff,
        details={"automation_limit": automation_limit, "timeline_limit": timeline_limit},
    )


def build_resume_continuity_card(
    repo_root: Path | str | None = None,
    resume_context: str = "",
    automation_limit: int = 20,
    timeline_limit: int = 12,
) -> ResumeWorkContinuityCard:
    """Build resume-work continuity card: context, what happened, suggested next, handoff."""
    root = _repo_root(repo_root)
    what = build_what_happened_summary(repo_root=root, automation_limit=automation_limit, timeline_limit=timeline_limit)
    if not resume_context:
        try:
            from workflow_dataset.live_context.state import get_live_context_state
            ctx = get_live_context_state(repo_root=root)
            if ctx and getattr(ctx, "inferred_project", None) and getattr(ctx.inferred_project, "label", None):
                resume_context = f"Last context: {ctx.inferred_project.label}"
            else:
                resume_context = "Resume from inbox or workspace"
        except Exception:
            resume_context = "Resume from inbox or workspace"
    digest = build_morning_automation_digest(repo_root=root, runs_limit=automation_limit)
    suggested = digest.most_important_follow_up or "workflow-dataset inbox list"
    handoff = get_recommended_handoff(repo_root=root)
    card_id = stable_id("card", "resume", utc_now_iso()[:16], prefix="card_")
    return ResumeWorkContinuityCard(
        card_id=card_id,
        generated_at=utc_now_iso(),
        title="Resume work",
        resume_context=resume_context,
        what_happened_while_away=what,
        suggested_next=suggested,
        handoff=handoff,
        details={"automation_limit": automation_limit},
    )


def format_morning_brief(brief: MorningBriefCard) -> str:
    """Plain-text format for CLI."""
    lines = [
        f"# {brief.title}",
        f"Generated: {brief.generated_at[:19]}",
        "",
        "## What happened while you were away",
        *brief.what_happened_while_away,
        "",
        "## Top next action",
        f"  {brief.top_next_action}",
        "",
    ]
    if brief.handoff:
        lines.append("## Handoff")
        lines.append(f"  {brief.handoff.label}: {brief.handoff.command}")
    return "\n".join(lines)


def format_continuity_card(card: ResumeWorkContinuityCard) -> str:
    """Plain-text format for CLI."""
    lines = [
        f"# {card.title}",
        f"Generated: {card.generated_at[:19]}",
        "",
        "## Resume context",
        f"  {card.resume_context}",
        "",
        "## What happened while you were away",
        *card.what_happened_while_away,
        "",
        "## Suggested next",
        f"  {card.suggested_next}",
        "",
    ]
    if card.handoff:
        lines.append("## Handoff")
        lines.append(f"  {card.handoff.label}: {card.handoff.command}")
    return "\n".join(lines)
