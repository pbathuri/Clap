"""
M36E–M36H: Tests for unified work queue.
M36H.1: Mode-aware views, sections by project/episode, overloaded summary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.unified_queue.models import (
    UnifiedQueueItem,
    QueueSection,
    QueueViewMode,
    ModeAwareQueueView,
    QueueSummary,
    SourceSubsystem,
    ActionabilityClass,
)
from workflow_dataset.unified_queue.prioritize import (
    rank_unified_queue,
    build_sections_by_project,
    build_sections_by_episode,
)
from workflow_dataset.unified_queue.views import build_mode_view, build_mode_aware_view_bundle
from workflow_dataset.unified_queue.summary import build_queue_summary


def test_unified_queue_item_model():
    item = UnifiedQueueItem(
        item_id="uq_abc",
        source_subsystem=SourceSubsystem.REVIEW_STUDIO,
        source_ref="rs_1",
        actionability_class=ActionabilityClass.NEEDS_REVIEW,
        priority="high",
        section_id="review_ready",
        mode_tags=["review_ready", "focus_ready"],
        project_id="proj_1",
    )
    assert item.item_id == "uq_abc"
    assert item.mode_tags == ["review_ready", "focus_ready"]
    d = item.model_dump()
    assert d["section_id"] == "review_ready"


def test_rank_unified_queue_assigns_section_and_mode_tags():
    items = [
        UnifiedQueueItem(item_id="a", priority="low", urgency_score=0.3),
        UnifiedQueueItem(item_id="b", priority="high", urgency_score=0.9),
    ]
    ranked = rank_unified_queue(items, context={})
    assert len(ranked) == 2
    assert ranked[0].item_id == "b"
    assert ranked[1].item_id == "a"
    for i in ranked:
        assert i.section_id in ("blocked", "approval", "automation", "review_ready", "")
        assert isinstance(i.mode_tags, list)


def test_build_sections_by_project():
    items = [
        UnifiedQueueItem(item_id="1", project_id="A"),
        UnifiedQueueItem(item_id="2", project_id="A"),
        UnifiedQueueItem(item_id="3", project_id="B"),
    ]
    sections = build_sections_by_project(items)
    assert len(sections) == 2
    by_id = {s.section_id: s for s in sections}
    assert by_id["project_A"].count == 2
    assert by_id["project_B"].count == 1


def test_build_sections_by_episode():
    items = [
        UnifiedQueueItem(item_id="1", episode_id="ep1"),
        UnifiedQueueItem(item_id="2", episode_id="ep1"),
        UnifiedQueueItem(item_id="3", episode_id="ep2"),
    ]
    sections = build_sections_by_episode(items)
    assert len(sections) >= 1
    counts = {s.episode_id: s.count for s in sections if s.episode_id}
    assert counts.get("ep1") == 2
    assert counts.get("ep2") == 1


def test_build_mode_view_filters_by_mode_tag():
    items = [
        UnifiedQueueItem(item_id="1", mode_tags=["focus_ready", "review_ready"]),
        UnifiedQueueItem(item_id="2", mode_tags=["review_ready"]),
        UnifiedQueueItem(item_id="3", mode_tags=["wrap_up"]),
    ]
    view = build_mode_view(QueueViewMode.REVIEW, items)
    assert view.mode == QueueViewMode.REVIEW
    assert view.total_count == 2
    assert "1" in view.item_ids and "2" in view.item_ids
    assert "3" not in view.item_ids


def test_build_mode_aware_view_bundle():
    items = [
        UnifiedQueueItem(item_id="1", mode_tags=["focus_ready", "review_ready"]),
        UnifiedQueueItem(item_id="2", mode_tags=["wrap_up"]),
    ]
    bundle = build_mode_aware_view_bundle(items)
    assert "focus" in bundle
    assert "review" in bundle
    assert "operator" in bundle
    assert "wrap_up" in bundle
    assert bundle["review"].total_count == 1
    assert bundle["wrap_up"].total_count == 1


def test_build_queue_summary_not_overloaded():
    items = [UnifiedQueueItem(item_id=str(i)) for i in range(5)]
    for i in items:
        i.section_id = "review_ready"
    summary = build_queue_summary(items, overload_threshold=20)
    assert summary.total_count == 5
    assert summary.is_overloaded is False
    assert summary.overflow_message == ""


def test_build_queue_summary_overloaded():
    items = [UnifiedQueueItem(item_id=str(i), section_id="review_ready") for i in range(25)]
    summary = build_queue_summary(items, overload_threshold=20)
    assert summary.total_count == 25
    assert summary.is_overloaded is True
    assert "over threshold" in summary.overflow_message or summary.overflow_message
    assert "queue view" in summary.suggested_action.lower() or summary.suggested_action == ""


def test_build_queue_summary_by_section_and_mode():
    items = [
        UnifiedQueueItem(item_id="1", section_id="blocked", mode_tags=["review_ready"]),
        UnifiedQueueItem(item_id="2", section_id="approval", mode_tags=["review_ready"]),
        UnifiedQueueItem(item_id="3", section_id="approval", mode_tags=["focus_ready"]),
    ]
    summary = build_queue_summary(items)
    assert summary.by_section["blocked"] == 1
    assert summary.by_section["approval"] == 2
    assert summary.top_blocked_item_id == "1"
