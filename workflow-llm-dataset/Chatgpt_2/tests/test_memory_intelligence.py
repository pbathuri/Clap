"""
M44I–M44L: Tests for memory intelligence — models, retrieval, recommendations, explanation, no-memory behavior.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.memory_intelligence.models import (
    RetrievalGroundedRecommendation,
    RetrievedPriorCase,
    DecisionRationaleRecall,
    MemoryBackedNextStepSuggestion,
    MemoryBackedOperatorFlowHint,
    WeakMemoryCaution,
    MemoryToActionLinkage,
)
from workflow_dataset.memory_intelligence.retrieval import retrieve_for_context
from workflow_dataset.memory_intelligence.recommendations import build_memory_backed_recommendations
from workflow_dataset.memory_intelligence.explanation import (
    explain_recommendation,
    explain_prior_case_influence,
    list_weak_memory_cautions,
)
from workflow_dataset.memory_intelligence.store import (
    save_recommendation,
    load_recommendation,
    list_recent_recommendations,
)
from workflow_dataset.memory_intelligence.planner_enrichment import enrich_planning_sources
from workflow_dataset.memory_intelligence.continuity_enrichment import (
    get_resume_memory_context,
    get_next_session_memory_context,
)
from workflow_dataset.memory_intelligence.assist_enrichment import memory_backed_suggestions_for_context
from workflow_dataset.memory_intelligence.operator_context import get_memory_backed_operator_context


def test_models_to_dict() -> None:
    """Models serialize to dict with expected keys."""
    pc = RetrievedPriorCase(unit_id="u1", snippet="s", confidence=0.8)
    assert pc.to_dict()["unit_id"] == "u1"
    assert pc.to_dict()["confidence"] == 0.8

    rec = RetrievalGroundedRecommendation(
        recommendation_id="rec_1",
        kind="next_step",
        title="T",
        prior_cases=[pc],
        rationale_recall=[],
    )
    d = rec.to_dict()
    assert d["recommendation_id"] == "rec_1"
    assert len(d["prior_cases"]) == 1
    assert d["prior_cases"][0]["unit_id"] == "u1"


def test_retrieve_for_context_empty() -> None:
    """With no memory substrate data, retrieve returns empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = retrieve_for_context(project_id="p1", session_id=None, repo_root=root, limit=5)
        assert isinstance(out, list)
        assert len(out) == 0


def test_build_memory_backed_recommendations_no_memory() -> None:
    """When no relevant memory, recommendations list is empty."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        recs = build_memory_backed_recommendations(
            project_id="founder_case_alpha",
            session_id=None,
            repo_root=root,
            persist=False,
        )
        assert recs == []


def test_explain_recommendation_not_found() -> None:
    """Explain for missing id returns found=False."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = explain_recommendation("rec_nonexistent", repo_root=root)
        assert out["found"] is False
        assert out["recommendation_id"] == "rec_nonexistent"


def test_explain_prior_case_influence_not_found() -> None:
    """Prior-case influence for missing id returns found=False."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = explain_prior_case_influence("rec_nonexistent", repo_root=root)
        assert out["found"] is False
        assert out["prior_cases"] == []


def test_list_weak_memory_cautions_structure() -> None:
    """list_weak_memory_cautions returns dict with fusion and recommendations keys."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = list_weak_memory_cautions(limit=10, repo_root=root)
        assert "weak_memories_from_fusion" in out
        assert "weak_cautions_from_recommendations" in out
        assert isinstance(out["weak_memories_from_fusion"], list)
        assert isinstance(out["weak_cautions_from_recommendations"], list)


def test_planner_enrichment_adds_keys() -> None:
    """enrich_planning_sources adds memory_context and memory_prior_cases."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sources = {"session": None, "errors": []}
        out = enrich_planning_sources(sources, project_id="p1", repo_root=root)
        assert "memory_context" in out
        assert "memory_prior_cases" in out
        assert "summary" in out["memory_context"]
        assert isinstance(out["memory_prior_cases"], list)


def test_continuity_enrichment_returns_dict() -> None:
    """get_resume_memory_context and get_next_session_memory_context return dicts with prior_cases."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ctx = get_resume_memory_context(project_id="p1", session_ref="", repo_root=root)
        assert "prior_cases" in ctx
        assert "rationale_summary" in ctx
        ctx2 = get_next_session_memory_context(project_id="p1", repo_root=root)
        assert "prior_cases" in ctx2
        assert "rationale_summary" in ctx2


def test_store_save_load() -> None:
    """Save recommendation then load by id."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rec = RetrievalGroundedRecommendation(
            recommendation_id="rec_test_1",
            kind="next_step",
            title="Test",
            description="D",
            created_at_utc="2025-01-01T00:00:00",
        )
        save_recommendation(rec, repo_root=root)
        loaded = load_recommendation("rec_test_1", repo_root=root)
        assert loaded is not None
        assert loaded["recommendation_id"] == "rec_test_1"
        assert loaded["title"] == "Test"
        recent = list_recent_recommendations(limit=5, repo_root=root)
        assert len(recent) >= 1
        assert recent[0]["recommendation_id"] == "rec_test_1"


def test_no_relevant_memory_behavior() -> None:
    """Assist and operator context return safe defaults when no memory."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        suggestions = memory_backed_suggestions_for_context(project_id="p1", repo_root=root, max_suggestions=3)
        assert suggestions == []
        hint = get_memory_backed_operator_context(project_id="p1", responsibility_id="r1", repo_root=root)
        assert hint.responsibility_id == "r1"
        assert hint.hint_summary  # has a fallback string
        assert isinstance(hint.prior_cases, list)
        assert isinstance(hint.weak_cautions, list)


# ----- M44L.1: Memory-grounded playbooks + action packs -----


def test_memory_grounded_playbook_model_and_build() -> None:
    """Build memory-grounded playbook for a vertical; has reviewable and operator_guidance_from_memory."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.memory_intelligence import build_memory_grounded_playbook
        pb = build_memory_grounded_playbook("founder_operator_core", repo_root=root, persist=True)
        assert pb.playbook_id.startswith("mgp_")
        assert pb.curated_pack_id == "founder_operator_core"
        assert pb.reviewable is True
        assert "operator_guidance_from_memory" in pb.to_dict()
        assert "this_worked_before" in pb.to_dict()


def test_memory_grounded_playbook_store_list() -> None:
    """Save and list memory-grounded playbooks."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.memory_intelligence import build_memory_grounded_playbook
        from workflow_dataset.memory_intelligence.store import list_memory_grounded_playbooks, load_memory_grounded_playbook
        pb = build_memory_grounded_playbook("analyst_core", repo_root=root, persist=True)
        listed = list_memory_grounded_playbooks(repo_root=root)
        assert len(listed) >= 1
        loaded = load_memory_grounded_playbook(pb.playbook_id, repo_root=root)
        assert loaded is not None
        assert loaded["curated_pack_id"] == "analyst_core"


def test_memory_grounded_action_pack_model_and_build() -> None:
    """Build memory-grounded action pack; has actions and prior_successful_cases."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.memory_intelligence import build_memory_grounded_action_pack
        pack = build_memory_grounded_action_pack(project_id="founder_case_alpha", repo_root=root, persist=True)
        assert pack.action_pack_id.startswith("mgap_")
        assert pack.reviewable is True
        assert "actions" in pack.to_dict()
        assert "prior_successful_cases" in pack.to_dict()


def test_memory_grounded_action_pack_store_list() -> None:
    """Save and list memory-grounded action packs."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.memory_intelligence import build_memory_grounded_action_pack
        from workflow_dataset.memory_intelligence.store import list_memory_grounded_action_packs, load_memory_grounded_action_pack
        pack = build_memory_grounded_action_pack(project_id="proj_1", repo_root=root, persist=True)
        listed = list_memory_grounded_action_packs(project_id="proj_1", repo_root=root)
        assert len(listed) >= 1
        loaded = load_memory_grounded_action_pack(pack.action_pack_id, repo_root=root)
        assert loaded is not None
        assert loaded["project_id"] == "proj_1"
