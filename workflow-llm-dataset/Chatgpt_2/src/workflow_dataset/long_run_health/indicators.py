"""
M46A–M46D: Build subsystem health indicators from mission_control state (read-only).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.long_run_health.models import (
    SubsystemHealthSignal,
    OperatorBurdenIndicator,
    MemoryQualityIndicator,
    RoutingQualityIndicator,
    ExecutionReliabilityIndicator,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def operator_burden_from_state(state: dict[str, Any]) -> OperatorBurdenIndicator:
    """Derive operator burden from mission_control state."""
    ae = state.get("adaptive_execution_state") or {}
    sc = state.get("supervisory_control_state") or {}
    tr = state.get("triage", state.get("triage_state")) or {}
    awaiting = ae.get("awaiting_takeover_count", 0) or 0
    taken_over = sc.get("taken_over_count", 0) or 0
    paused = sc.get("paused_loops_count", 0) or 0
    open_issues = tr.get("open_issue_count", tr.get("open_issues", 0)) or 0
    if isinstance(open_issues, list):
        open_issues = len(open_issues)
    total = awaiting + taken_over + paused + open_issues
    summary = f"awaiting_takeover={awaiting} taken_over={taken_over} paused={paused} triage_open={open_issues}"
    return OperatorBurdenIndicator(
        review_count=open_issues,
        takeover_count=taken_over + awaiting,
        triage_open_count=open_issues,
        summary=summary,
        trend="increasing" if total > 3 else "stable",
    )


def memory_quality_from_state(state: dict[str, Any]) -> MemoryQualityIndicator:
    """Derive memory/retrieval quality from mission_control state."""
    mi = state.get("memory_intelligence", state.get("memory_intelligence_state")) or {}
    recs = mi.get("memory_backed_recommendation_count", 0) or 0
    weak = mi.get("weak_memory_caution_count", 0) or 0
    score = 0.7 - (weak * 0.1) + (min(recs, 5) * 0.02) if recs else 0.5
    score = max(0.0, min(1.0, score))
    return MemoryQualityIndicator(
        recommendation_count=recs,
        weak_caution_count=weak,
        usefulness_summary=f"recommendations={recs} weak_cautions={weak}",
        score=round(score, 2),
    )


def routing_quality_from_state(state: dict[str, Any]) -> RoutingQualityIndicator:
    """Derive routing quality from evaluation/runtime state."""
    ev = state.get("evaluation_state") or {}
    rec = (ev.get("recommendation") or "").lower()
    score = 0.8 if rec == "promote" else (0.5 if rec == "hold" else 0.6)
    return RoutingQualityIndicator(
        summary=f"eval_recommendation={rec or 'unknown'}",
        score=score,
        fallback_used="revert" in rec or "rollback" in rec,
    )


def execution_reliability_from_state(state: dict[str, Any]) -> ExecutionReliabilityIndicator:
    """Derive execution reliability from adaptive/shadow/supervisory state."""
    ae = state.get("adaptive_execution_state") or {}
    sh = state.get("shadow_execution_state") or {}
    running = ae.get("running_loop_count", 0) or 0
    awaiting = ae.get("awaiting_takeover_count", 0) or 0
    takeover_candidates = sh.get("forced_takeover_candidate_count", 0) or 0
    failed = awaiting + takeover_candidates
    total = running + failed
    score = (running / total) if total else 0.5
    return ExecutionReliabilityIndicator(
        loops_completed=running,
        loops_failed_or_stopped=failed,
        shadow_forced_takeover_count=takeover_candidates,
        summary=f"running={running} awaiting_takeover={awaiting} forced_takeover={takeover_candidates}",
        score=round(score, 2),
    )


def build_subsystem_health_signals(state: dict[str, Any]) -> list[SubsystemHealthSignal]:
    """Build one SubsystemHealthSignal per subsystem from state."""
    signals: list[SubsystemHealthSignal] = []
    ob = operator_burden_from_state(state)
    mq = memory_quality_from_state(state)
    rq = routing_quality_from_state(state)
    er = execution_reliability_from_state(state)
    sq = state.get("signal_quality") or {}
    tr = state.get("triage", state.get("triage_state")) or {}

    signals.append(SubsystemHealthSignal(
        subsystem_id="operator_burden",
        label="Operator burden",
        status="warning" if ob.takeover_count + ob.triage_open_count > 2 else "ok",
        score=1.0 - min(1.0, (ob.takeover_count + ob.triage_open_count) / 10.0),
        summary=ob.summary,
        evidence_refs=["adaptive_execution_state", "supervisory_control_state", "triage"],
    ))
    signals.append(SubsystemHealthSignal(
        subsystem_id="memory_os",
        label="Memory / retrieval",
        status="degraded" if mq.weak_caution_count > 2 else ("warning" if mq.weak_caution_count > 0 else "ok"),
        score=mq.score,
        summary=mq.usefulness_summary,
        evidence_refs=["memory_intelligence"],
    ))
    signals.append(SubsystemHealthSignal(
        subsystem_id="routing",
        label="Routing / eval",
        status="warning" if rq.fallback_used else "ok",
        score=rq.score,
        summary=rq.summary,
        evidence_refs=["evaluation_state"],
    ))
    signals.append(SubsystemHealthSignal(
        subsystem_id="execution_loops",
        label="Execution reliability",
        status="degraded" if er.score < 0.5 else ("warning" if er.score < 0.7 else "ok"),
        score=er.score,
        summary=er.summary,
        evidence_refs=["adaptive_execution_state", "shadow_execution_state"],
    ))
    calmness = sq.get("calmness_score", 1.0)
    signals.append(SubsystemHealthSignal(
        subsystem_id="queue",
        label="Queue / signal quality",
        status="degraded" if calmness < 0.4 else ("warning" if calmness < 0.6 else "ok"),
        score=calmness if isinstance(calmness, (int, float)) else 0.5,
        summary=f"calmness={calmness} noise={sq.get('noise_level', '')}",
        evidence_refs=["signal_quality"],
    ))
    open_count = tr.get("open_issue_count", 0) or (len(tr.get("open_issues", [])) if isinstance(tr.get("open_issues"), list) else 0)
    signals.append(SubsystemHealthSignal(
        subsystem_id="triage",
        label="Triage / support",
        status="warning" if open_count > 5 else ("ok" if open_count == 0 else "warning"),
        score=max(0.0, 1.0 - open_count / 20.0),
        summary=f"open_issues={open_count}",
        evidence_refs=["triage"],
    ))
    return signals
