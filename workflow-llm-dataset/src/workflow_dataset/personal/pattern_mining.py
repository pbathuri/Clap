"""
M31E–M31H: Routine and pattern mining — task sequences, file flows, session patterns, repeated blocks/success.
Bounded and explainable; no high confidence from weak evidence.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

# Cap confidence so weak evidence does not produce "strong" patterns
MAX_CONFIDENCE_FROM_WEAK = 0.6
MIN_OCCURRENCES_TASK_SEQUENCE = 2
MIN_OCCURRENCES_FILE_FLOW = 2
MIN_OCCURRENCES_SESSION_PATTERN = 2


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def task_sequence_patterns(
    repo_root: Path | str | None = None,
    min_occurrences: int = MIN_OCCURRENCES_TASK_SEQUENCE,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Repeated task sequences from session outcomes (order of source_ref in task_outcomes).
    Returns list of {sequence: [source_refs], count, confidence, supporting_signals, sample_session_ids}.
    """
    from workflow_dataset.outcomes.store import list_session_outcomes
    root = _repo_root(repo_root)
    sessions = list_session_outcomes(limit=200, repo_root=root)
    sequence_counts: Counter[tuple[str, ...]] = Counter()
    sequence_sessions: dict[tuple[str, ...], list[str]] = {}
    for so in sessions:
        refs = tuple(t.source_ref for t in so.task_outcomes if t.source_ref)
        if len(refs) < 2:
            continue
        sequence_counts[refs] += 1
        if refs not in sequence_sessions:
            sequence_sessions[refs] = []
        if so.session_id and so.session_id not in sequence_sessions[refs]:
            sequence_sessions[refs].append(so.session_id)
    out: list[dict[str, Any]] = []
    for seq, count in sequence_counts.most_common(limit):
        if count < min_occurrences:
            break
        confidence = min(MAX_CONFIDENCE_FROM_WEAK + 0.1 * (count - min_occurrences), 0.9)
        out.append({
            "pattern_type": "task_sequence",
            "sequence": list(seq),
            "count": count,
            "confidence": round(confidence, 2),
            "supporting_signals": [f"session_count={count}", f"length={len(seq)}"],
            "sample_session_ids": sequence_sessions.get(seq, [])[:5],
        })
    return out


def file_flow_patterns(
    events: list[Any],
    root_paths: list[Path] | None = None,
    min_occurrences: int = MIN_OCCURRENCES_FILE_FLOW,
    limit: int = 20,
    sequence_length: int = 3,
) -> list[dict[str, Any]]:
    """
    Repeated file/document flows: sequences of extensions (or path prefixes) in order of event time.
    events: list of file observation events (dict or ObservationEvent). root_paths for project inference.
    """
    from workflow_dataset.personal.routine_detector import _parse_file_events
    rows = _parse_file_events(events, root_paths)
    if not rows:
        return []
    rows_sorted = sorted(rows, key=lambda r: r.get("timestamp_utc") or "")
    ext_sequences: Counter[tuple[str, ...]] = Counter()
    for i in range(len(rows_sorted) - sequence_length + 1):
        window = rows_sorted[i : i + sequence_length]
        exts = tuple((r.get("extension") or "").strip().lower() or "_" for r in window)
        if len(set(exts)) < 2:
            continue
        ext_sequences[exts] += 1
    out: list[dict[str, Any]] = []
    for seq, count in ext_sequences.most_common(limit):
        if count < min_occurrences:
            break
        confidence = min(MAX_CONFIDENCE_FROM_WEAK + 0.05 * (count - min_occurrences), 0.85)
        out.append({
            "pattern_type": "file_flow",
            "sequence": list(seq),
            "count": count,
            "confidence": round(confidence, 2),
            "supporting_signals": [f"flow_count={count}", f"extensions={list(seq)}"],
        })
    return out


def session_shape_patterns(
    repo_root: Path | str | None = None,
    min_occurrences: int = MIN_OCCURRENCES_SESSION_PATTERN,
    limit: int = 15,
) -> list[dict[str, Any]]:
    """
    Repeated session "shapes": same set of job_ids or routine_ids across sessions.
    Returns list of {shape: {job_ids, routine_ids}, count, confidence, sample_session_ids}.
    """
    from workflow_dataset.outcomes.store import list_session_outcomes
    root = _repo_root(repo_root)
    sessions = list_session_outcomes(limit=200, repo_root=root)
    shape_counts: Counter[tuple[frozenset[str], frozenset[str]]] = Counter()
    shape_sessions: dict[tuple[frozenset[str], frozenset[str]], list[str]] = {}
    for so in sessions:
        job_refs = frozenset(t.source_ref for t in so.task_outcomes if t.source_type == "job_run" and t.source_ref)
        routine_refs = frozenset(t.source_ref for t in so.task_outcomes if t.source_type == "routine_run" and t.source_ref)
        key = (job_refs, routine_refs)
        if not job_refs and not routine_refs:
            continue
        shape_counts[key] += 1
        if key not in shape_sessions:
            shape_sessions[key] = []
        if so.session_id:
            shape_sessions[key].append(so.session_id)
    out: list[dict[str, Any]] = []
    for (jobs, routines), count in shape_counts.most_common(limit):
        if count < min_occurrences:
            break
        confidence = min(MAX_CONFIDENCE_FROM_WEAK + 0.1 * (count - min_occurrences), 0.85)
        out.append({
            "pattern_type": "session_shape",
            "shape": {"job_ids": list(jobs), "routine_ids": list(routines)},
            "count": count,
            "confidence": round(confidence, 2),
            "supporting_signals": [f"session_count={count}"],
            "sample_session_ids": shape_sessions.get((jobs, routines), [])[:5],
        })
    return out


def repeated_block_patterns_personal(
    repo_root: Path | str | None = None,
    min_occurrences: int = 2,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Repeated approval/block patterns from outcomes. Wraps outcomes.patterns.repeated_block_patterns with confidence."""
    from workflow_dataset.outcomes.patterns import repeated_block_patterns
    raw = repeated_block_patterns(repo_root=repo_root, min_occurrences=min_occurrences, limit=limit)
    out: list[dict[str, Any]] = []
    for p in raw:
        count = p.get("count", 0)
        confidence = min(MAX_CONFIDENCE_FROM_WEAK + 0.1 * (count - min_occurrences), 0.85)
        out.append({
            "pattern_type": "repeated_block",
            "cause_code": p.get("cause_code"),
            "source_ref": p.get("source_ref"),
            "count": count,
            "confidence": round(confidence, 2),
            "supporting_signals": [f"block_count={count}"],
            "sample_session_ids": p.get("sample_session_ids", []),
        })
    return out


def repeated_success_patterns_personal(
    repo_root: Path | str | None = None,
    min_occurrences: int = 2,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Repeated success/usefulness patterns. Wraps outcomes.patterns.repeated_success_patterns with confidence."""
    from workflow_dataset.outcomes.patterns import repeated_success_patterns
    raw = repeated_success_patterns(repo_root=repo_root, min_occurrences=min_occurrences, limit=limit)
    out: list[dict[str, Any]] = []
    for p in raw:
        count = p.get("count", 0)
        confidence = min(0.5 + 0.1 * (count - min_occurrences), 0.9)
        out.append({
            "pattern_type": "repeated_success",
            "source_ref": p.get("source_ref"),
            "pack_id": p.get("pack_id"),
            "count": count,
            "confidence": round(confidence, 2),
            "supporting_signals": [f"success_count={count}"],
        })
    return out


def all_routines_from_events(
    events: list[Any],
    root_paths: list[Path] | None = None,
) -> list[dict[str, Any]]:
    """File-based routines from events (delegate to routine_detector.detect_routines)."""
    from workflow_dataset.personal.routine_detector import detect_routines
    return detect_routines(events, root_paths=root_paths)


def all_patterns(
    repo_root: Path | str | None = None,
    events: list[Any] | None = None,
    root_paths: list[Path] | None = None,
    include_task_sequence: bool = True,
    include_file_flow: bool = True,
    include_session_shape: bool = True,
    include_blocks: bool = True,
    include_success: bool = True,
) -> list[dict[str, Any]]:
    """
    Aggregate patterns from all mining functions. events optional for file_flow; if None, file_flow is skipped.
    Returns flat list with pattern_type, confidence, supporting_signals in each.
    """
    out: list[dict[str, Any]] = []
    if include_task_sequence:
        out.extend(task_sequence_patterns(repo_root=repo_root))
    if include_file_flow and events:
        out.extend(file_flow_patterns(events, root_paths=root_paths))
    if include_session_shape:
        out.extend(session_shape_patterns(repo_root=repo_root))
    if include_blocks:
        out.extend(repeated_block_patterns_personal(repo_root=repo_root))
    if include_success:
        out.extend(repeated_success_patterns_personal(repo_root=repo_root))
    return sorted(out, key=lambda x: (-(x.get("confidence") or 0), -(x.get("count") or 0)))
