"""Tests for personal corpus from setup and style/imitation modules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.llm.corpus_builder import (
    build_personal_corpus_from_setup,
    build_personal_corpus_from_setup_full,
    load_corpus,
)
from workflow_dataset.parse.document_models import ParsedDocument
from workflow_dataset.personal.style_profiles import (
    StyleProfile,
    aggregate_naming_style,
    save_style_profile,
    load_style_profiles,
)
from workflow_dataset.personal.imitation_candidates import (
    ImitationCandidate,
    collect_candidates_from_profiles,
    save_imitation_candidates,
)


def test_build_personal_corpus_from_setup(tmp_path: Path) -> None:
    """Personal corpus can be built from parsed artifacts dir."""
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    doc = ParsedDocument(
        source_path="/fake/path/doc.txt",
        artifact_family="text_document",
        title="My Doc",
        summary="A short summary.",
        raw_text_snippet="Optional content when allowed.",
    )
    (parsed_dir / "p_abc.json").write_text(doc.model_dump_json())
    out_path = tmp_path / "personal.jsonl"
    total, counts = build_personal_corpus_from_setup(parsed_dir, out_path, allow_raw_text=False)
    assert total == 1
    assert out_path.exists()
    docs = load_corpus(out_path)
    assert len(docs) == 1
    assert "personal_text_document" in counts
    assert "Summary" in docs[0].text


def test_build_personal_corpus_with_raw_text(tmp_path: Path) -> None:
    """When allow_raw_text=True, content includes raw_text_snippet."""
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    doc = ParsedDocument(
        source_path="/fake/path/doc.txt",
        artifact_family="text_document",
        title="Doc",
        summary="Summary.",
        raw_text_snippet="Full content here.",
    )
    (parsed_dir / "p_xyz.json").write_text(doc.model_dump_json())
    out_path = tmp_path / "personal_raw.jsonl"
    build_personal_corpus_from_setup(parsed_dir, out_path, allow_raw_text=True)
    docs = load_corpus(out_path)
    assert len(docs) == 1
    assert "Full content here" in docs[0].text


def test_build_personal_corpus_from_setup_full(tmp_path: Path) -> None:
    """Full personal corpus includes parsed artifacts, style signals, and session summary."""
    from workflow_dataset.setup.style_persistence import persist_style_signals
    session_id = "sess_full"
    parsed_base = tmp_path / "parsed"
    (parsed_base / session_id).mkdir(parents=True)
    doc = ParsedDocument(
        source_path="/fake/proj/report.txt",
        artifact_family="text_document",
        title="Report",
        summary="A report summary.",
    )
    (parsed_base / session_id / "p1.json").write_text(doc.model_dump_json())
    style_dir = tmp_path / "style_signals"
    persist_style_signals(session_id, [{"pattern_type": "naming", "value": "snake", "description": "Snake case"}], style_dir)
    out_dir = tmp_path / "corpus_out"
    total, counts = build_personal_corpus_from_setup_full(
        str(parsed_base), str(style_dir), session_id, str(out_dir),
        allow_raw_text=False, include_style_signals=True, include_session_summary=True,
    )
    assert total >= 2  # at least one artifact doc + one style doc + session summary
    assert (out_dir / "personal_corpus.jsonl").exists()
    docs = load_corpus(out_dir / "personal_corpus.jsonl")
    source_types = {d.source_type for d in docs}
    assert "personal_text_document" in source_types or "personal_style_signature" in source_types
    assert "personal_session_summary" in source_types


def test_style_profile_aggregate_and_save(tmp_path: Path) -> None:
    """Style profiles can be aggregated and saved."""
    signals = [
        {"pattern_type": "revision_naming", "value": "v1", "domain": "creative"},
        {"pattern_type": "revision_naming", "value": "v2", "domain": "creative"},
    ]
    profile = aggregate_naming_style(signals)
    assert profile is not None
    assert profile.profile_type == "naming_style"
    assert profile.evidence_count == 2
    path = save_style_profile(profile, tmp_path)
    assert path.exists()
    loaded = load_style_profiles(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].profile_id == profile.profile_id


def test_imitation_candidates_from_profiles(tmp_path: Path) -> None:
    """Imitation candidates can be collected from style profiles."""
    profile = StyleProfile(
        profile_id="profile_abc",
        profile_type="naming_style",
        domain="creative",
        evidence_count=3,
        signals=[],
        confidence=0.8,
    )
    save_style_profile(profile, tmp_path)
    candidates = collect_candidates_from_profiles(tmp_path)
    assert len(candidates) >= 1
    assert candidates[0].domain == "creative"
