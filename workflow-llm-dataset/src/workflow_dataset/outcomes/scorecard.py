"""
M24Q.1: Pack scorecards — per-pack usefulness, blockers, readiness, trusted-real suitability,
session reuse strength, and recommended improvement backlog.
Operator-readable; first-draft.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.outcomes.store import list_session_outcomes
from workflow_dataset.outcomes.patterns import most_useful_per_pack, repeated_block_patterns
from workflow_dataset.outcomes.signals import generate_improvement_signals
from workflow_dataset.outcomes.bridge import (
    pack_refinement_suggestions,
    next_run_recommendations,
    outcome_to_correction_suggestions,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _trusted_real_suitability_for_pack(pack_id: str, repo_root: Path) -> dict[str, Any]:
    """Count trusted_for_real vs simulate_only among pack's recommended jobs. Optional job_packs/value_packs."""
    out: dict[str, Any] = {"trusted_count": 0, "simulate_only_count": 0, "job_ids": [], "summary": "—"}
    try:
        from workflow_dataset.value_packs.registry import get_value_pack
        from workflow_dataset.job_packs import get_job_pack
        pack = get_value_pack(pack_id)
        if not pack or not pack.recommended_job_ids:
            out["summary"] = "no pack or no jobs"
            return out
        job_ids = list(pack.recommended_job_ids or [])[:20]
        out["job_ids"] = job_ids
        for jid in job_ids:
            job = get_job_pack(jid, repo_root)
            if not job:
                continue
            if job.trust_level in ("trusted_for_real", "approval_valid_for_scope") and job.real_mode_eligibility:
                out["trusted_count"] += 1
            elif job.trust_level == "simulate_only" or not job.real_mode_eligibility:
                out["simulate_only_count"] += 1
        total = out["trusted_count"] + out["simulate_only_count"]
        if total:
            out["summary"] = f"{out['trusted_count']} trusted_for_real, {out['simulate_only_count']} simulate_only"
        else:
            out["summary"] = "jobs not loaded"
    except Exception as e:
        out["summary"] = f"error: {e}"
    return out


def _readiness_proxy(repo_root: Path) -> dict[str, Any]:
    """Repo-level readiness proxy (rollout/acceptance). First-draft."""
    out: dict[str, Any] = {"demo_ready": False, "summary": "—"}
    try:
        from workflow_dataset.rollout.readiness import build_rollout_readiness_report
        r = build_rollout_readiness_report(repo_root)
        out["demo_ready"] = r.get("demo_ready", False)
        out["summary"] = "demo_ready" if out["demo_ready"] else "not demo_ready"
    except Exception as e:
        out["summary"] = f"error: {e}"
    return out


def build_pack_scorecard(
    pack_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build per-pack scorecard: usefulness, blockers, readiness, trusted_real_suitability,
    session_reuse_strength, improvement_backlog.
    """
    root = _repo_root(repo_root)
    sessions = list_session_outcomes(limit=100, repo_root=root, pack_id=pack_id)
    useful_per_pack = most_useful_per_pack(repo_root=root, top_n=10)
    pack_useful = [u for u in useful_per_pack if u.get("pack_id") == pack_id]
    blocks = repeated_block_patterns(repo_root=root, min_occurrences=1, limit=30)

    # Usefulness
    useful_count = sum(len(s.usefulness_confirmations) for s in sessions)
    useful_refs = [u.get("source_ref", "") for u in pack_useful if u.get("source_ref")]
    usefulness = {
        "total_confirmations": useful_count,
        "high_value_refs": useful_refs[:10],
        "summary": f"{useful_count} confirmations, {len(useful_refs)} high-value refs" if (useful_count or useful_refs) else "—",
    }

    # Blockers (from sessions for this pack + recurring patterns that mention pack's refs)
    try:
        from workflow_dataset.value_packs.registry import get_value_pack
        pack = get_value_pack(pack_id)
        pack_refs = set((pack.recommended_job_ids or []) + (pack.recommended_routine_ids or []) + (pack.recommended_macro_ids or [])) if pack else set()
    except Exception:
        pack_refs = set()
    blocked_causes_flat = []
    for s in sessions:
        for b in s.blocked_causes:
            blocked_causes_flat.append({"cause_code": b.cause_code, "source_ref": b.source_ref})
    pack_blockers = [b for b in blocks if (not pack_refs) or (b.get("source_ref") in pack_refs)] if blocks else []
    blockers = {
        "session_block_count": sum(len(s.blocked_causes) for s in sessions),
        "recurring_causes": [b.get("cause_code") for b in pack_blockers[:10]],
        "recurring_detail": [{"cause_code": b.get("cause_code"), "source_ref": b.get("source_ref"), "count": b.get("count")} for b in pack_blockers[:5]],
        "summary": f"{sum(len(s.blocked_causes) for s in sessions)} in sessions, {len(pack_blockers)} recurring patterns" if (sessions or pack_blockers) else "—",
    }

    # Readiness (repo-level proxy)
    readiness = _readiness_proxy(root)

    # Trusted-real suitability
    trusted_real = _trusted_real_suitability_for_pack(pack_id, root)

    # Session reuse strength
    complete_count = sum(1 for s in sessions if (s.disposition or "").lower() == "complete")
    fix_pause_count = sum(1 for s in sessions if (s.disposition or "").lower() in ("fix", "pause"))
    session_reuse_strength = {
        "sessions_count": len(sessions),
        "complete_count": complete_count,
        "fix_pause_count": fix_pause_count,
        "ratio_complete": (complete_count / len(sessions)) if sessions else 0.0,
        "summary": f"{len(sessions)} sessions, {complete_count} complete, {fix_pause_count} fix/pause" if sessions else "—",
    }

    # Improvement backlog (pack-scoped)
    refinement = pack_refinement_suggestions(repo_root=root, pack_id=pack_id)
    next_recs = next_run_recommendations(repo_root=root, pack_id=pack_id)
    correction_sug = outcome_to_correction_suggestions(repo_root=root, limit=5)
    correction_sug = [c for c in correction_sug if pack_refs and c.get("source_ref") in pack_refs] if pack_refs else correction_sug[:3]
    improvement_backlog: list[dict[str, Any]] = []
    for r in refinement:
        improvement_backlog.append({"kind": r.get("kind", ""), "title": r.get("detail", r.get("source_ref", "")), "priority": "medium", "detail": r.get("detail", "")})
    for n in next_recs:
        improvement_backlog.append({"kind": n.get("kind", ""), "title": n.get("title", ""), "priority": "high" if n.get("kind") == "resolve_before_retry" else "medium", "detail": n.get("detail", "")})
    for c in correction_sug:
        improvement_backlog.append({"kind": "correction_suggested", "title": c.get("reason", ""), "priority": "medium", "detail": c.get("action", "")})

    return {
        "pack_id": pack_id,
        "usefulness": usefulness,
        "blockers": blockers,
        "readiness": readiness,
        "trusted_real_suitability": trusted_real,
        "session_reuse_strength": session_reuse_strength,
        "improvement_backlog": improvement_backlog[:20],
    }


def build_improvement_backlog(
    repo_root: Path | str | None = None,
    pack_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Build operator-readable improvement backlog. If pack_id given, filter to that pack.
    Each item: pack_id, kind, title, priority, detail.
    """
    root = _repo_root(repo_root)
    backlog: list[dict[str, Any]] = []
    signals = generate_improvement_signals(repo_root=root)
    for s in signals.get("signals_list", [])[:25]:
        ref = s.get("ref", "")
        kind = s.get("signal_type", "")
        title = s.get("title", "")
        priority = s.get("priority", "medium")
        if pack_id:
            # Infer pack from macro_or_job_highly_useful or recurring_blocker (we don't have pack in signal; include all and let caller filter, or add pack from success_pats)
            pass
        backlog.append({
            "pack_id": "",  # signals don't carry pack_id for all types
            "kind": kind,
            "title": title,
            "priority": priority,
            "detail": s.get("detail", ""),
        })
    # Add pack-scoped items from next_run and pack_refinement
    for pack_id_val in ([pack_id] if pack_id else []):
        recs = next_run_recommendations(repo_root=root, pack_id=pack_id_val)
        for r in recs:
            backlog.append({
                "pack_id": pack_id_val or "",
                "kind": r.get("kind", ""),
                "title": r.get("title", ""),
                "priority": "high" if r.get("kind") == "resolve_before_retry" else "medium",
                "detail": r.get("detail", ""),
            })
        refs = pack_refinement_suggestions(repo_root=root, pack_id=pack_id_val)
        for ref in refs:
            backlog.append({
                "pack_id": pack_id_val or "",
                "kind": ref.get("kind", ""),
                "title": ref.get("detail", ref.get("source_ref", "")),
                "priority": "medium",
                "detail": ref.get("detail", ""),
            })
    if not pack_id:
        # Global: add next_run and refinement for all packs we have in outcomes
        from workflow_dataset.outcomes.store import load_outcome_history
        history = load_outcome_history(root, limit=100)
        pack_ids = list(dict.fromkeys(e.get("pack_id") for e in history if e.get("pack_id")))
        for pid in pack_ids[:5]:
            if not pid or pid == "_unknown":
                continue
            recs = next_run_recommendations(repo_root=root, pack_id=pid)
            for r in recs[:2]:
                backlog.append({
                    "pack_id": pid,
                    "kind": r.get("kind", ""),
                    "title": r.get("title", ""),
                    "priority": "high" if r.get("kind") == "resolve_before_retry" else "medium",
                    "detail": r.get("detail", ""),
                })
    return backlog[:40]
