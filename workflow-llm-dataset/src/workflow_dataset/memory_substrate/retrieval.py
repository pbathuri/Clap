"""
M43B: Hybrid retrieval — keyword + structured. Optional semantic when backend supports it.
"""

from __future__ import annotations

from workflow_dataset.memory_substrate.models import CompressedMemoryUnit, MemoryStorageBackend, RetrievalIntent


def retrieve(
    backend: MemoryStorageBackend,
    intent: RetrievalIntent,
) -> list[CompressedMemoryUnit]:
    """
    Hybrid retrieval: keyword search + structured filter; merge and dedupe by unit_id.
    """
    seen: set[str] = set()
    out: list[CompressedMemoryUnit] = []

    if intent.query.strip():
        kw_results = backend.search_keyword(
            intent.query.strip(),
            top_k=intent.top_k,
            session_id=intent.session_id,
        )
        for u in kw_results:
            if u.unit_id not in seen:
                seen.add(u.unit_id)
                out.append(u)

    structured = backend.search_structured(
        session_id=intent.session_id,
        source=intent.source,
        limit=intent.top_k,
    )
    for u in structured:
        if u.unit_id not in seen:
            seen.add(u.unit_id)
            out.append(u)

    return out[: intent.top_k]
