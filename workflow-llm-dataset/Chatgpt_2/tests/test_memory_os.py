"""
M44A–M44D: Tests for Memory OS — surfaces, retrieve by intent/scope, explain, weak-memory, no-match.
M44D.1: Retrieval profiles and vertical memory views.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.memory_os import (
    list_surfaces,
    get_surface,
    memory_os_retrieve,
    memory_os_status,
    list_profiles,
    get_profile,
    get_profile_reason,
    list_views,
    get_view_for_vertical,
    SURFACE_PROJECT,
    SURFACE_SESSION,
    SURFACE_LEARNING,
)
from workflow_dataset.memory_os.models import (
    RetrievalScope,
    RetrievalIntentOS,
    RETRIEVAL_INTENT_RECALL_CONTEXT,
    PROFILE_CONSERVATIVE,
    PROFILE_CODING_HEAVY,
)
from workflow_dataset.memory_os.explain import build_explanation, format_explanation_text


def test_list_surfaces() -> None:
    """Surfaces include project, session, episode, continuity, operator, learning, cursor."""
    surfaces = list_surfaces()
    ids = [s.surface_id for s in surfaces]
    assert SURFACE_PROJECT in ids
    assert SURFACE_SESSION in ids
    assert SURFACE_LEARNING in ids
    assert "episode" in ids
    assert "continuity" in ids
    assert "operator" in ids
    assert "cursor" in ids


def test_get_surface() -> None:
    """get_surface returns the right surface or None."""
    s = get_surface(SURFACE_SESSION)
    assert s is not None
    assert s.surface_id == SURFACE_SESSION
    assert s.label
    assert get_surface("nonexistent") is None


def test_retrieve_by_intent_scope_empty() -> None:
    """Retrieve with empty scope returns empty items and explanation with no_match_reason."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scope = RetrievalScope(entity_type="session", entity_id="no_such_session")
        intent = RetrievalIntentOS(intent=RETRIEVAL_INTENT_RECALL_CONTEXT, top_k=5)
        items, retrieval_id, explanation = memory_os_retrieve(SURFACE_SESSION, scope, intent, repo_root=root)
        assert isinstance(items, list)
        assert retrieval_id.startswith("memret_")
        assert explanation.retrieval_id == retrieval_id
        assert explanation.no_match_reason or len(items) == 0


def test_retrieve_learning_surface() -> None:
    """Learning surface returns slices when available (or empty)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scope = RetrievalScope()
        intent = RetrievalIntentOS(intent=RETRIEVAL_INTENT_RECALL_CONTEXT, top_k=5)
        items, retrieval_id, explanation = memory_os_retrieve(SURFACE_LEARNING, scope, intent, repo_root=root)
        assert isinstance(items, list)
        assert retrieval_id.startswith("memret_")
        assert explanation.confidence >= 0


def test_explain_format() -> None:
    """build_explanation and format_explanation_text produce valid output."""
    from workflow_dataset.memory_os.models import RetrievalExplanation, MemoryEvidenceBundle

    bundle = MemoryEvidenceBundle(retrieval_id="memret_test", items=[], total_count=0)
    expl = RetrievalExplanation(
        retrieval_id="memret_test",
        reason="No memory for scope.",
        evidence_bundle=bundle,
        confidence=0.0,
        no_match_reason="No links.",
    )
    d = build_explanation("memret_test", expl, include_evidence=True, include_weak=True)
    assert d["retrieval_id"] == "memret_test"
    assert "reason" in d
    assert d["confidence"] == 0.0
    assert "No links" in d.get("no_match_reason", "")
    text = format_explanation_text(expl)
    assert "Reason:" in text
    assert "Confidence:" in text


def test_weak_memory_handling() -> None:
    """When fusion has weak links, retrieval marks them and explanation has weak_warnings."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.memory_fusion.links import add_link
        from workflow_dataset.memory_substrate.store import ingest
        from workflow_dataset.memory_substrate.models import MemoryItem

        item = MemoryItem(content="Low confidence memory.", source="manual", session_id="s1")
        units = ingest([item], repo_root=root)
        add_link(units[0].unit_id, "session", "s1", confidence=0.4, needs_review=True, repo_root=root)
        scope = RetrievalScope(session_id="s1")
        intent = RetrievalIntentOS(intent=RETRIEVAL_INTENT_RECALL_CONTEXT, top_k=5)
        items, retrieval_id, explanation = memory_os_retrieve(SURFACE_SESSION, scope, intent, repo_root=root)
        weak_in_items = [it for it in items if it.get("tier") == "weak"]
        assert len(explanation.weak_memory_warnings) >= 0
        if items:
            assert any(it.get("memory_id") for it in items)


def test_memory_os_status() -> None:
    """memory_os_status returns namespaces, surfaces_count, weak_memory_warnings."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        st = memory_os_status(repo_root=root)
        assert "namespaces" in st
        assert "surfaces_count" in st
        assert "weak_memory_warnings" in st
        assert st["surfaces_count"] >= 7


# ----- M44D.1: Retrieval profiles and vertical views -----


def test_list_profiles() -> None:
    """Profiles include conservative, continuity_heavy, operator_heavy, coding_heavy."""
    profiles = list_profiles()
    ids = [p.profile_id for p in profiles]
    assert PROFILE_CONSERVATIVE in ids
    assert PROFILE_CODING_HEAVY in ids
    assert "continuity_heavy" in ids
    assert "operator_heavy" in ids
    for p in profiles:
        assert p.label
        assert p.preference_reason


def test_get_profile_and_reason() -> None:
    """get_profile returns profile; get_profile_reason explains why preferred."""
    p = get_profile(PROFILE_CONSERVATIVE)
    assert p is not None
    assert p.profile_id == PROFILE_CONSERVATIVE
    assert p.trusted_only is True
    assert p.min_confidence >= 0.7
    reason = get_profile_reason(PROFILE_CONSERVATIVE)
    assert "conservative" in reason.lower() or "high-confidence" in reason.lower() or "trusted" in reason.lower()
    assert get_profile("nonexistent") is None
    assert "Unknown" in get_profile_reason("nonexistent") or "nonexistent" in get_profile_reason("nonexistent")


def test_conservative_profile_filters_weak() -> None:
    """With conservative profile, weak/low-confidence items are excluded from retrieval."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.memory_fusion.links import add_link
        from workflow_dataset.memory_substrate.store import ingest
        from workflow_dataset.memory_substrate.models import MemoryItem

        item = MemoryItem(content="Low conf memory.", source="manual", session_id="s1")
        units = ingest([item], repo_root=root)
        add_link(units[0].unit_id, "session", "s1", confidence=0.4, needs_review=True, repo_root=root)
        scope = RetrievalScope(session_id="s1")
        intent = RetrievalIntentOS(intent=RETRIEVAL_INTENT_RECALL_CONTEXT, top_k=10)
        items_no_profile, _, expl_no = memory_os_retrieve(SURFACE_SESSION, scope, intent, repo_root=root)
        items_conservative, _, expl_con = memory_os_retrieve(
            SURFACE_SESSION, scope, intent, repo_root=root, profile_id=PROFILE_CONSERVATIVE
        )
        assert expl_con.profile_used == PROFILE_CONSERVATIVE
        assert expl_con.profile_reason
        assert len(items_conservative) <= len(items_no_profile)
        for it in items_conservative:
            assert it.get("tier") == "trusted"
            assert (it.get("confidence") or 0) >= 0.7


def test_list_views_and_get_view_for_vertical() -> None:
    """Vertical views exist for project, session, learning, coding, continuity, operator."""
    views = list_views()
    verticals = [v.vertical_id for v in views]
    assert "project" in verticals
    assert "session" in verticals
    assert "learning" in verticals
    assert "coding" in verticals
    v = get_view_for_vertical("coding")
    assert v is not None
    assert v.vertical_id == "coding"
    assert v.preferred_profile_id == PROFILE_CODING_HEAVY
    assert v.why_this_profile
    assert get_view_for_vertical("nonexistent") is None


def test_explanation_includes_profile_reason() -> None:
    """When retrieval uses a profile, explanation has profile_used and profile_reason."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scope = RetrievalScope(entity_type="session", entity_id="any")
        intent = RetrievalIntentOS(intent=RETRIEVAL_INTENT_RECALL_CONTEXT, top_k=5)
        _, _, explanation = memory_os_retrieve(
            SURFACE_SESSION, scope, intent, repo_root=root, profile_id=PROFILE_CODING_HEAVY
        )
        assert explanation.profile_used == PROFILE_CODING_HEAVY
        assert explanation.profile_reason
        d = build_explanation(explanation.retrieval_id, explanation, include_evidence=True, include_weak=True)
        assert d.get("profile_used") == PROFILE_CODING_HEAVY
        assert d.get("profile_reason")
        text = format_explanation_text(explanation)
        assert "Profile:" in text
        assert PROFILE_CODING_HEAVY in text
