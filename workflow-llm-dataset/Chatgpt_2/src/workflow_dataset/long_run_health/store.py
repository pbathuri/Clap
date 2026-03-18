"""
M46A–M46D: Persist health snapshots and drift signals under data/local/long_run_health.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.long_run_health.models import DeploymentHealthSnapshot, DriftSignal


DIR_NAME = "data/local/long_run_health"
SNAPSHOTS_INDEX = "snapshots_index.json"
DRIFT_SIGNALS_DIR = "drift_signals"
MAX_SNAPSHOTS_INDEX = 200
MAX_DRIFT_SIGNALS = 500


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_health_dir(repo_root: Path | str | None = None) -> Path:
    """Return data/local/long_run_health directory."""
    return _repo_root(repo_root) / DIR_NAME


def save_snapshot(snapshot: DeploymentHealthSnapshot, repo_root: Path | str | None = None) -> Path:
    """Append snapshot to index and persist. Returns path to index file."""
    root = get_health_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / SNAPSHOTS_INDEX
    index: list[dict[str, Any]] = []
    if path.exists():
        try:
            index = json.loads(path.read_text(encoding="utf-8")).get("snapshots", [])
        except Exception:
            index = []
    entry = {
        "snapshot_id": snapshot.snapshot_id,
        "generated_at_iso": snapshot.generated_at_iso,
        "window_kind": snapshot.window.kind,
        "alert_state": snapshot.alert_state.value,
    }
    index.insert(0, entry)
    index = index[:MAX_SNAPSHOTS_INDEX]
    path.write_text(json.dumps({"snapshots": index}, indent=2), encoding="utf-8")
    snap_file = root / "snapshots" / f"{snapshot.snapshot_id}.json"
    snap_file.parent.mkdir(parents=True, exist_ok=True)
    snap_file.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")
    return path


def load_snapshot(snapshot_id: str, repo_root: Path | str | None = None) -> DeploymentHealthSnapshot | None:
    """Load a snapshot by id."""
    root = get_health_dir(repo_root)
    snap_file = root / "snapshots" / f"{snapshot_id}.json"
    if not snap_file.exists():
        return None
    try:
        data = json.loads(snap_file.read_text(encoding="utf-8"))
        return _dict_to_snapshot(data)
    except Exception:
        return None


def _dict_to_snapshot(data: dict[str, Any]) -> DeploymentHealthSnapshot:
    from workflow_dataset.long_run_health.models import (
        DeploymentHealthSnapshot,
        StabilityWindow,
        SubsystemHealthSignal,
        DriftSignal,
        DegradationTrend,
        OperatorBurdenIndicator,
        MemoryQualityIndicator,
        RoutingQualityIndicator,
        ExecutionReliabilityIndicator,
        AlertState,
        AlertStateExplanation,
    )
    w = data.get("window") or {}
    window = StabilityWindow(kind=w.get("kind", "rolling_7"), start_iso=w.get("start_iso", ""), end_iso=w.get("end_iso", ""), label=w.get("label", ""))
    subs = []
    for s in data.get("subsystem_signals") or []:
        subs.append(SubsystemHealthSignal(
            subsystem_id=s.get("subsystem_id", ""),
            label=s.get("label", ""),
            status=s.get("status", "unknown"),
            score=float(s.get("score", 0)),
            summary=s.get("summary", ""),
            evidence_refs=list(s.get("evidence_refs", [])),
        ))
    drifts = [_dict_to_drift(d) for d in (data.get("drift_signals") or [])]
    trends = []
    for t in data.get("degradation_trends") or []:
        trends.append(DegradationTrend(
            subsystem_id=t.get("subsystem_id", ""),
            metric_id=t.get("metric_id", ""),
            direction=t.get("direction", "stable"),
            magnitude=float(t.get("magnitude", 0)),
            summary=t.get("summary", ""),
        ))
    ob = data.get("operator_burden")
    mq = data.get("memory_quality")
    rq = data.get("routing_quality")
    er = data.get("execution_reliability")
    alert_ex = data.get("alert_explanation")
    state_val = data.get("alert_state", "healthy")
    try:
        alert_state = AlertState(state_val)
    except ValueError:
        alert_state = AlertState.HEALTHY
    if alert_ex:
        ex_state = alert_ex.get("state", "healthy")
        try:
            ex_enum = AlertState(ex_state)
        except ValueError:
            ex_enum = AlertState.HEALTHY
        alert_explanation = AlertStateExplanation(
            state=ex_enum,
            rationale=alert_ex.get("rationale", ""),
            evidence_refs=list(alert_ex.get("evidence_refs", [])),
            confidence=alert_ex.get("confidence", "medium"),
            contradictory=alert_ex.get("contradictory", False),
            short_summary=alert_ex.get("short_summary", ""),
        )
    else:
        alert_explanation = None
    return DeploymentHealthSnapshot(
        snapshot_id=data.get("snapshot_id", ""),
        window=window,
        subsystem_signals=subs,
        drift_signals=drifts,
        degradation_trends=trends,
        operator_burden=OperatorBurdenIndicator(
            review_count=ob.get("review_count", 0),
            takeover_count=ob.get("takeover_count", 0),
            triage_open_count=ob.get("triage_open_count", 0),
            summary=ob.get("summary", ""),
            trend=ob.get("trend", "stable"),
        ) if ob else None,
        memory_quality=MemoryQualityIndicator(
            recommendation_count=mq.get("recommendation_count", 0),
            weak_caution_count=mq.get("weak_caution_count", 0),
            usefulness_summary=mq.get("usefulness_summary", ""),
            score=float(mq.get("score", 0)),
        ) if mq else None,
        routing_quality=RoutingQualityIndicator(
            summary=rq.get("summary", ""),
            score=float(rq.get("score", 0)),
            fallback_used=rq.get("fallback_used", False),
        ) if rq else None,
        execution_reliability=ExecutionReliabilityIndicator(
            loops_completed=er.get("loops_completed", 0),
            loops_failed_or_stopped=er.get("loops_failed_or_stopped", 0),
            shadow_forced_takeover_count=er.get("shadow_forced_takeover_count", 0),
            summary=er.get("summary", ""),
            score=float(er.get("score", 0)),
        ) if er else None,
        alert_state=alert_state,
        alert_explanation=alert_explanation,
        generated_at_iso=data.get("generated_at_iso", ""),
        vertical_id=data.get("vertical_id", ""),
    )


def _dict_to_drift(d: dict[str, Any]) -> DriftSignal:
    return DriftSignal(
        drift_id=d.get("drift_id", ""),
        kind=d.get("kind", ""),
        subsystem_id=d.get("subsystem_id", ""),
        severity=d.get("severity", "low"),
        summary=d.get("summary", ""),
        baseline_value=d.get("baseline_value"),
        current_value=d.get("current_value"),
        window_kind=d.get("window_kind", ""),
        evidence_refs=d.get("evidence_refs", []),
        created_at_iso=d.get("created_at_iso", ""),
    )


def list_snapshots(limit: int = 20, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List snapshot index entries (snapshot_id, generated_at_iso, window_kind, alert_state)."""
    root = get_health_dir(repo_root)
    path = root / SNAPSHOTS_INDEX
    if not path.exists():
        return []
    try:
        index = json.loads(path.read_text(encoding="utf-8")).get("snapshots", [])
        return index[:limit]
    except Exception:
        return []


def save_drift_signal(signal: DriftSignal, repo_root: Path | str | None = None) -> Path:
    """Persist a drift signal by id."""
    root = get_health_dir(repo_root)
    (root / DRIFT_SIGNALS_DIR).mkdir(parents=True, exist_ok=True)
    path = root / DRIFT_SIGNALS_DIR / f"{signal.drift_id}.json"
    path.write_text(json.dumps(signal.to_dict(), indent=2), encoding="utf-8")
    return path


def load_drift_signal(drift_id: str, repo_root: Path | str | None = None) -> DriftSignal | None:
    """Load a drift signal by id."""
    root = get_health_dir(repo_root)
    path = root / DRIFT_SIGNALS_DIR / f"{drift_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _dict_to_drift(data)
    except Exception:
        return None


def list_drift_signals(limit: int = 50, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List drift signal ids and summary from files."""
    root = get_health_dir(repo_root)
    drift_dir = root / DRIFT_SIGNALS_DIR
    if not drift_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(drift_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if len(out) >= limit:
            break
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append({"drift_id": data.get("drift_id"), "kind": data.get("kind"), "subsystem_id": data.get("subsystem_id"), "severity": data.get("severity"), "summary": (data.get("summary") or "")[:80], "created_at_iso": data.get("created_at_iso")})
        except Exception:
            pass
    return out
