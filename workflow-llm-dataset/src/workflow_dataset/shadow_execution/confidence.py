"""
M45E–M45H Phase B: Confidence and risk evaluation using benchmark, runtime, memory, trust, loop/step type, degraded mode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.shadow_execution.models import ConfidenceScore, RiskMarker

CONFIDENCE_THRESHOLD_LOW = 0.4
CONFIDENCE_THRESHOLD_HIGH = 0.75
RISK_LEVEL_HIGH = "high"
RISK_LEVEL_MEDIUM = "medium"
RISK_LEVEL_LOW = "low"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _benchmark_contribution(plan_ref: str, step_index: int, repo_root: Path) -> float:
    """Prior benchmark results: try to get pass rate or score for this plan/step; return 0–1."""
    try:
        from workflow_dataset.eval.board import board_report
        root = _repo_root(repo_root)
        eval_root = root / "data/local/eval"
        br = board_report(limit_runs=3, root=eval_root)
        if br.get("recommendation") == "pass" or br.get("best_run_id"):
            return 0.7
        return 0.5
    except Exception:
        return 0.5


def _runtime_stability(repo_root: Path) -> float:
    """Runtime/model stability contribution; degraded mode reduces score."""
    try:
        root = _repo_root(repo_root)
        degraded_file = root / "data/local/reliability/degraded_active.json"
        if degraded_file.exists():
            return 0.4
        return 0.85
    except Exception:
        return 0.7


def _memory_prior_cases(plan_ref: str, project_id: str, repo_root: Path) -> float:
    """Memory-backed prior cases: high-confidence prior success boosts confidence."""
    try:
        from workflow_dataset.memory_intelligence import retrieve_for_context
        root = _repo_root(repo_root)
        prior = retrieve_for_context(project_id=project_id or "", query=f"plan {plan_ref} success", limit=3, repo_root=root)
        if not prior:
            return 0.5
        best = max((p.confidence for p in prior), default=0)
        return 0.5 + 0.4 * best
    except Exception:
        return 0.5


def _trust_posture(repo_root: Path) -> float:
    """Trust posture: cautious vs normal; affects confidence ceiling."""
    try:
        from workflow_dataset.trust.presets import get_active_preset_id
        root = _repo_root(repo_root)
        preset = get_active_preset_id(repo_root=root)
        if preset == "cautious":
            return 0.6
        return 0.85
    except Exception:
        return 0.7


def evaluate_confidence_step(
    step_index: int,
    step_id: str,
    plan_ref: str = "",
    loop_type: str = "",
    project_id: str = "",
    repo_root: Path | str | None = None,
) -> ConfidenceScore:
    """Compute confidence score for a single step."""
    root = _repo_root(repo_root)
    factors: list[str] = []
    bench = _benchmark_contribution(plan_ref, step_index, root)
    factors.append("benchmark")
    runtime = _runtime_stability(root)
    factors.append("runtime_stability")
    memory = _memory_prior_cases(plan_ref, project_id, root)
    factors.append("memory_prior")
    trust = _trust_posture(root)
    factors.append("trust_posture")
    degraded_penalty = 0.0
    if runtime < 0.6:
        degraded_penalty = 0.2
        factors.append("degraded_penalty")
    raw = (bench * 0.25 + runtime * 0.3 + memory * 0.25 + trust * 0.2)
    score = max(0.0, min(1.0, raw - degraded_penalty))
    return ConfidenceScore(
        scope="step",
        step_index=step_index,
        score=round(score, 3),
        factors=factors,
        degraded_penalty=degraded_penalty,
    )


def evaluate_confidence_loop(
    plan_ref: str = "",
    loop_type: str = "",
    step_scores: list[float] | None = None,
    project_id: str = "",
    repo_root: Path | str | None = None,
) -> ConfidenceScore:
    """Compute aggregate confidence for the loop (from step scores and loop-level factors)."""
    root = _repo_root(repo_root)
    factors: list[str] = []
    if step_scores:
        avg = sum(step_scores) / len(step_scores)
        factors.append("step_average")
    else:
        avg = 0.5
    runtime = _runtime_stability(root)
    trust = _trust_posture(root)
    memory = _memory_prior_cases(plan_ref, project_id, root)
    factors.extend(["runtime_stability", "trust_posture", "memory_prior"])
    degraded_penalty = 0.0
    if runtime < 0.6:
        degraded_penalty = 0.15
    raw = avg * 0.5 + runtime * 0.2 + trust * 0.15 + memory * 0.15
    score = max(0.0, min(1.0, raw - degraded_penalty))
    return ConfidenceScore(
        scope="loop",
        step_index=None,
        score=round(score, 3),
        factors=factors,
        degraded_penalty=degraded_penalty,
    )


def evaluate_risk_step(
    step_index: int,
    confidence_score: float,
    observed_status: str = "",
    repo_root: Path | str | None = None,
) -> RiskMarker:
    """Compute risk marker for a step."""
    if confidence_score < CONFIDENCE_THRESHOLD_LOW:
        level = RISK_LEVEL_HIGH
        reason = "confidence_below_threshold"
    elif confidence_score < CONFIDENCE_THRESHOLD_HIGH:
        level = RISK_LEVEL_MEDIUM
        reason = "confidence_moderate"
    else:
        level = RISK_LEVEL_LOW
        reason = "confidence_acceptable"
    if observed_status == "error":
        level = RISK_LEVEL_HIGH
        reason = "step_observed_error"
    elif observed_status == "blocked":
        level = RISK_LEVEL_MEDIUM
        reason = "step_blocked"
    return RiskMarker(scope="step", step_index=step_index, level=level, reason=reason)


def evaluate_risk_loop(confidence_loop: float, any_step_high_risk: bool) -> RiskMarker:
    """Compute risk marker for the loop."""
    if any_step_high_risk or confidence_loop < CONFIDENCE_THRESHOLD_LOW:
        return RiskMarker(scope="loop", step_index=None, level=RISK_LEVEL_HIGH, reason="loop_confidence_or_step_risk")
    if confidence_loop < CONFIDENCE_THRESHOLD_HIGH:
        return RiskMarker(scope="loop", step_index=None, level=RISK_LEVEL_MEDIUM, reason="loop_confidence_moderate")
    return RiskMarker(scope="loop", step_index=None, level=RISK_LEVEL_LOW, reason="loop_confidence_acceptable")
