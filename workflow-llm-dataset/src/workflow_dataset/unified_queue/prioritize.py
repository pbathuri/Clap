"""
M36E–M36H: Prioritize and rank unified queue; assign section and mode tags.
M36H.1: Sections by project or episode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.unified_queue.models import UnifiedQueueItem, QueueSection


def _assign_section_and_mode_tags(item: UnifiedQueueItem, context: dict[str, Any] | None) -> None:
    """Mutate item: set section_id and mode_tags from actionability, source, priority."""
    context = context or {}
    active_project_id = context.get("active_project_id", "")
    # Section: blocked first, then approval, then review_ready / focus_ready / operator_ready / wrap_up
    if item.actionability_class.value == "blocked" or item.blocked_reason:
        item.section_id = "blocked"
        item.mode_tags = ["review_ready", "operator_ready"]
    elif item.source_subsystem.value == "approval_queue":
        item.section_id = "approval"
        item.mode_tags = ["review_ready"]
    elif item.source_subsystem.value == "automation_inbox":
        item.section_id = "automation"
        item.mode_tags = ["review_ready", "operator_ready"]
    else:
        item.section_id = "review_ready"
        item.mode_tags = ["review_ready"]
    if active_project_id and item.project_id == active_project_id:
        item.mode_tags = list(set(item.mode_tags + ["focus_ready"]))
    # Wrap-up: lower urgency, review/automation
    if item.priority == "low" or item.urgency_score < 0.4:
        item.mode_tags = list(set(item.mode_tags + ["wrap_up"]))


def rank_unified_queue(
    items: list[UnifiedQueueItem],
    repo_root: Path | str | None = None,
    context: dict[str, Any] | None = None,
) -> list[UnifiedQueueItem]:
    """
    Sort by priority (urgent > high > medium > low), then urgency_score, then created_at.
    Assign section_id and mode_tags per item.
    """
    from workflow_dataset.unified_queue.collect import _root
    root = _root(repo_root)
    ctx = context or {}
    try:
        from workflow_dataset.project_case.store import get_current_project_id
        ctx["active_project_id"] = get_current_project_id(root) or ""
    except Exception:
        pass
    for item in items:
        _assign_section_and_mode_tags(item, ctx)
    order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    def key(i: UnifiedQueueItem):
        return (order.get(i.priority, 2), -i.urgency_score, i.created_at or "")
    return sorted(items, key=key)


def build_sections_by_project(items: list[UnifiedQueueItem]) -> list[QueueSection]:
    """Group items by project_id into QueueSections. M36H.1."""
    by_project: dict[str, list[str]] = {}
    for item in items:
        pid = item.project_id or "_no_project"
        by_project.setdefault(pid, []).append(item.item_id)
    out: list[QueueSection] = []
    for pid, ids in sorted(by_project.items(), key=lambda x: -len(x[1])):
        out.append(QueueSection(
            section_id=f"project_{pid}",
            label=pid if pid != "_no_project" else "No project",
            project_id=pid if pid != "_no_project" else "",
            item_ids=ids,
            count=len(ids),
        ))
    return out


def build_sections_by_episode(items: list[UnifiedQueueItem]) -> list[QueueSection]:
    """Group items by episode_id into QueueSections. M36H.1."""
    by_episode: dict[str, list[str]] = {}
    for item in items:
        eid = item.episode_id or "_no_episode"
        by_episode.setdefault(eid, []).append(item.item_id)
    out: list[QueueSection] = []
    for eid, ids in sorted(by_episode.items(), key=lambda x: -len(x[1])):
        out.append(QueueSection(
            section_id=f"episode_{eid}",
            label=eid if eid != "_no_episode" else "No episode",
            episode_id=eid if eid != "_no_episode" else "",
            item_ids=ids,
            count=len(ids),
        ))
    return out
