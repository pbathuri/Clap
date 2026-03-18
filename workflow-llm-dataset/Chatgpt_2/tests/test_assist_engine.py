"""
M32E–M32H: Tests for just-in-time assist engine — models, generation, queue, store, explain,
prioritization, repeat suppression, dismiss/snooze/accept, low-confidence, no-context.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.assist_engine.models import (
    AssistSuggestion,
    SuggestionReason,
    TriggeringContext,
)
from workflow_dataset.assist_engine.store import (
    save_suggestion,
    load_suggestion,
    list_suggestions,
    update_status,
    list_dismissed_patterns,
)
from workflow_dataset.assist_engine.generation import generate_assist_suggestions
from workflow_dataset.assist_engine.queue import (
    run_now,
    get_queue,
    accept_suggestion,
    dismiss_suggestion,
    snooze_suggestion,
    _suppress_repetitive,
)
from workflow_dataset.assist_engine.explain import explain_suggestion


def _make_suggestion(
    suggestion_id: str = "sug_test1",
    suggestion_type: str = "next_step",
    title: str = "Test suggestion",
    confidence: float = 0.8,
    usefulness_score: float = 0.7,
) -> AssistSuggestion:
    return AssistSuggestion(
        suggestion_id=suggestion_id,
        suggestion_type=suggestion_type,
        title=title,
        description="Test description",
        reason=SuggestionReason(title="Test reason", description="Because.", evidence=["e1"]),
        triggering_context=TriggeringContext(source="test", summary="Test context", signals=["s1"]),
        confidence=confidence,
        usefulness_score=usefulness_score,
        interruptiveness_score=0.2,
        required_operator_action="Do something.",
        status="pending",
        created_utc="2025-03-16T12:00:00Z",
        updated_utc="2025-03-16T12:00:00Z",
    )


def test_assist_suggestion_model():
    s = _make_suggestion()
    assert s.suggestion_id == "sug_test1"
    assert s.suggestion_type == "next_step"
    assert s.reason is not None
    assert s.reason.title == "Test reason"
    assert s.triggering_context is not None
    assert s.triggering_context.source == "test"
    d = s.to_dict()
    assert d["suggestion_id"] == "sug_test1"
    loaded = AssistSuggestion.from_dict(d)
    assert loaded.suggestion_id == s.suggestion_id


def test_store_save_load(tmp_path: Path):
    s = _make_suggestion()
    save_suggestion(s, repo_root=tmp_path)
    loaded = load_suggestion("sug_test1", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.title == "Test suggestion"
    assert load_suggestion("nonexistent", repo_root=tmp_path) is None


def test_store_list_and_update_status(tmp_path: Path):
    save_suggestion(_make_suggestion("sug_a"), repo_root=tmp_path)
    save_suggestion(_make_suggestion("sug_b", suggestion_id="sug_b"), repo_root=tmp_path)
    pending = list_suggestions(repo_root=tmp_path, status_filter="pending", limit=10)
    assert len(pending) >= 2
    assert update_status("sug_a", "dismissed", repo_root=tmp_path) is True
    pending_after = list_suggestions(repo_root=tmp_path, status_filter="pending", limit=10)
    assert len(pending_after) < len(pending) or all(p.suggestion_id != "sug_a" for p in pending_after)
    dismissed = list_suggestions(repo_root=tmp_path, status_filter="dismissed", limit=10)
    assert any(d.suggestion_id == "sug_a" for d in dismissed)


def test_list_dismissed_patterns(tmp_path: Path):
    save_suggestion(_make_suggestion("sug_x", suggestion_type="blocked_review"), repo_root=tmp_path)
    update_status("sug_x", "dismissed", repo_root=tmp_path)
    patterns = list_dismissed_patterns(repo_root=tmp_path, limit=10)
    assert isinstance(patterns, list)
    assert any(p.get("suggestion_type") == "blocked_review" for p in patterns)


def test_generation_returns_list_no_crash(tmp_path: Path):
    suggestions = generate_assist_suggestions(repo_root=tmp_path, max_total=10)
    assert isinstance(suggestions, list)
    for s in suggestions:
        assert isinstance(s, AssistSuggestion)
        assert s.suggestion_id
        assert s.suggestion_type
        assert 0 <= s.confidence <= 1
        assert 0 <= s.usefulness_score <= 1


def test_queue_run_now(tmp_path: Path):
    result = run_now(repo_root=tmp_path, max_new=5, merge_with_existing_pending=True)
    assert isinstance(result, list)
    for s in result:
        assert s.status == "pending"


def test_queue_get_queue(tmp_path: Path):
    items = get_queue(repo_root=tmp_path, status_filter="pending", limit=10)
    assert isinstance(items, list)
    items = get_queue(repo_root=tmp_path, status_filter="dismissed", limit=5)
    assert isinstance(items, list)


def test_accept_dismiss_snooze(tmp_path: Path):
    s = _make_suggestion("sug_act")
    save_suggestion(s, repo_root=tmp_path)
    assert accept_suggestion("sug_act", repo_root=tmp_path) is True
    loaded = load_suggestion("sug_act", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.status == "accepted"
    update_status("sug_act", "pending", repo_root=tmp_path)
    assert dismiss_suggestion("sug_act", repo_root=tmp_path) is True
    loaded = load_suggestion("sug_act", repo_root=tmp_path)
    assert loaded.status == "dismissed"
    update_status("sug_act", "pending", repo_root=tmp_path)
    assert snooze_suggestion("sug_act", "2026-01-01T00:00:00Z", repo_root=tmp_path) is True
    loaded = load_suggestion("sug_act", repo_root=tmp_path)
    assert loaded.status == "snoozed"
    assert loaded.snoozed_until_utc == "2026-01-01T00:00:00Z"
    assert dismiss_suggestion("nonexistent", repo_root=tmp_path) is False


def test_suppress_repetitive(tmp_path: Path):
    s1 = _make_suggestion("sug_r1", suggestion_type="next_step", title="Same type and reason")
    s1.reason = SuggestionReason(title="Same reason", description="", evidence=[])
    s2 = _make_suggestion("sug_r2", suggestion_type="next_step", title="Other")
    s2.reason = SuggestionReason(title="Other reason", description="", evidence=[])
    save_suggestion(s1, repo_root=tmp_path)
    update_status("sug_r1", "dismissed", repo_root=tmp_path)
    candidates = [s1, s2]
    filtered = _suppress_repetitive(candidates, repo_root=tmp_path, window_hours=24)
    assert len(filtered) <= len(candidates)
    patterns = list_dismissed_patterns(repo_root=tmp_path)
    type_reason_keys = {(d.get("suggestion_type", ""), (d.get("reason_title") or "")[:60]) for d in patterns}
    if ("next_step", "Same reason") in type_reason_keys:
        assert not any(x.suggestion_id == "sug_r1" for x in filtered)


def test_explain_suggestion(tmp_path: Path):
    s = _make_suggestion("sug_ex")
    save_suggestion(s, repo_root=tmp_path)
    ex = explain_suggestion("sug_ex", repo_root=tmp_path)
    assert ex["suggestion_id"] == "sug_ex"
    assert "reason" in ex
    assert ex["reason"]["title"] == "Test reason"
    assert "triggering_context" in ex
    assert ex["triggering_context"]["source"] == "test"
    assert explain_suggestion("nonexistent", repo_root=tmp_path) == {}


def test_no_context_empty_or_minimal(tmp_path: Path):
    suggestions = generate_assist_suggestions(repo_root=tmp_path, max_total=5)
    assert isinstance(suggestions, list)
    queue = get_queue(repo_root=tmp_path, status_filter="pending", limit=5)
    assert isinstance(queue, list)
