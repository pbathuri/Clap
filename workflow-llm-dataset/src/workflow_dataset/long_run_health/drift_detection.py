"""
M46A–M46D: Drift detection — read-only from mission_control, reliability, stores.
M46D.1: Optional drift threshold profile (conservative, balanced, production_strict).
Returns DriftSignal or None per kind; no writes.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from workflow_dataset.long_run_health.models import DriftSignal
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

if TYPE_CHECKING:
    from workflow_dataset.long_run_health.threshold_profiles import DriftThresholdProfile


def _profile_or_balanced(profile: "DriftThresholdProfile | None") -> "DriftThresholdProfile":
    if profile is not None:
        return profile
    from workflow_dataset.long_run_health.threshold_profiles import get_threshold_profile, PROFILE_BALANCED
    return get_threshold_profile("balanced") or PROFILE_BALANCED


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def execution_loop_drift(
    state: dict[str, Any],
    window_kind: str,
    repo_root: Path | str | None = None,
    threshold_profile: "DriftThresholdProfile | None" = None,
) -> DriftSignal | None:
    """Drift: execution loops failing or awaiting takeover more than baseline."""
    p = _profile_or_balanced(threshold_profile)
    ae = state.get("adaptive_execution_state") or {}
    awaiting = ae.get("awaiting_takeover_count", 0) or 0
    running = ae.get("running_loop_count", 0) or 0
    if awaiting + running == 0:
        return None
    fail_ratio = awaiting / max(1, awaiting + running)
    if fail_ratio < p.execution_loop_fail_ratio_max:
        return None
    severity = "high" if fail_ratio > 0.6 else ("medium" if fail_ratio > 0.45 else "low")
    drift_id = stable_id("drift", "execution_loop", window_kind, utc_now_iso()[:10], prefix="drift_")
    return DriftSignal(
        drift_id=drift_id,
        kind="execution_loop",
        subsystem_id="execution_loops",
        severity=severity,
        summary=f"Execution loop failure/awaiting ratio {fail_ratio:.2f} (awaiting={awaiting} running={running})",
        baseline_value=0.2,
        current_value=fail_ratio,
        window_kind=window_kind,
        evidence_refs=["adaptive_execution_state"],
        created_at_iso=utc_now_iso(),
    )


def intervention_rate_drift(
    state: dict[str, Any],
    window_kind: str,
    repo_root: Path | str | None = None,
    threshold_profile: "DriftThresholdProfile | None" = None,
) -> DriftSignal | None:
    """Drift: high intervention (pause/takeover/redirect) rate."""
    p = _profile_or_balanced(threshold_profile)
    sc = state.get("supervisory_control_state") or {}
    paused = sc.get("paused_loops_count", 0) or 0
    taken = sc.get("taken_over_count", 0) or 0
    active = sc.get("active_loops_count", 0) or 1
    rate = (paused + taken) / max(1, active)
    if rate < p.intervention_rate_max:
        return None
    severity = "high" if rate > 0.9 else ("medium" if rate > 0.7 else "low")
    drift_id = stable_id("drift", "intervention_rate", window_kind, utc_now_iso()[:10], prefix="drift_")
    return DriftSignal(
        drift_id=drift_id,
        kind="intervention_rate",
        subsystem_id="operator_burden",
        severity=severity,
        summary=f"Intervention rate {rate:.2f} (paused={paused} taken_over={taken} active={active})",
        baseline_value=0.2,
        current_value=rate,
        window_kind=window_kind,
        evidence_refs=["supervisory_control_state"],
        created_at_iso=utc_now_iso(),
    )


def queue_calmness_drift(
    state: dict[str, Any],
    window_kind: str,
    repo_root: Path | str | None = None,
    threshold_profile: "DriftThresholdProfile | None" = None,
) -> DriftSignal | None:
    """Drift: queue calmness dropped or noise increased."""
    p = _profile_or_balanced(threshold_profile)
    sq = state.get("signal_quality") or {}
    calmness = sq.get("calmness_score")
    if calmness is None:
        return None
    c = float(calmness) if isinstance(calmness, (int, float)) else 0.5
    if c >= p.queue_calmness_min:
        return None
    severity = "high" if c < 0.3 else ("medium" if c < 0.4 else "low")
    drift_id = stable_id("drift", "queue_calmness", window_kind, utc_now_iso()[:10], prefix="drift_")
    return DriftSignal(
        drift_id=drift_id,
        kind="queue_calmness",
        subsystem_id="queue",
        severity=severity,
        summary=f"Queue calmness low: {c:.2f} (noise={sq.get('noise_level', '')})",
        baseline_value=0.7,
        current_value=c,
        window_kind=window_kind,
        evidence_refs=["signal_quality"],
        created_at_iso=utc_now_iso(),
    )


def memory_quality_drift(
    state: dict[str, Any],
    window_kind: str,
    repo_root: Path | str | None = None,
    threshold_profile: "DriftThresholdProfile | None" = None,
) -> DriftSignal | None:
    """Drift: memory retrieval quality / weak cautions increased."""
    p = _profile_or_balanced(threshold_profile)
    mi = state.get("memory_intelligence", state.get("memory_intelligence_state")) or {}
    weak = mi.get("weak_memory_caution_count", 0) or 0
    if weak <= p.memory_weak_cautions_max:
        return None
    severity = "high" if weak > 5 else ("medium" if weak > 3 else "low")
    drift_id = stable_id("drift", "memory_quality", window_kind, utc_now_iso()[:10], prefix="drift_")
    return DriftSignal(
        drift_id=drift_id,
        kind="memory_quality",
        subsystem_id="memory_os",
        severity=severity,
        summary=f"Memory weak cautions elevated: {weak}",
        baseline_value=0.0,
        current_value=float(weak),
        window_kind=window_kind,
        evidence_refs=["memory_intelligence"],
        created_at_iso=utc_now_iso(),
    )


def routing_quality_drift(
    state: dict[str, Any],
    window_kind: str,
    repo_root: Path | str | None = None,
    threshold_profile: "DriftThresholdProfile | None" = None,
) -> DriftSignal | None:
    """Drift: eval recommendation regressed (revert/hold)."""
    ev = state.get("evaluation_state") or {}
    rec = (ev.get("recommendation") or "").lower()
    if rec not in ("revert", "rollback", "hold"):
        return None
    severity = "high" if rec in ("revert", "rollback") else "medium"
    drift_id = stable_id("drift", "routing_quality", window_kind, utc_now_iso()[:10], prefix="drift_")
    return DriftSignal(
        drift_id=drift_id,
        kind="routing_quality",
        subsystem_id="routing",
        severity=severity,
        summary=f"Eval recommendation: {rec}",
        baseline_value=0.0,
        current_value=1.0 if rec in ("revert", "rollback") else 0.5,
        window_kind=window_kind,
        evidence_refs=["evaluation_state"],
        created_at_iso=utc_now_iso(),
    )


def takeover_frequency_drift(
    state: dict[str, Any],
    window_kind: str,
    repo_root: Path | str | None = None,
    threshold_profile: "DriftThresholdProfile | None" = None,
) -> DriftSignal | None:
    """Drift: shadow forced takeover or supervisory takeover frequency high."""
    p = _profile_or_balanced(threshold_profile)
    sh = state.get("shadow_execution_state") or {}
    sc = state.get("supervisory_control_state") or {}
    forced = sh.get("forced_takeover_candidate_count", 0) or 0
    taken = sc.get("taken_over_count", 0) or 0
    if forced + taken < p.takeover_count_min:
        return None
    severity = "high" if forced + taken > 5 else ("medium" if forced + taken > 3 else "low")
    drift_id = stable_id("drift", "takeover_frequency", window_kind, utc_now_iso()[:10], prefix="drift_")
    return DriftSignal(
        drift_id=drift_id,
        kind="takeover_frequency",
        subsystem_id="operator_burden",
        severity=severity,
        summary=f"Takeover frequency high: forced_takeover={forced} taken_over={taken}",
        baseline_value=0.0,
        current_value=float(forced + taken),
        window_kind=window_kind,
        evidence_refs=["shadow_execution_state", "supervisory_control_state"],
        created_at_iso=utc_now_iso(),
    )


def triage_recurrence_drift(
    state: dict[str, Any],
    window_kind: str,
    repo_root: Path | str | None = None,
    threshold_profile: "DriftThresholdProfile | None" = None,
) -> DriftSignal | None:
    """Drift: triage open issues elevated."""
    p = _profile_or_balanced(threshold_profile)
    tr = state.get("triage", state.get("triage_state")) or {}
    open_count = tr.get("open_issue_count", 0)
    if isinstance(tr.get("open_issues"), list):
        open_count = open_count or len(tr["open_issues"])
    if open_count < p.triage_open_issues_min:
        return None
    severity = "high" if open_count > 10 else ("medium" if open_count > 5 else "low")
    drift_id = stable_id("drift", "triage_recurrence", window_kind, utc_now_iso()[:10], prefix="drift_")
    return DriftSignal(
        drift_id=drift_id,
        kind="triage_recurrence",
        subsystem_id="triage",
        severity=severity,
        summary=f"Triage open issues: {open_count}",
        baseline_value=0.0,
        current_value=float(open_count),
        window_kind=window_kind,
        evidence_refs=["triage"],
        created_at_iso=utc_now_iso(),
    )


def value_regression_drift(
    state: dict[str, Any],
    window_kind: str,
    repo_root: Path | str | None = None,
    threshold_profile: "DriftThresholdProfile | None" = None,
) -> DriftSignal | None:
    """Drift: vertical/first-value regression (from product_state / cohort)."""
    p = _profile_or_balanced(threshold_profile)
    prod = state.get("product_state") or {}
    cohort = prod.get("cohort_recommendation") or ""
    avg_usefulness = prod.get("avg_usefulness")
    if avg_usefulness is not None and float(avg_usefulness) < p.value_usefulness_min:
        severity = "high" if float(avg_usefulness) < 0.25 else "medium"
        drift_id = stable_id("drift", "value_regression", window_kind, utc_now_iso()[:10], prefix="drift_")
        return DriftSignal(
            drift_id=drift_id,
            kind="value_regression",
            subsystem_id="value",
            severity=severity,
            summary=f"Avg usefulness low: {avg_usefulness}",
            baseline_value=0.6,
            current_value=float(avg_usefulness),
            window_kind=window_kind,
            evidence_refs=["product_state"],
            created_at_iso=utc_now_iso(),
        )
    if "rollback" in cohort.lower() or "narrow" in cohort.lower():
        drift_id = stable_id("drift", "value_regression", window_kind, utc_now_iso()[:10], prefix="drift_")
        return DriftSignal(
            drift_id=drift_id,
            kind="value_regression",
            subsystem_id="value",
            severity="medium",
            summary=f"Cohort recommendation: {cohort}",
            baseline_value=0.0,
            current_value=0.5,
            window_kind=window_kind,
            evidence_refs=["product_state"],
            created_at_iso=utc_now_iso(),
        )
    return None


def collect_drift_signals(
    state: dict[str, Any],
    window_kind: str = "rolling_7",
    repo_root: Path | str | None = None,
    threshold_profile: "DriftThresholdProfile | None" = None,
) -> list[DriftSignal]:
    """Run all drift detectors and return list of signals (may be empty)."""
    root = _repo_root(repo_root)
    out: list[DriftSignal] = []
    for fn in (
        execution_loop_drift,
        intervention_rate_drift,
        queue_calmness_drift,
        memory_quality_drift,
        routing_quality_drift,
        takeover_frequency_drift,
        triage_recurrence_drift,
        value_regression_drift,
    ):
        try:
            s = fn(state, window_kind, root, threshold_profile)
            if s:
                out.append(s)
        except Exception:
            pass
    return out
