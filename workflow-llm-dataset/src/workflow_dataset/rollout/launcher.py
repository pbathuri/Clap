"""
M24F: Golden journey launcher — run acceptance for demo's scenario, return next step.
No execution of real actions; report mode only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.rollout.demos import get_demo, DEMO_TO_SCENARIO


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def launch_golden_journey(
    demo_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Launch golden journey for a demo: run acceptance for the matching scenario,
    update rollout state, return next step and summary. No job/macro execution.
    """
    root = _repo_root(repo_root)
    demo = get_demo(demo_id)
    if not demo:
        return {
            "demo_id": demo_id,
            "error": f"Demo {demo_id} not found",
            "outcome": "fail",
            "next_step": "workflow-dataset rollout demos list",
        }

    scenario_id = DEMO_TO_SCENARIO.get(demo_id)
    if not scenario_id:
        scenario_id = demo_id.replace("_demo", "_first_run")

    # Run acceptance (report mode)
    try:
        from workflow_dataset.acceptance.runner import run_scenario
        from workflow_dataset.acceptance.storage import save_run
        from workflow_dataset.rollout.tracker import update_rollout_from_acceptance
        result = run_scenario(scenario_id, repo_root=root, report_only=True)
        save_run(result, repo_root=root)
        update_rollout_from_acceptance(result, repo_root=root, target_scenario_id=scenario_id)
    except Exception as e:
        return {
            "demo_id": demo_id,
            "scenario_id": scenario_id,
            "error": str(e),
            "outcome": "fail",
            "next_step": "workflow-dataset acceptance run --id " + scenario_id,
        }

    # Next step suggestion
    outcome = result.get("outcome", "fail")
    if outcome == "pass":
        next_step = "Product ready for trial. Run 'workflow-dataset inbox' for daily digest; consider 'workflow-dataset kits first-run --id " + demo.required_pack + "' for first-value flow."
    elif outcome == "partial":
        next_step = "Address reasons above; then run 'workflow-dataset acceptance run --id " + scenario_id + "' again or 'workflow-dataset quickstart first-value'."
    elif outcome == "blocked":
        next_step = "Fix blocked items (install check, kit prerequisites); then run 'workflow-dataset acceptance run --id " + scenario_id + "'."
    else:
        next_step = "Run 'workflow-dataset acceptance report' for details; fix errors and re-run acceptance."

    return {
        "demo_id": demo_id,
        "scenario_id": scenario_id,
        "outcome": outcome,
        "ready_for_trial": result.get("ready_for_trial", False),
        "reasons": result.get("reasons", []),
        "next_step": next_step,
    }
