"""
M40J: Production release gate evaluation — supported surface freeze, deployment bundle, upgrade/recovery, trust, reliability, operator playbooks, vertical first-value.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.production_launch.models import LaunchGateResult

# Production gate IDs (aligned with spec; reuse release_readiness gates where applicable)
PRODUCTION_GATE_SUPPORTED_SURFACE_FREEZE = "supported_surface_freeze_complete"
PRODUCTION_GATE_DEPLOYMENT_BUNDLE_VALID = "deployment_bundle_valid"
PRODUCTION_GATE_UPGRADE_RECOVERY_POSTURE = "upgrade_recovery_posture_acceptable"
PRODUCTION_GATE_TRUST_REVIEW_POSTURE = "trust_review_posture_acceptable"
PRODUCTION_GATE_RELIABILITY_GOLDEN_PATH = "reliability_golden_path_health_acceptable"
PRODUCTION_GATE_OPERATOR_PLAYBOOKS_READY = "operator_playbooks_supportability_ready"
PRODUCTION_GATE_VERTICAL_FIRST_VALUE = "chosen_vertical_first_value_proof_acceptable"
PRODUCTION_GATE_RELEASE_READINESS_NOT_BLOCKED = "release_readiness_not_blocked"

PRODUCTION_GATE_LABELS: dict[str, str] = {
    PRODUCTION_GATE_SUPPORTED_SURFACE_FREEZE: "Supported surface freeze complete",
    PRODUCTION_GATE_DEPLOYMENT_BUNDLE_VALID: "Deployment bundle valid",
    PRODUCTION_GATE_UPGRADE_RECOVERY_POSTURE: "Upgrade/recovery posture acceptable",
    PRODUCTION_GATE_TRUST_REVIEW_POSTURE: "Trust/review posture acceptable",
    PRODUCTION_GATE_RELIABILITY_GOLDEN_PATH: "Reliability golden-path health acceptable",
    PRODUCTION_GATE_OPERATOR_PLAYBOOKS_READY: "Operator playbooks and supportability ready",
    PRODUCTION_GATE_VERTICAL_FIRST_VALUE: "Chosen vertical first-value proof acceptable",
    PRODUCTION_GATE_RELEASE_READINESS_NOT_BLOCKED: "Release readiness not blocked",
}


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _evaluate_supported_surface_freeze(root: Path) -> tuple[bool, str]:
    """Supported surface scope is defined and consistent with active vertical."""
    try:
        from workflow_dataset.vertical_selection import get_active_vertical_id, get_scope_report
        vid = get_active_vertical_id(root)
        if not vid:
            return True, "no vertical locked; surface freeze N/A"
        report = get_scope_report(vid, root)
        if not report:
            return False, "scope report missing for vertical"
        return True, f"vertical={vid} scope defined"
    except Exception as e:
        return False, str(e)


def _evaluate_deployment_bundle_valid(root: Path) -> tuple[bool, str]:
    """Deployment bundle exists and is valid (local path or manifest check)."""
    bundle_dir = root / "data/local/distribution/bundles"
    if not bundle_dir.exists():
        return True, "no bundle dir; optional for local-first"
    bundles = list(bundle_dir.glob("*.json"))
    if not bundles:
        return True, "no bundles yet; optional"
    # Basic validity: at least one JSON file exists
    try:
        import json
        for p in bundles[:3]:
            json.loads(p.read_text(encoding="utf-8"))
        return True, f"bundles present: {len(bundles)}"
    except Exception as e:
        return False, str(e)


def _evaluate_upgrade_recovery_posture(root: Path) -> tuple[bool, str]:
    """Upgrade and recovery posture acceptable (install check, rollback available or N/A)."""
    try:
        from workflow_dataset.package_readiness.summary import build_readiness_summary
        pkg = build_readiness_summary(root)
        if not pkg.get("ready_for_first_real_user_install"):
            return False, "package not ready for first real user install"
        return True, "package ready; rollback check optional"
    except Exception as e:
        return False, str(e)


def _evaluate_trust_review_posture(root: Path) -> tuple[bool, str]:
    """Trust cockpit and approval registry present."""
    try:
        from workflow_dataset.release_readiness.gates import evaluate_gate, GATE_TRUST_APPROVAL_READY
        r = evaluate_gate(GATE_TRUST_APPROVAL_READY, root)
        return bool(r.get("passed")), r.get("detail", "")
    except Exception as e:
        return False, str(e)


def _evaluate_reliability_golden_path(root: Path) -> tuple[bool, str]:
    """Reliability golden-path health acceptable (latest run pass or degraded)."""
    try:
        from workflow_dataset.reliability import load_latest_run
        latest = load_latest_run(root)
        if not latest:
            return True, "no runs; N/A"
        outcome = latest.get("outcome", "")
        if outcome in ("blocked", "fail"):
            return False, f"latest outcome={outcome}"
        return True, f"outcome={outcome}"
    except Exception as e:
        return False, str(e)


def _evaluate_operator_playbooks_ready(root: Path) -> tuple[bool, str]:
    """Operator playbooks and supportability ready (triage playbooks + release supportability)."""
    try:
        from workflow_dataset.triage.playbooks import get_default_playbooks
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        playbooks = get_default_playbooks()
        readiness = build_release_readiness(root)
        guidance = (readiness.supportability.guidance or "").strip()
        if readiness.status == "blocked":
            return False, "release readiness blocked"
        return True, f"playbooks={len(playbooks)} guidance={guidance or 'ok'}"
    except Exception as e:
        return False, str(e)


def _evaluate_vertical_first_value(root: Path) -> tuple[bool, str]:
    """Chosen vertical first-value proof acceptable (milestone progress or N/A)."""
    try:
        from workflow_dataset.vertical_selection import get_active_vertical_id
        from workflow_dataset.vertical_packs.progress import build_milestone_progress_output
        vid = get_active_vertical_id(root)
        if not vid:
            return True, "no vertical; N/A"
        vp = build_milestone_progress_output(repo_root=root)
        blocked = vp.get("blocked_vertical_onboarding_step") or {}
        if blocked.get("blocked_step_index") is not None:
            return False, f"blocked at step {blocked.get('blocked_step_index')}: {blocked.get('remediation_hint', '')[:60]}"
        return True, f"vertical={vid} first-value path ok"
    except Exception as e:
        return False, str(e)


def _evaluate_release_readiness_not_blocked(root: Path) -> tuple[bool, str]:
    """Release readiness status is not blocked."""
    try:
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        r = build_release_readiness(root)
        return r.status != "blocked", f"release_readiness={r.status}"
    except Exception as e:
        return False, str(e)


def evaluate_production_gates(repo_root: Path | str | None = None) -> list[LaunchGateResult]:
    """
    Evaluate all production gates. Returns list of LaunchGateResult (passed, detail per gate).
    """
    root = _repo_root(repo_root)
    results: list[LaunchGateResult] = []

    evaluators: list[tuple[str, Any]] = [
        (PRODUCTION_GATE_RELEASE_READINESS_NOT_BLOCKED, _evaluate_release_readiness_not_blocked),
        (PRODUCTION_GATE_SUPPORTED_SURFACE_FREEZE, _evaluate_supported_surface_freeze),
        (PRODUCTION_GATE_DEPLOYMENT_BUNDLE_VALID, _evaluate_deployment_bundle_valid),
        (PRODUCTION_GATE_UPGRADE_RECOVERY_POSTURE, _evaluate_upgrade_recovery_posture),
        (PRODUCTION_GATE_TRUST_REVIEW_POSTURE, _evaluate_trust_review_posture),
        (PRODUCTION_GATE_RELIABILITY_GOLDEN_PATH, _evaluate_reliability_golden_path),
        (PRODUCTION_GATE_OPERATOR_PLAYBOOKS_READY, _evaluate_operator_playbooks_ready),
        (PRODUCTION_GATE_VERTICAL_FIRST_VALUE, _evaluate_vertical_first_value),
    ]

    for gate_id, fn in evaluators:
        try:
            passed, detail = fn(root)
            results.append(LaunchGateResult(
                gate_id=gate_id,
                label=PRODUCTION_GATE_LABELS.get(gate_id, gate_id),
                passed=passed,
                detail=detail or "",
            ))
        except Exception as e:
            results.append(LaunchGateResult(
                gate_id=gate_id,
                label=PRODUCTION_GATE_LABELS.get(gate_id, gate_id),
                passed=False,
                detail=str(e),
            ))

    return results
