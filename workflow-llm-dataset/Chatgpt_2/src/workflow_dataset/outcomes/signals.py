"""
M24N–M24Q: Improvement signals — job repeatedly fails, macro highly useful, recurring blocker, first-value flow weak.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.outcomes.patterns import repeated_block_patterns, repeated_success_patterns, most_useful_per_pack
from workflow_dataset.outcomes.store import load_outcome_history, list_session_outcomes


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def generate_improvement_signals(
    repo_root: Path | str | None = None,
    min_block_count: int = 2,
    min_success_count: int = 2,
) -> dict[str, Any]:
    """
    Generate explicit improvement signals from outcome history.
    Returns: job_fails_repeatedly, macro_or_job_highly_useful, recurring_blockers, first_value_flow_weak, signals_list.
    """
    root = _repo_root(repo_root)
    signals_list: list[dict[str, Any]] = []

    # Recurring blockers
    blocks = repeated_block_patterns(repo_root=root, min_occurrences=min_block_count, limit=30)
    recurring_blockers = [{"cause_code": b["cause_code"], "source_ref": b["source_ref"], "count": b["count"]} for b in blocks]
    for b in blocks:
        signals_list.append({
            "signal_type": "recurring_blocker",
            "title": f"Recurring block: {b['cause_code']}",
            "detail": f"source_ref={b['source_ref']} count={b['count']}",
            "ref": b["source_ref"],
            "priority": "high" if b["count"] >= 3 else "medium",
        })

    # Job/routine/macro repeatedly fails (same source_ref appears in blocked outcomes often)
    job_fails_repeatedly: list[dict[str, Any]] = []
    for b in blocks:
        if b["source_ref"] and b["cause_code"] in ("approval_missing", "job_not_found", "policy_denied", "path_scope_denied"):
            job_fails_repeatedly.append({"source_ref": b["source_ref"], "cause_code": b["cause_code"], "count": b["count"]})
            if not any(s["ref"] == b["source_ref"] and s.get("signal_type") == "job_fails_repeatedly" for s in signals_list):
                signals_list.append({
                    "signal_type": "job_fails_repeatedly",
                    "title": f"Job/routine repeatedly blocked: {b['source_ref']}",
                    "detail": f"cause={b['cause_code']} count={b['count']}",
                    "ref": b["source_ref"],
                    "priority": "high" if b["count"] >= 3 else "medium",
                })

    # Macro/job highly useful
    success_pats = repeated_success_patterns(repo_root=root, min_occurrences=min_success_count, limit=20)
    macro_or_job_highly_useful = [{"source_ref": s["source_ref"], "pack_id": s["pack_id"], "count": s["count"]} for s in success_pats]
    for s in success_pats[:10]:
        signals_list.append({
            "signal_type": "macro_or_job_highly_useful",
            "title": f"High value: {s['source_ref']}",
            "detail": f"pack_id={s['pack_id']} count={s['count']}",
            "ref": s["source_ref"],
            "priority": "medium",
        })

    # First-value flow weak: many sessions with blocked_count > 0 and disposition fix/pause
    history = load_outcome_history(root, limit=100)
    weak_flow_sessions = [e for e in history if e.get("blocked_count", 0) > 0 and e.get("disposition") in ("fix", "pause")]
    first_value_flow_weak = len(weak_flow_sessions) >= 2
    if first_value_flow_weak:
        signals_list.append({
            "signal_type": "first_value_flow_weak",
            "title": "First-value flow often blocked",
            "detail": f"{len(weak_flow_sessions)} sessions with blocks and disposition fix/pause",
            "ref": "",
            "priority": "medium",
        })

    return {
        "job_fails_repeatedly": job_fails_repeatedly,
        "macro_or_job_highly_useful": macro_or_job_highly_useful,
        "recurring_blockers": recurring_blockers,
        "first_value_flow_weak": first_value_flow_weak,
        "signals_list": signals_list,
    }
