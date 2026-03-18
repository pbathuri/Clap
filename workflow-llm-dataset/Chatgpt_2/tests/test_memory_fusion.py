"""
M43E–M43H: Tests for memory fusion — links, substrate stub, live context integration, continuity, review.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.memory_fusion.links import (
    add_link,
    get_links_for_entity,
    get_memory_ids_for_entity,
    list_memory_links,
)
from workflow_dataset.memory_fusion.substrate import get_memory_substrate, StubMemorySubstrate
from workflow_dataset.memory_fusion.live_context_integration import (
    get_memory_context_for_live_context,
    explain_live_context_memory,
)
from workflow_dataset.memory_fusion.continuity_integration import get_memory_context_for_continuity
from workflow_dataset.memory_fusion.review import list_weak_memories


def test_substrate_stub_returns_empty() -> None:
    """With empty repo_root, substrate returns no results (stub or real adapter with no data)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sub = get_memory_substrate(repo_root=root)
        assert sub is not None
        results = sub.retrieve(project_id="p1", session_id="s1", limit=5)
        assert results == []


def test_links_add_and_get() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        add_link("mem_1", "project", "proj_alpha", confidence=0.9, repo_root=root)
        add_link("mem_1", "session", "sess_1", confidence=0.8, repo_root=root)
        add_link("mem_2", "project", "proj_alpha", needs_review=True, repo_root=root)
        links = get_links_for_entity("project", "proj_alpha", repo_root=root)
        assert len(links) == 2
        ids = get_memory_ids_for_entity("project", "proj_alpha", repo_root=root)
        assert "mem_1" in ids and "mem_2" in ids
        listed = list_memory_links(limit=10, repo_root=root)
        assert len(listed) >= 2


def test_live_context_integration_empty() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ctx = get_memory_context_for_live_context("p1", "s1", repo_root=root)
        assert ctx["project_id"] == "p1"
        assert ctx["session_id"] == "s1"
        assert ctx["snippets"] == []
        assert "source" in ctx


def test_explain_live_context_memory() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        expl = explain_live_context_memory("p1", "s1", repo_root=root)
        assert "memory_links_to_project" in expl
        assert "explanation" in expl


def test_continuity_integration_empty() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ctx = get_memory_context_for_continuity("p1", "s1", repo_root=root)
        assert ctx["project_id"] == "p1"
        assert ctx["has_memory_context"] is False
        assert "rationale_line" in ctx


def test_continuity_integration_with_links() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        add_link("m1", "project", "p1", repo_root=root)
        ctx = get_memory_context_for_continuity("p1", "", repo_root=root)
        # Stub returns no snippets, but we have links
        assert ctx["project_id"] == "p1"


def test_list_weak_memories() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        add_link("m_low", "project", "p1", confidence=0.3, repo_root=root)
        add_link("m_review", "session", "s1", needs_review=True, repo_root=root)
        weak = list_weak_memories(confidence_below=0.6, repo_root=root)
        assert len(weak) >= 1
        weak_review = list_weak_memories(needs_review_only=True, repo_root=root)
        assert any(w.get("needs_review") for w in weak_review)


def test_pane1_pane2_integration_substrate_to_live_context() -> None:
    """Ingest via substrate (Pane 1), link session (Pane 2), then get_memory_context returns snippets."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.memory_substrate import ingest
        from workflow_dataset.memory_substrate.models import MemoryItem

        item = MemoryItem(
            content="We use SQLite for the memory backend in this project.",
            source="manual",
            session_id="sess_live",
            timestamp_utc="2025-03-16T12:00:00Z",
        )
        units = ingest([item], repo_root=root)
        assert len(units) == 1
        add_link(units[0].unit_id, "session", "sess_live", repo_root=root)

        ctx = get_memory_context_for_live_context("", "sess_live", limit=5, repo_root=root)
        assert ctx["session_id"] == "sess_live"
        assert len(ctx["snippets"]) >= 1
        assert any("SQLite" in s.get("text", "") for s in ctx["snippets"])
