"""
M24C: Acceptance runner — run scenario in report mode, compare actual vs expected, classify pass/partial/blocked/fail.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.acceptance.scenarios import get_scenario
from workflow_dataset.acceptance.journeys import run_journey_steps


OUTCOMES = ("pass", "partial", "blocked", "fail")


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def classify_outcome(
    scenario_id: str,
    steps_results: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    """
    Classify overall outcome from step results. Returns (outcome, reasons).
    pass: critical steps met, no unexpected errors.
    partial: some steps met, some blocked as expected (e.g. no approval registry yet).
    blocked: first-value workflow or kit missing, or install not passed.
    fail: unexpected error or critical step failed.
    """
    reasons: list[str] = []
    scenario = get_scenario(scenario_id)
    if not scenario:
        return "fail", [f"Scenario {scenario_id} not found"]

    step_by_id = {r["step_id"]: r.get("actual", {}) for r in steps_results}
    has_error = any(
        step_by_id.get(s, {}).get("error") for s in (
            "install_readiness", "bootstrap_profile", "onboard_approvals",
            "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox"
        )
    )
    if has_error:
        err_steps = [s for s, a in step_by_id.items() if a.get("error")]
        if err_steps:
            reasons.append(f"Errors in steps: {err_steps}")
            return "fail", reasons

    # Install readiness
    install = step_by_id.get("install_readiness", {})
    if not install.get("passed", False):
        reasons.append("Install check did not pass (missing prereqs or failed required checks).")
        if install.get("missing_prereqs"):
            reasons.append("Missing: " + "; ".join(install.get("missing_prereqs", [])[:3]))
        return "blocked", reasons

    # Bootstrap profile: prefer exists
    bootstrap = step_by_id.get("bootstrap_profile", {})
    if not bootstrap.get("profile_exists"):
        reasons.append("Bootstrap profile not yet created (run profile bootstrap or first-run).")
        return "partial", reasons

    # Select pack: kit should be found
    select = step_by_id.get("select_pack", {})
    if not select.get("requested_kit_found"):
        reasons.append(f"Starter kit {scenario.starter_kit_id} not found.")
        return "blocked", reasons

    missing_prereqs = select.get("missing_prerequisites", [])
    if missing_prereqs:
        reasons.append("Missing prerequisites for kit: " + "; ".join(missing_prereqs[:3]))

    # First simulate workflow: job or routine should exist for full pass
    run_sim = step_by_id.get("run_first_simulate", {})
    if not run_sim.get("runnable", False):
        reasons.append(f"First simulate workflow ({run_sim.get('workflow_id', '')}) not found (job or routine missing).")
        return "blocked", reasons

    # Trust and inbox: no error
    if step_by_id.get("inspect_trust", {}).get("error"):
        reasons.append("Trust cockpit reported an error.")
        return "partial", reasons
    if step_by_id.get("inspect_inbox", {}).get("error"):
        reasons.append("Inbox reported an error.")
        return "partial", reasons

    if reasons:
        return "partial", reasons
    return "pass", ["All critical steps met; product ready for controlled first-user trial."]


def run_scenario(
    scenario_id: str,
    repo_root: Path | str | None = None,
    report_only: bool = True,
) -> dict[str, Any]:
    """
    Run acceptance scenario in report mode. Gathers state via journey steps; does not execute jobs/macros.
    Returns: scenario_id, outcome (pass|partial|blocked|fail), steps_results, reasons, ready_for_trial (bool).
    """
    root = _repo_root(repo_root)
    scenario = get_scenario(scenario_id)
    if not scenario:
        return {
            "scenario_id": scenario_id,
            "outcome": "fail",
            "reasons": [f"Scenario {scenario_id} not found"],
            "steps_results": [],
            "ready_for_trial": False,
        }

    steps_results = run_journey_steps(scenario_id, root, step_ids=scenario.first_value_steps or None)
    outcome, reasons = classify_outcome(scenario_id, steps_results)
    ready_for_trial = outcome == "pass"

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.name,
        "outcome": outcome,
        "reasons": reasons,
        "steps_results": steps_results,
        "ready_for_trial": ready_for_trial,
    }
