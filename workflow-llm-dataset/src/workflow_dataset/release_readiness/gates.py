"""
M30L.1: Rollout gates — explicit conditions that must pass before a launch profile is allowed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.release_readiness.models import RolloutGate

# Gate IDs (used by launch profiles)
GATE_ENV_REQUIRED_OK = "env_required_ok"
GATE_ACCEPTANCE_PASS = "acceptance_pass"
GATE_FIRST_USER_READY = "first_user_ready"
GATE_RELEASE_READINESS_NOT_BLOCKED = "release_readiness_not_blocked"
GATE_ROLLOUT_STAGE_READY = "rollout_stage_ready_for_trial"
GATE_TRUST_APPROVAL_READY = "trust_approval_ready"

# Registry: gate_id -> RolloutGate
GATES: dict[str, RolloutGate] = {
    GATE_ENV_REQUIRED_OK: RolloutGate(
        gate_id=GATE_ENV_REQUIRED_OK,
        label="Environment required checks pass",
        description="Environment health required_ok true.",
    ),
    GATE_ACCEPTANCE_PASS: RolloutGate(
        gate_id=GATE_ACCEPTANCE_PASS,
        label="Latest acceptance pass",
        description="Latest acceptance run outcome is pass.",
    ),
    GATE_FIRST_USER_READY: RolloutGate(
        gate_id=GATE_FIRST_USER_READY,
        label="First-user install ready",
        description="Package readiness: ready_for_first_real_user_install.",
    ),
    GATE_RELEASE_READINESS_NOT_BLOCKED: RolloutGate(
        gate_id=GATE_RELEASE_READINESS_NOT_BLOCKED,
        label="Release readiness not blocked",
        description="Release readiness status is not blocked.",
    ),
    GATE_ROLLOUT_STAGE_READY: RolloutGate(
        gate_id=GATE_ROLLOUT_STAGE_READY,
        label="Rollout stage ready for trial",
        description="Rollout current_stage is ready_for_trial.",
    ),
    GATE_TRUST_APPROVAL_READY: RolloutGate(
        gate_id=GATE_TRUST_APPROVAL_READY,
        label="Trust/approval registry present",
        description="Trust cockpit approval registry exists.",
    ),
}


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def evaluate_gate(gate_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Evaluate a single gate. Returns {passed: bool, detail: str}.
    """
    root = _repo_root(repo_root)
    passed = False
    detail = ""

    if gate_id == GATE_ENV_REQUIRED_OK:
        try:
            from workflow_dataset.validation.env_health import check_environment_health
            env = check_environment_health(root)
            passed = bool(env.get("required_ok", False))
            detail = "required_ok=true" if passed else "required_ok=false or missing"
        except Exception as e:
            detail = str(e)

    elif gate_id == GATE_ACCEPTANCE_PASS:
        try:
            from workflow_dataset.acceptance.storage import load_latest_run
            run = load_latest_run(root)
            outcome = (run or {}).get("outcome")
            passed = outcome == "pass"
            detail = f"outcome={outcome}" if outcome else "no acceptance run"
        except Exception as e:
            detail = str(e)

    elif gate_id == GATE_FIRST_USER_READY:
        try:
            from workflow_dataset.package_readiness.summary import build_readiness_summary
            pkg = build_readiness_summary(root)
            passed = bool(pkg.get("ready_for_first_real_user_install", False))
            detail = "ready_for_first_real_user_install=true" if passed else "; ".join((pkg.get("not_ready_reasons") or [])[:3])
        except Exception as e:
            detail = str(e)

    elif gate_id == GATE_RELEASE_READINESS_NOT_BLOCKED:
        try:
            from workflow_dataset.release_readiness.readiness import build_release_readiness
            r = build_release_readiness(root)
            passed = r.status != "blocked"
            detail = f"release_readiness={r.status}"
        except Exception as e:
            detail = str(e)

    elif gate_id == GATE_ROLLOUT_STAGE_READY:
        try:
            from workflow_dataset.rollout.tracker import load_rollout_state
            rollout = load_rollout_state(root)
            stage = (rollout or {}).get("current_stage", "")
            passed = stage == "ready_for_trial"
            detail = f"current_stage={stage}"
        except Exception as e:
            detail = str(e)

    elif gate_id == GATE_TRUST_APPROVAL_READY:
        try:
            from workflow_dataset.trust.cockpit import build_trust_cockpit
            cockpit = build_trust_cockpit(root)
            approval = (cockpit or {}).get("approval_readiness") or {}
            passed = bool(approval.get("registry_exists", False))
            detail = "registry_exists=true" if passed else "registry_exists=false or missing"
        except Exception as e:
            detail = str(e)

    else:
        detail = f"unknown gate: {gate_id}"

    return {"passed": passed, "detail": detail}


def list_gates() -> list[dict[str, Any]]:
    """List all defined gates."""
    return [g.to_dict() for g in GATES.values()]


def get_gate(gate_id: str) -> RolloutGate | None:
    """Return RolloutGate for gate_id or None."""
    return GATES.get(gate_id)
