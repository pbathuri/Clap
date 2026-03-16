"""Tests for retrieval_context: retrieve, retrieve_with_scores, relevance_hint_from_scores."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.llm.retrieval_context import (
    retrieve,
    retrieve_with_scores,
    relevance_hint_from_scores,
    OPS_REPORTING_PREFERRED_SOURCE_TYPES,
    RELEVANCE_HIGH_MIN,
    RELEVANCE_MIXED_MIN,
)
from workflow_dataset.llm.schemas import CorpusDocument


def _write_corpus(path: Path, docs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


def test_retrieve_backward_compat(tmp_path: Path) -> None:
    """retrieve() returns list[CorpusDocument] and delegates to retrieve_with_scores."""
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(corpus_path, [
        {"doc_id": "d1", "source_type": "occupation", "title": "Manager", "text": "reporting status workflow"},
        {"doc_id": "d2", "source_type": "workflow_step", "title": "Step", "text": "weekly summary next steps"},
    ])
    result = retrieve(corpus_path, "reporting workflow", top_k=2)
    assert len(result) == 2
    assert all(isinstance(d, CorpusDocument) for d in result)
    assert result[0].doc_id in ("d1", "d2")


def test_retrieve_with_scores_prefers_ops_sources(tmp_path: Path) -> None:
    """With prefer_source_types, workflow_step with overlap is boosted over occupation with same overlap."""
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(corpus_path, [
        {"doc_id": "occ1", "source_type": "occupation", "title": "Analyst", "text": "reporting"},
        {"doc_id": "wf1", "source_type": "workflow_step", "title": "Report", "text": "reporting status workflow weekly summary"},
    ])
    docs, scores = retrieve_with_scores(
        corpus_path,
        "reporting status workflow",
        top_k=2,
        prefer_source_types=OPS_REPORTING_PREFERRED_SOURCE_TYPES,
    )
    assert len(docs) == 2
    assert len(scores) == 2
    assert docs[0].source_type == "workflow_step"
    assert scores[0] > scores[1]


def test_relevance_hint_from_scores() -> None:
    assert relevance_hint_from_scores([]) == "weak"
    assert relevance_hint_from_scores([0.0]) == "weak"
    assert relevance_hint_from_scores([RELEVANCE_MIXED_MIN]) == "mixed"
    assert relevance_hint_from_scores([RELEVANCE_MIXED_MIN + 0.01]) == "mixed"
    assert relevance_hint_from_scores([RELEVANCE_HIGH_MIN]) == "high"
    assert relevance_hint_from_scores([0.5]) == "high"
    assert relevance_hint_from_scores([0.1, 0.05]) == "weak"
    assert relevance_hint_from_scores([0.2, 0.1]) == "mixed"
