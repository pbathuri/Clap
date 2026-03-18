"""
M36H.1: Mode-aware queue views (focus, review, operator, wrap-up).
"""

from __future__ import annotations

from pathlib import Path

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.unified_queue.models import (
    UnifiedQueueItem,
    QueueViewMode,
    ModeAwareQueueView,
    QueueSection,
)


def build_mode_view(
    mode: QueueViewMode,
    items: list[UnifiedQueueItem],
    by_project: bool = False,
    by_episode: bool = False,
) -> ModeAwareQueueView:
    """
    Build a queue view for one mode: filter items that have this mode in mode_tags,
    optionally group into sections by project or episode.
    """
    now = utc_now_iso()
    tag = mode.value + "_ready" if mode != QueueViewMode.WRAP_UP else "wrap_up"
    filtered = [i for i in items if tag in i.mode_tags]
    item_ids = [i.item_id for i in filtered]
    sections: list[QueueSection] = []
    if by_project:
        # Build sections from filtered items only
        by_p: dict[str, list[str]] = {}
        for i in filtered:
            pid = i.project_id or "_no_project"
            by_p.setdefault(pid, []).append(i.item_id)
        for pid, ids in sorted(by_p.items(), key=lambda x: -len(x[1])):
            sections.append(QueueSection(
                section_id=f"project_{pid}",
                label=pid if pid != "_no_project" else "No project",
                project_id=pid if pid != "_no_project" else "",
                item_ids=ids,
                count=len(ids),
            ))
    elif by_episode:
        by_e: dict[str, list[str]] = {}
        for i in filtered:
            eid = i.episode_id or "_no_episode"
            by_e.setdefault(eid, []).append(i.item_id)
        for eid, ids in sorted(by_e.items(), key=lambda x: -len(x[1])):
            sections.append(QueueSection(
                section_id=f"episode_{eid}",
                label=eid if eid != "_no_episode" else "No episode",
                episode_id=eid if eid != "_no_episode" else "",
                item_ids=ids,
                count=len(ids),
            ))
    labels = {
        QueueViewMode.FOCUS: "Focus mode",
        QueueViewMode.REVIEW: "Review mode",
        QueueViewMode.OPERATOR: "Operator mode",
        QueueViewMode.WRAP_UP: "Wrap-up",
    }
    desc = {
        QueueViewMode.FOCUS: "Items suited for current project / focus.",
        QueueViewMode.REVIEW: "Items needing review or approval.",
        QueueViewMode.OPERATOR: "Items for operator follow-up and continuity.",
        QueueViewMode.WRAP_UP: "Lower-urgency items for end-of-session.",
    }
    return ModeAwareQueueView(
        mode=mode,
        label=labels.get(mode, mode.value),
        description=desc.get(mode, ""),
        item_ids=item_ids,
        sections=sections,
        total_count=len(item_ids),
        generated_at_utc=now,
    )


def build_mode_aware_view_bundle(
    items: list[UnifiedQueueItem],
    by_project: bool = False,
    by_episode: bool = False,
) -> dict[str, ModeAwareQueueView]:
    """Build all four mode views (focus, review, operator, wrap-up). M36H.1."""
    return {
        QueueViewMode.FOCUS.value: build_mode_view(QueueViewMode.FOCUS, items, by_project=by_project, by_episode=by_episode),
        QueueViewMode.REVIEW.value: build_mode_view(QueueViewMode.REVIEW, items, by_project=by_project, by_episode=by_episode),
        QueueViewMode.OPERATOR.value: build_mode_view(QueueViewMode.OPERATOR, items, by_project=by_project, by_episode=by_episode),
        QueueViewMode.WRAP_UP.value: build_mode_view(QueueViewMode.WRAP_UP, items, by_project=by_project, by_episode=by_episode),
    }
