"""
M43I–M43L: Memory substrate — list memory slices, resolve refs, Cursor bridge report.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.memory_substrate.models import MemorySliceSummary, MemoryBackedRef, MEMORY_SCOPE_EXPERIMENTAL
from workflow_dataset.memory_substrate.slices import list_memory_slices, get_memory_slice_refs
from workflow_dataset.memory_substrate.cursor_bridge import build_cursor_bridge_report


def test_list_memory_slices_empty(tmp_path):
    """With no experiments/slices/corrections, list can be empty or have only corrections aggregate."""
    slices = list_memory_slices(repo_root=tmp_path, limit=10)
    # May be empty or contain mem_corrections_recent if corrections dir exists
    assert isinstance(slices, list)
    for s in slices:
        assert isinstance(s, MemorySliceSummary)
        assert s.memory_slice_id
        assert s.source_type in ("learning_lab_experiment", "candidate_studio_slice", "corrections_set")


def test_get_memory_slice_refs_corrections_recent(tmp_path):
    """Resolve mem_corrections_recent returns MemoryBackedRef with correction_ids (maybe empty)."""
    refs = get_memory_slice_refs("mem_corrections_recent", repo_root=tmp_path)
    assert refs is not None
    assert refs.memory_slice_id == "mem_corrections_recent"
    assert isinstance(refs.correction_ids, list)
    assert refs.scope == MEMORY_SCOPE_EXPERIMENTAL


def test_get_memory_slice_refs_unknown_returns_none(tmp_path):
    """Unknown memory_slice_id returns None."""
    assert get_memory_slice_refs("mem_unknown_xyz", repo_root=tmp_path) is None


def test_cursor_bridge_report(tmp_path):
    """Cursor bridge report has repo_root, production_safe_paths, experimental_paths, usage_notes."""
    report = build_cursor_bridge_report(repo_root=tmp_path)
    assert "repo_root" in report
    assert "data_local" in report
    assert "production_safe_paths" in report
    assert "experimental_paths" in report
    assert "usage_notes" in report
    assert "cursor_bridge_version" in report
    assert isinstance(report["usage_notes"], list)
    assert len(report["usage_notes"]) >= 1


def test_create_experiment_from_memory_slice(tmp_path):
    """Create learning-lab experiment from mem_corrections_recent populates slice with memory_slice_id."""
    from workflow_dataset.learning_lab.memory_slices import create_experiment_from_memory_slice
    from workflow_dataset.learning_lab.store import get_experiment
    exp = create_experiment_from_memory_slice("mem_corrections_recent", repo_root=tmp_path)
    assert exp is not None
    assert exp.source_type == "memory_slice"
    assert exp.source_ref == "mem_corrections_recent"
    assert exp.local_slice is not None
    assert exp.local_slice.memory_slice_id == "mem_corrections_recent"
    loaded = get_experiment(exp.experiment_id, repo_root=tmp_path)
    assert loaded is not None
    assert loaded.local_slice and loaded.local_slice.memory_slice_id == "mem_corrections_recent"


def test_build_slice_from_memory_slice(tmp_path):
    """Candidate-model build_slice_from_memory_slice returns DatasetSlice with memory_slice_id and provenance."""
    from workflow_dataset.candidate_model_studio.dataset_slice import build_slice_from_memory_slice
    slice_obj = build_slice_from_memory_slice("cand_1", "mem_corrections_recent", repo_root=tmp_path)
    assert slice_obj.provenance_source == "memory_slice"
    assert slice_obj.memory_slice_id == "mem_corrections_recent"
    assert slice_obj.candidate_id == "cand_1"


# ----- M43A–M43D: Memory backbone (item, unit, backends, compression, retrieval) -----


def test_memory_ingest_and_retrieve(tmp_path):
    """Ingest MemoryItems then retrieve by query and by session."""
    from workflow_dataset.memory_substrate import (
        MemoryItem,
        ingest,
        retrieve_units,
        list_sessions,
        get_status,
    )
    from workflow_dataset.memory_substrate.models import RetrievalIntent

    items = [
        MemoryItem(
            content="We chose SQLite for the memory backend.",
            source="manual",
            session_id="s1",
            timestamp_utc="2025-03-16T12:00:00Z",
        ),
        MemoryItem(
            content="Meeting about compression pipeline with the team.",
            source="session",
            session_id="s1",
            timestamp_utc="2025-03-16T11:00:00Z",
        ),
    ]
    units = ingest(items, repo_root=tmp_path)
    assert len(units) == 2
    assert all(u.unit_id for u in units)
    assert units[0].lossless_restatement == items[0].content

    intent = RetrievalIntent(query="SQLite", top_k=5)
    out = retrieve_units(intent, repo_root=tmp_path)
    assert len(out) >= 1
    assert any("SQLite" in u.lossless_restatement for u in out)

    sessions = list_sessions(limit=10, repo_root=tmp_path)
    assert "s1" in sessions

    status = get_status(repo_root=tmp_path)
    assert status["backend_id"] == "sqlite"
    assert status["units_count"] == 2
    assert status["sessions_count"] == 1


def test_memory_backends_protocol(tmp_path):
    """In-memory backend satisfies store/list/search."""
    from workflow_dataset.memory_substrate.backends import InMemoryBackend
    from workflow_dataset.memory_substrate.models import CompressedMemoryUnit, MemorySessionLink

    be = InMemoryBackend()
    u = CompressedMemoryUnit(
        unit_id="mu_1",
        lossless_restatement="Test restatement",
        keywords=["test", "memory"],
        session_id="s1",
        source="test",
    )
    link = MemorySessionLink(link_id="ml_1", unit_id="mu_1", session_id="s1")
    be.store(u, link)
    assert be.get("mu_1") is not None
    assert be.get("mu_1").lossless_restatement == "Test restatement"
    assert len(be.list_units(session_id=None, limit=10)) == 1
    kw = be.search_keyword("memory", top_k=5, session_id=None)
    assert len(kw) == 1
    assert be.get_stats()["backend_id"] == "in_memory"


def test_compression_keywords():
    """compress_item extracts keywords from content."""
    from workflow_dataset.memory_substrate.compression import compress_item
    from workflow_dataset.memory_substrate.models import MemoryItem

    item = MemoryItem(content="User decided to use SQLite for durable storage.", source="manual", session_id="s1")
    unit = compress_item(item)
    assert unit.lossless_restatement == item.content
    assert "sqlite" in unit.keywords or "storage" in unit.keywords or "durable" in unit.keywords
    assert unit.session_id == "s1"


def test_simplemem_bridge_dict_roundtrip():
    """unit_to_simplemem_entry_dict and simplemem_entry_dict_to_unit roundtrip."""
    from workflow_dataset.memory_substrate.models import CompressedMemoryUnit
    from workflow_dataset.memory_substrate.simplemem_bridge import unit_to_simplemem_entry_dict, simplemem_entry_dict_to_unit

    u = CompressedMemoryUnit(
        unit_id="mu_x",
        lossless_restatement="Alice met Bob at Starbucks.",
        keywords=["alice", "bob", "starbucks"],
        timestamp="2025-03-16T14:00:00",
        session_id="s1",
        source="session",
    )
    d = unit_to_simplemem_entry_dict(u)
    assert d["entry_id"] == "mu_x"
    assert d["lossless_restatement"] == u.lossless_restatement
    u2 = simplemem_entry_dict_to_unit(d, session_id="s1", source="bridge")
    assert u2.unit_id == u.unit_id
    assert u2.lossless_restatement == u.lossless_restatement
    assert u2.session_id == "s1"
    assert u2.source == "bridge"
