"""
M24N–M24Q: Pattern detection — repeated block patterns, repeated success patterns, most useful per pack.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from workflow_dataset.outcomes.store import list_session_outcomes, load_outcome_history


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def repeated_block_patterns(
    repo_root: Path | str | None = None,
    min_occurrences: int = 2,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return patterns of repeated blocks: cause_code, source_ref, count, sample_session_ids."""
    history = load_outcome_history(repo_root, limit=500)
    cause_ref_counts: Counter[tuple[str, str]] = Counter()
    cause_ref_sessions: dict[tuple[str, str], list[str]] = {}
    for e in history:
        for cause in e.get("blocked_causes", []):
            ref = e.get("source_refs", [])
            key_ref = ref[0] if ref else ""
            key = (cause, key_ref)
            cause_ref_counts[key] += 1
            if key not in cause_ref_sessions:
                cause_ref_sessions[key] = []
            if e.get("session_id") and e["session_id"] not in cause_ref_sessions[key]:
                cause_ref_sessions[key].append(e["session_id"])
    out: list[dict[str, Any]] = []
    for (cause_code, source_ref), count in cause_ref_counts.most_common(limit):
        if count < min_occurrences:
            break
        out.append({
            "cause_code": cause_code,
            "source_ref": source_ref,
            "count": count,
            "sample_session_ids": cause_ref_sessions.get((cause_code, source_ref), [])[:5],
        })
    return out


def repeated_success_patterns(
    repo_root: Path | str | None = None,
    min_occurrences: int = 2,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return patterns of repeated usefulness/success: source_ref (job/macro/routine), count, pack_id."""
    sessions = list_session_outcomes(limit=200, repo_root=repo_root)
    ref_pack_counts: Counter[tuple[str, str]] = Counter()
    for so in sessions:
        for u in so.usefulness_confirmations:
            if u.source_ref and (u.usefulness_score >= 3 or u.operator_confirmed):
                key = (u.source_ref, so.pack_id or "")
                ref_pack_counts[key] += 1
        for t in so.task_outcomes:
            if t.outcome_kind == "success" and t.source_ref:
                key = (t.source_ref, so.pack_id or "")
                ref_pack_counts[key] += 1
    out: list[dict[str, Any]] = []
    for (source_ref, pack_id), count in ref_pack_counts.most_common(limit):
        if count < min_occurrences:
            break
        out.append({"source_ref": source_ref, "pack_id": pack_id, "count": count})
    return out


def most_useful_per_pack(
    repo_root: Path | str | None = None,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """For each pack, return most useful job/routine/macro refs by usefulness count."""
    sessions = list_session_outcomes(limit=200, repo_root=repo_root)
    pack_ref_scores: dict[str, Counter[str]] = {}
    for so in sessions:
        pack = so.pack_id or "_unknown"
        if pack not in pack_ref_scores:
            pack_ref_scores[pack] = Counter()
        for u in so.usefulness_confirmations:
            if u.source_ref:
                score = u.usefulness_score if u.usefulness_score else (2 if u.operator_confirmed else 1)
                pack_ref_scores[pack][u.source_ref] += score
        for t in so.task_outcomes:
            if t.outcome_kind == "success" and t.source_ref:
                pack_ref_scores[pack][t.source_ref] += 1
    out: list[dict[str, Any]] = []
    for pack, counter in pack_ref_scores.items():
        for ref, score in counter.most_common(top_n):
            out.append({"pack_id": pack, "source_ref": ref, "score": score})
    return out
