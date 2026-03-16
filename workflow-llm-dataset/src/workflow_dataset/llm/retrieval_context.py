"""
Lightweight retrieval over corpus documents for context-augmented prompts.

BM25-like lexical or embedding-ready abstraction; no vector DB required for first pass.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from workflow_dataset.llm.corpus_builder import load_corpus
from workflow_dataset.llm.schemas import CorpusDocument

# For narrow ops/reporting pilot: prefer workflow and task context over generic occupation/industry.
OPS_REPORTING_PREFERRED_SOURCE_TYPES = (
    "workflow_step",
    "work_context",
    "task",
    "detailed_work_activity",
)

# Query suffix to scope retrieval to ops/reporting: reporting, status, blockers, wins, next steps, project updates.
OPS_REPORTING_QUERY_SUFFIX = (
    " reporting status workflow weekly summary next steps blockers wins project updates operations"
)

# Score thresholds for relevance hint (max of top-k scores).
RELEVANCE_HIGH_MIN = 0.35
RELEVANCE_MIXED_MIN = 0.15


def _tokenize(text: str) -> list[str]:
    """Simple whitespace tokenization; lowercase."""
    return re.findall(r"\w+", text.lower())


def _bm25_like_score(query_tokens: list[str], doc: CorpusDocument) -> float:
    """Simple term overlap score (BM25-lite). No idf for minimal deps."""
    doc_tokens = set(_tokenize(doc.text)) | set(_tokenize(doc.title))
    if not doc_tokens:
        return 0.0
    overlap = sum(1 for t in query_tokens if t in doc_tokens)
    return overlap / max(len(query_tokens), 1) if query_tokens else 0.0


def retrieve(
    corpus_path: Path | str,
    query: str,
    top_k: int = 5,
    source_filter: str | None = None,
    max_docs: int = 5000,
) -> list[CorpusDocument]:
    """
    Retrieve top-k documents from corpus by lexical overlap with query.
    source_filter: optional source_type to restrict (e.g. occupation, workflow_step).
    """
    docs, _ = retrieve_with_scores(
        corpus_path, query, top_k=top_k, source_filter=source_filter, max_docs=max_docs
    )
    return docs


def retrieve_with_scores(
    corpus_path: Path | str,
    query: str,
    top_k: int = 5,
    source_filter: str | None = None,
    prefer_source_types: tuple[str, ...] | None = None,
    max_docs: int = 5000,
) -> tuple[list[CorpusDocument], list[float]]:
    """
    Retrieve top-k documents with scores. Optionally boost docs whose source_type
    is in prefer_source_types (e.g. ops/reporting: workflow_step, work_context, task).
    Returns (docs, scores) in descending score order.
    """
    docs = load_corpus(corpus_path, limit=max_docs)
    if source_filter:
        docs = [d for d in docs if d.source_type == source_filter]
    query_tokens = _tokenize(query)
    prefer_set = set(prefer_source_types or ())

    def score_one(d: CorpusDocument) -> float:
        s = _bm25_like_score(query_tokens, d)
        if prefer_set and d.source_type in prefer_set and s > 0:
            s = min(1.0, s * 1.5)
        return s

    if not query_tokens:
        return docs[:top_k], [0.0] * min(top_k, len(docs))
    scored = [(d, score_one(d)) for d in docs]
    scored.sort(key=lambda x: -x[1])
    top = scored[:top_k]
    return [d for d, _ in top], [s for _, s in top]


def relevance_hint_from_scores(scores: list[float]) -> str:
    """Classify retrieval relevance from top-k scores for operator and prompt clarity."""
    if not scores:
        return "weak"
    max_s = max(scores)
    if max_s >= RELEVANCE_HIGH_MIN:
        return "high"
    if max_s >= RELEVANCE_MIXED_MIN:
        return "mixed"
    return "weak"


def format_context_for_prompt(docs: list[CorpusDocument], max_chars: int = 2000) -> str:
    """Format retrieved docs as a single context string for injection into prompt."""
    parts: list[str] = []
    total = 0
    for d in docs:
        block = f"[{d.title}]\n{d.text}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n---\n\n".join(parts) if parts else ""
