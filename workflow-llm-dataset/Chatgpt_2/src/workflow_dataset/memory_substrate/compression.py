"""
M43B: Rule-based memory compression/synthesis. No LLM; local-first.
"""

from __future__ import annotations

import re
from typing import Any

from workflow_dataset.memory_substrate.models import MemoryItem, CompressedMemoryUnit

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_keywords(text: str, max_keywords: int = 15) -> list[str]:
    """Simple keyword extraction: alphanumeric tokens, drop short and stop-like."""
    stop = {"a", "an", "the", "is", "are", "was", "were", "to", "of", "in", "on", "at", "for", "and", "or", "it", "its", "this", "that"}
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        if len(t) < 2 or t in stop or t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= max_keywords:
            break
    return out


def compress_item(item: MemoryItem, unit_id: str | None = None) -> CompressedMemoryUnit:
    """Turn a single MemoryItem into a CompressedMemoryUnit (restatement = content, keywords extracted)."""
    uid = unit_id or stable_id("unit", item.item_id or item.content[:200], item.timestamp_utc, prefix="mu_")
    keywords = _extract_keywords(item.content)
    return CompressedMemoryUnit(
        unit_id=uid,
        lossless_restatement=item.content,
        keywords=keywords,
        timestamp=item.timestamp_utc,
        location=None,
        persons=[],
        entities=[],
        topic=None,
        session_id=item.session_id,
        source=item.source,
        source_ref=item.source_ref,
        created_at_utc=item.metadata.get("created_at_utc") or utc_now_iso(),
    )


def synthesize_units(units: list[CompressedMemoryUnit], max_merged: int = 5) -> list[CompressedMemoryUnit]:
    """
    Optional synthesis: merge units that share session and very similar keywords into one.
    Returns a new list; does not mutate. Keeps units that cannot be merged.
    """
    if len(units) <= 1:
        return list(units)
    out: list[CompressedMemoryUnit] = []
    used: set[str] = set()
    for u in units:
        if u.unit_id in used:
            continue
        group = [u]
        for v in units:
            if v.unit_id in used or v.unit_id == u.unit_id:
                continue
            if v.session_id != u.session_id:
                continue
            overlap = len(set(u.keywords) & set(v.keywords))
            if overlap >= max(1, min(len(u.keywords), len(v.keywords)) // 2):
                group.append(v)
                used.add(v.unit_id)
                if len(group) >= max_merged:
                    break
        if len(group) == 1:
            out.append(u)
            continue
        used.add(u.unit_id)
        merged_id = stable_id("merged", u.unit_id, str(len(group)), prefix="mu_")
        merged_restatement = " | ".join(g.lossless_restatement for g in group[:3])
        if len(group) > 3:
            merged_restatement += " ..."
        all_keywords: list[str] = []
        seen_kw: set[str] = set()
        for g in group:
            for kw in g.keywords:
                if kw not in seen_kw:
                    seen_kw.add(kw)
                    all_keywords.append(kw)
        out.append(CompressedMemoryUnit(
            unit_id=merged_id,
            lossless_restatement=merged_restatement,
            keywords=all_keywords[:20],
            timestamp=u.timestamp,
            location=u.location,
            persons=u.persons,
            entities=u.entities,
            topic=u.topic,
            session_id=u.session_id,
            source=u.source,
            source_ref=u.source_ref,
            created_at_utc=u.created_at_utc,
        ))
    return out
