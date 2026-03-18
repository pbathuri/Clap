"""
M24F–M24I: Rollout go/no-go readiness report — demo-ready, first-user-ready,
blocks, operator actions, experimental. Aggregates rollout, package_readiness,
acceptance, trust, environment. Local-only; advisory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_rollout_readiness_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Aggregate rollout, package_readiness, acceptance, trust, environment into
    a single readiness payload: demo_ready, first_user_ready, blocks,
    operator_actions, experimental. No side effects.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "demo_ready": False,
        "demo_ready_reasons": [],
        "first_user_ready": False,
        "first_user_ready_reasons": [],
        "blocks": [],
        "operator_actions": [],
        "experimental": [],
    }

    # Rollout state
    try:
        from workflow_dataset.rollout.tracker import load_rollout_state
        rollout = load_rollout_state(root)
    except Exception:
        rollout = {}
    stage = rollout.get("current_stage") or "not_started"
    blocked_items = rollout.get("blocked_items") or []
    next_action = rollout.get("next_required_action")
    latest_acc = rollout.get("latest_acceptance_result") or {}
    acc_outcome = latest_acc.get("outcome")
    acc_ready = latest_acc.get("ready_for_trial", False)

    # Package readiness
    try:
        from workflow_dataset.package_readiness.summary import build_readiness_summary
        pkg = build_readiness_summary(root)
    except Exception:
        pkg = {}
    machine_ready = (pkg.get("current_machine_readiness") or {}).get("ready", False)
    first_install_ready = pkg.get("ready_for_first_real_user_install", False)
    not_ready_reasons = pkg.get("not_ready_reasons") or []
    ready_reasons = pkg.get("ready_reasons") or []
    out["experimental"] = list(pkg.get("experimental") or [])

    # Acceptance (if not already from rollout)
    if not latest_acc:
        try:
            from workflow_dataset.acceptance.storage import load_latest_run
            latest_run = load_latest_run(root)
            if latest_run:
                acc_outcome = latest_run.get("outcome")
                acc_ready = latest_run.get("ready_for_trial", False)
        except Exception:
            pass

    # Trust cockpit (light touch)
    try:
        from workflow_dataset.trust.cockpit import build_trust_cockpit
        cockpit = build_trust_cockpit(root)
        approval_ok = (cockpit.get("approval_readiness") or {}).get("registry_exists", False)
    except Exception:
        approval_ok = False
        cockpit = {}

    # Environment health
    try:
        from workflow_dataset.validation.env_health import check_environment_health
        env = check_environment_health(root)
        env_ok = env.get("required_ok", False)
    except Exception:
        env_ok = False

    # ---- Demo-ready ----
    if stage == "ready_for_trial" and acc_outcome == "pass":
        out["demo_ready"] = True
        out["demo_ready_reasons"].append("Rollout stage ready_for_trial and latest acceptance pass.")
    else:
        if acc_outcome != "pass" and acc_outcome is not None:
            out["demo_ready_reasons"].append(f"Latest acceptance outcome: {acc_outcome} (need pass).")
        if stage != "ready_for_trial":
            out["demo_ready_reasons"].append(f"Rollout stage: {stage} (need ready_for_trial). Run 'workflow-dataset rollout launch --id founder_demo'.")
    if blocked_items:
        out["demo_ready"] = False
        for b in blocked_items[:5]:
            out["blocks"].append(f"Rollout: {b}")

    # ---- First-user-ready ----
    if first_install_ready and acc_ready and env_ok:
        out["first_user_ready"] = True
        out["first_user_ready_reasons"].append("Package readiness: ready for first real-user install.")
        out["first_user_ready_reasons"].append("Acceptance: ready_for_trial.")
        if env_ok:
            out["first_user_ready_reasons"].append("Environment: required checks passed.")
    else:
        if not first_install_ready:
            for r in not_ready_reasons[:5]:
                out["first_user_ready_reasons"].append(f"Not ready: {r}")
                out["blocks"].append(r)
        if not acc_ready and acc_outcome is not None:
            out["first_user_ready_reasons"].append("Acceptance not ready for trial; re-run acceptance for target scenario.")
        if not env_ok:
            out["first_user_ready_reasons"].append("Environment required checks failed.")
            out["blocks"].append("Environment: required_ok false")

    # Dedupe blocks
    out["blocks"] = list(dict.fromkeys(out["blocks"]))

    # Operator actions
    if next_action:
        out["operator_actions"].append(next_action)
    if not machine_ready and not_ready_reasons:
        out["operator_actions"].append("Run 'workflow-dataset package readiness-report' and fix missing prerequisites.")
    if acc_outcome not in ("pass", None):
        out["operator_actions"].append("Run 'workflow-dataset acceptance run --id <scenario_id>' and address reasons.")
    if not rollout and not out["operator_actions"]:
        out["operator_actions"].append("Run 'workflow-dataset rollout launch --id founder_demo' to start golden journey.")

    return out


def format_rollout_readiness_report(repo_root: Path | str | None = None) -> str:
    """Produce a readable go/no-go readiness report for the operator."""
    r = build_rollout_readiness_report(repo_root)
    lines = [
        "=== Rollout readiness (go/no-go) ===",
        "",
        "[Demo-ready] " + ("YES" if r["demo_ready"] else "NO"),
    ]
    for reason in r.get("demo_ready_reasons") or []:
        lines.append("  " + reason)
    lines.append("")
    lines.append("[First-user-ready] " + ("YES" if r["first_user_ready"] else "NO"))
    for reason in r.get("first_user_ready_reasons") or []:
        lines.append("  " + reason)
    lines.append("")
    lines.append("[Blocks]")
    for b in r.get("blocks") or []:
        lines.append("  - " + b)
    if not r.get("blocks"):
        lines.append("  (none)")
    lines.append("")
    lines.append("[Operator actions]")
    for a in r.get("operator_actions") or []:
        lines.append("  - " + a)
    if not r.get("operator_actions"):
        lines.append("  (none)")
    lines.append("")
    lines.append("[Experimental / advisory]")
    for e in r.get("experimental") or []:
        lines.append("  - " + str(e))
    lines.append("")
    lines.append("(Local-only. No automatic changes.)")
    return "\n".join(lines)
