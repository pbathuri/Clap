"""
M44E–M44H Phase B: Summarization and compression — rollups with provenance.
Compress repeated event streams, session histories, operator patterns, workflow episode chains.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_curation.models import SummarizedMemoryUnit, CompressionCandidate

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
        return datetime.now(timezone.utc).isoformat()


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def summarize_repeated_events(
    unit_ids: list[str],
    session_ids: list[str],
    summary_text: str,
    source_kind: str = "repeated_events",
    repo_root: Path | str | None = None,
) -> SummarizedMemoryUnit:
    """Produce one summarized unit from repeated event unit ids; preserve provenance."""
    summary_id = stable_id("sum", "repeated", utc_now_iso(), prefix="sum_")
    return SummarizedMemoryUnit(
        summary_id=summary_id,
        summary_text=summary_text,
        source_unit_ids=list(unit_ids),
        source_session_ids=list(session_ids),
        source_kind=source_kind,
        created_at_utc=utc_now_iso(),
        keyword_tags=[],
    )


def summarize_session_history(
    session_id: str,
    unit_ids: list[str],
    summary_text: str,
    repo_root: Path | str | None = None,
) -> SummarizedMemoryUnit:
    """Summarize a session's memory units into one rollup."""
    summary_id = stable_id("sum", "session", session_id, utc_now_iso(), prefix="sum_")
    return SummarizedMemoryUnit(
        summary_id=summary_id,
        summary_text=summary_text,
        source_unit_ids=list(unit_ids),
        source_session_ids=[session_id],
        source_kind="session_history",
        created_at_utc=utc_now_iso(),
        keyword_tags=[],
    )


def summarize_operator_pattern(
    unit_ids: list[str],
    session_ids: list[str],
    summary_text: str,
    repo_root: Path | str | None = None,
) -> SummarizedMemoryUnit:
    """Summarize repeated operator pattern (e.g. same routine, same correction type)."""
    summary_id = stable_id("sum", "pattern", utc_now_iso(), prefix="sum_")
    return SummarizedMemoryUnit(
        summary_id=summary_id,
        summary_text=summary_text,
        source_unit_ids=list(unit_ids),
        source_session_ids=list(session_ids),
        source_kind="operator_pattern",
        created_at_utc=utc_now_iso(),
        keyword_tags=[],
    )


def summarize_episode_chain(
    episode_refs: list[str],
    unit_ids: list[str],
    summary_text: str,
    repo_root: Path | str | None = None,
) -> SummarizedMemoryUnit:
    """Summarize a chain of workflow episodes into one rollup."""
    summary_id = stable_id("sum", "episode_chain", utc_now_iso(), prefix="sum_")
    return SummarizedMemoryUnit(
        summary_id=summary_id,
        summary_text=summary_text,
        source_unit_ids=list(unit_ids),
        source_session_ids=[],  # episode refs stored in summary_text or metadata if needed
        source_kind="episode_chain",
        created_at_utc=utc_now_iso(),
        keyword_tags=episode_refs[:10],
    )


def build_compression_candidates_from_sessions(
    repo_root: Path | str | None = None,
    max_age_days: int = 30,
    min_units: int = 3,
    limit: int = 20,
) -> list[CompressionCandidate]:
    """
    Scan memory substrate (or outcome history) for session chunks that are good compression candidates.
    Returns candidates (unit_ids, session_ids, reason); does not apply compression.
    """
    root = _root(repo_root)
    candidates: list[CompressionCandidate] = []
    try:
        from workflow_dataset.outcomes.store import load_outcome_history
        # Use outcome history as a proxy for "sessions with activity" to form candidates
        history = load_outcome_history(repo_root=root, limit=200)
        if len(history) >= min_units:
            # Group by session_id and take older sessions
            by_session: dict[str, list[dict[str, Any]]] = {}
            for e in history:
                sid = e.get("session_id") or "_unknown"
                by_session.setdefault(sid, []).append(e)
            for sid, entries in list(by_session.items())[:limit]:
                if len(entries) < min_units:
                    continue
                unit_ids = [e.get("session_id", "") + "_" + str(e.get("timestamp", "")) for e in entries[:50]]
                cid = stable_id("comp", "session", sid, prefix="comp_")
                candidates.append(CompressionCandidate(
                    candidate_id=cid,
                    unit_ids=unit_ids[:30],
                    session_ids=[sid],
                    reason="session_history",
                    item_count=len(entries),
                    created_at_utc=utc_now_iso(),
                ))
    except Exception:
        pass
    return candidates[:limit]
