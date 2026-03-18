"""
M37E–M37H: Tests for signal quality, queue calmness, attention protection.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.signal_quality.models import (
    SignalQualityScore,
    ProtectedFocusItem,
    SuppressedQueueItem,
    StaleButImportantRule,
    ALWAYS_SHOW_PRIORITY,
    NEVER_SUPPRESS_SOURCES,
)
from workflow_dataset.signal_quality.scoring import (
    score_queue_item,
    score_assist_suggestion,
    rank_by_high_signal,
    eligible_resurfacing,
)
from workflow_dataset.signal_quality.quieting import (
    apply_queue_quieting,
    apply_assist_quieting,
)
from workflow_dataset.signal_quality.attention import (
    get_protected_focus,
    interruption_threshold_for_mode,
    digest_bundling_recommended,
)
from workflow_dataset.signal_quality.reports import (
    build_quality_report,
    build_suppressions_report,
    build_focus_protection_report,
    build_resurfacing_report,
)


class _FakeQueueItem:
    def __init__(self, item_id="x", priority="medium", urgency_score=0.5, value_score=0.5, source_subsystem=None, actionability_class=None, section_id="", created_at=""):
        self.item_id = item_id
        self.priority = priority
        self.urgency_score = urgency_score
        self.value_score = value_score
        self.source_subsystem = source_subsystem
        self.actionability_class = actionability_class
        self.section_id = section_id
        self.created_at = created_at


class _FakeActionability:
    value = "blocked"


class _FakeSource:
    value = "approval_queue"


def test_signal_quality_score_model():
    s = SignalQualityScore(urgency=0.9, usefulness=0.5, is_urgent_tier=True)
    assert s.is_urgent_tier is True
    assert s.urgency == 0.9


def test_score_queue_item_urgent_tier():
    item = _FakeQueueItem(priority="urgent", actionability_class=_FakeActionability)
    item.actionability_class = type("C", (), {"value": "blocked"})()
    score = score_queue_item(item, {})
    assert score.is_urgent_tier is True


def test_score_queue_item_approval_source():
    item = _FakeQueueItem(source_subsystem=_FakeSource)
    score = score_queue_item(item, {})
    assert score.is_urgent_tier is True


def test_rank_by_high_signal():
    items = [
        _FakeQueueItem("a", priority="low", urgency_score=0.3),
        _FakeQueueItem("b", priority="high", urgency_score=0.9),
    ]
    ranked = rank_by_high_signal(items, score_queue_item, {})
    assert len(ranked) == 2
    assert ranked[0].item_id == "b"


def test_apply_queue_quieting_never_suppress_urgent():
    urgent = _FakeQueueItem("u", priority="urgent")
    urgent.source_subsystem = type("S", (), {"value": "review_studio"})()
    urgent.actionability_class = type("A", (), {"value": "needs_review"})()
    focus = ProtectedFocusItem(active=True, allow_urgent_only=True)
    visible, suppressed = apply_queue_quieting([urgent], focus=focus)
    assert len(visible) == 1
    assert len(suppressed) == 0


def test_apply_queue_quieting_focus_safe_suppresses_non_urgent():
    low = _FakeQueueItem("l", priority="low", urgency_score=0.2)
    low.source_subsystem = type("S", (), {"value": "review_studio"})()
    low.actionability_class = type("A", (), {"value": "needs_review"})()
    focus = ProtectedFocusItem(active=True, allow_urgent_only=True)
    visible, suppressed = apply_queue_quieting([low], focus=focus)
    assert len(visible) == 0
    assert len(suppressed) == 1
    assert suppressed[0].reason == "focus_safe"


def test_apply_assist_quieting_returns_visible_and_suppressed():
    class _FakeSuggestion:
        suggestion_id = "s1"
        usefulness_score = 0.5
        interruptiveness_score = 0.2
        confidence = 0.6
        suggestion_type = "next_step"
    focus = ProtectedFocusItem(active=False)
    visible, suppressed = apply_assist_quieting([_FakeSuggestion()], focus=focus)
    assert len(visible) == 1
    assert len(suppressed) == 0


def test_interruption_threshold_for_mode():
    assert interruption_threshold_for_mode("focused") == 0.3
    assert interruption_threshold_for_mode("idle") == 0.8


def test_digest_bundling_recommended():
    rec = digest_bundling_recommended(25, overload_threshold=20)
    assert rec["recommended"] is True
    assert rec["queue_count"] == 25
    rec2 = digest_bundling_recommended(10, overload_threshold=20)
    assert rec2["recommended"] is False


def test_build_quality_report():
    supp = [SuppressedQueueItem(item_id="a", source="queue", reason="focus_safe")]
    report = build_quality_report(suppressed=supp)
    assert report["suppressed_count"] == 1
    assert "calmness_score" in report
    assert "noise_level" in report


def test_build_suppressions_report():
    supp = [
        SuppressedQueueItem(item_id="a", reason="focus_safe", resurfacing_eligible=True),
        SuppressedQueueItem(item_id="b", reason="low_value", resurfacing_eligible=True),
    ]
    report = build_suppressions_report(supp)
    assert report["total_suppressed"] == 2
    assert report["by_reason"]["focus_safe"] == 1
    assert report["resurfacing_eligible_count"] == 2


def test_build_focus_protection_report(tmp_path):
    report = build_focus_protection_report(repo_root=tmp_path)
    assert "active" in report
    assert "interruption_threshold" in report


def test_build_resurfacing_report():
    old = _FakeQueueItem("old", section_id="blocked", created_at="2020-01-01T00:00:00Z")
    old.urgency_score = 0.6
    rule = StaleButImportantRule(min_age_hours=1.0, required_section_or_kind=["blocked"])
    report = build_resurfacing_report(queue_items=[old], stale_rules=[rule])
    assert "resurfacing_candidates_count" in report
    assert "candidates" in report


def test_eligible_resurfacing():
    from datetime import datetime, timezone, timedelta
    old_created = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()
    item = _FakeQueueItem("x", section_id="blocked", created_at=old_created)
    item.urgency_score = 0.6
    rule = StaleButImportantRule(min_age_hours=72, required_section_or_kind=["blocked"])
    assert eligible_resurfacing(item, [rule]) is True


def test_always_show_priority_constants():
    assert "urgent" in ALWAYS_SHOW_PRIORITY
    assert "approval_queue" in NEVER_SUPPRESS_SOURCES


# ----- M37H.1 Calm profiles, interruption budgets, explanations -----
def test_calm_queue_profile_model():
    from workflow_dataset.signal_quality.models import CalmQueueProfile
    p = CalmQueueProfile(profile_id="focus", label="Focus", max_visible=10, noise_ceiling=0.3)
    assert p.max_visible == 10
    assert p.noise_ceiling == 0.3


def test_get_default_profiles():
    from workflow_dataset.signal_quality.profiles import get_default_profiles
    profiles = get_default_profiles()
    assert len(profiles) >= 4
    ids = {p.profile_id for p in profiles}
    assert "focus" in ids
    assert "default" in ids


def test_get_profile_for_role_mode():
    from workflow_dataset.signal_quality.profiles import get_profile_for_role_mode
    p = get_profile_for_role_mode("focused")
    assert p.profile_id == "focus"
    p2 = get_profile_for_role_mode("operator")
    assert p2.profile_id == "operator"


def test_get_noise_ceiling_for():
    from workflow_dataset.signal_quality.profiles import get_noise_ceiling_for
    ceiling, max_vis = get_noise_ceiling_for("focused")
    assert ceiling <= 0.5
    assert max_vis >= 1


def test_interruption_budget_model():
    from workflow_dataset.signal_quality.models import InterruptionBudget
    b = InterruptionBudget(budget_id="per_hour", period_hours=1.0, max_interruptions=15, consumed=3)
    assert b.consumed == 3
    assert b.max_interruptions == 15


def test_get_or_create_budget(tmp_path):
    from workflow_dataset.signal_quality.budgets import get_or_create_budget, remaining, build_interruption_budget_report
    budget = get_or_create_budget(repo_root=tmp_path)
    assert budget.max_interruptions >= 0
    assert remaining(tmp_path) >= 0
    report = build_interruption_budget_report(repo_root=tmp_path)
    assert "consumed" in report
    assert "remaining" in report
    assert "recommendation" in report


def test_explain_held_back():
    from workflow_dataset.signal_quality.explain import explain_held_back
    text = explain_held_back("focus_safe", work_mode="focused")
    assert "focus" in text.lower() or "urgent" in text.lower()


def test_explain_resurfaced():
    from workflow_dataset.signal_quality.explain import explain_resurfaced
    text = explain_resurfaced(rule_name="stale_blocked_3d", section_id="blocked")
    assert "resurface" in text.lower() or "stale" in text.lower() or "blocked" in text.lower()


def test_suppressed_item_has_explanation():
    from workflow_dataset.signal_quality.quieting import apply_queue_quieting
    from workflow_dataset.signal_quality.models import ProtectedFocusItem
    low = _FakeQueueItem("l", priority="low", urgency_score=0.2)
    low.source_subsystem = type("S", (), {"value": "review_studio"})()
    low.actionability_class = type("A", (), {"value": "needs_review"})()
    focus = ProtectedFocusItem(active=True, allow_urgent_only=True, work_mode="focused")
    visible, suppressed = apply_queue_quieting([low], focus=focus)
    assert len(suppressed) == 1
    assert suppressed[0].explanation != ""
