"""Tests for LLM corpus builder: deterministic docs from fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.llm.corpus_builder import (
    build_corpus,
    load_corpus,
    chunk_document,
)
from workflow_dataset.llm.schemas import CorpusDocument


@pytest.fixture
def processed_dir_with_occupations(tmp_path: Path) -> Path:
    """Minimal processed dir with one parquet table (occupations)."""
    import pandas as pd
    out = tmp_path / "processed"
    out.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([
        {"occupation_id": "11-1011.00", "title": "Chief Executives", "description": "Plan and direct organizations."},
    ])
    df.to_parquet(out / "occupations.parquet", index=False)
    return out


def test_build_corpus_produces_non_empty_deterministic_docs(
    processed_dir_with_occupations: Path,
    tmp_path: Path,
) -> None:
    out = tmp_path / "corpus.jsonl"
    total, counts = build_corpus(processed_dir_with_occupations, out)
    assert total >= 1
    assert "occupation" in counts
    assert counts["occupation"] >= 1
    assert out.exists()
    docs = load_corpus(out)
    assert len(docs) == total
    for d in docs:
        assert isinstance(d, CorpusDocument)
        assert d.doc_id
        assert d.source_type
        assert d.text


def test_build_corpus_empty_processed_dir(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "corpus.jsonl"
    total, counts = build_corpus(empty, out)
    assert total == 0
    assert out.exists()
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 0


def test_load_corpus_respects_limit(tmp_path: Path) -> None:
    out = tmp_path / "corpus.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    for i in range(5):
        doc = CorpusDocument(
            doc_id=f"id-{i}",
            source_type="test",
            title=f"Title {i}",
            text=f"Text {i}",
            metadata={},
            provenance={},
        )
        with open(out, "a", encoding="utf-8") as f:
            f.write(doc.model_dump_json() + "\n")
    loaded = load_corpus(out, limit=2)
    assert len(loaded) == 2


def test_chunk_document_bounds_size() -> None:
    doc = CorpusDocument(
        doc_id="big",
        source_type="test",
        title="Big",
        text="word " * 500,
        metadata={},
        provenance={},
    )
    chunks = chunk_document(doc, max_chars=200)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c.text) <= 250  # max_chars + small slack
