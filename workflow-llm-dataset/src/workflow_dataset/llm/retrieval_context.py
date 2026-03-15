"""
Lightweight retrieval over corpus documents for context-augmented prompts.

BM25-like lexical or embedding-ready abstraction; no vector DB required for first pass.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from workflow_dataset.llm.corpus_builder import load_corpus
from workflow_dataset.llm.schemas import CorpusDocument


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
    docs = load_corpus(corpus_path, limit=max_docs)
    if source_filter:
        docs = [d for d in docs if d.source_type == source_filter]
    query_tokens = _tokenize(query)
    if not query_tokens:
        return docs[:top_k]
    scored = [(d, _bm25_like_score(query_tokens, d)) for d in docs]
    scored.sort(key=lambda x: -x[1])
    return [d for d, _ in scored[:top_k]]


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
