"""
M30E–M30H: Reliability harness — run golden paths, classify pass/degraded/blocked/fail, record failure point and subsystem.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.reliability.models import GoldenPathScenario, ReliabilityRunResult
from workflow_dataset.reliability.golden_paths import get_path
from workflow_dataset.reliability.store import save_run as save_reliability_run

OUTCOMES = ("pass", "degraded", "blocked", "fail")


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _run_acceptance_steps(step_ids: list[str], repo_root: Path, scenario_id: str = "founder_first_run") -> list[dict[str, Any]]:
    """Run acceptance journey steps (install_readiness, bootstrap_profile, ...). Uses founder_first_run for kit/simulate."""
    from workflow_dataset.acceptance.journeys import run_journey_steps
    return run_journey_steps(scenario_id, repo_root, step_ids=step_ids)


def _gather_project_plan_ready(repo_root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.planner.store import load_current_goal, load_latest_plan
        goal = load_current_goal(repo_root)
        plan = load_latest_plan(repo_root)
        return {
            "goal_set": bool(goal and goal.strip()),
            "plan_loaded": plan is not None,
            "plan_ready": plan is not None and (getattr(plan, "steps", None) or getattr(plan, "blocked_conditions", None) is not None),
        }
    except Exception as e:
        return {"error": str(e), "plan_ready": False}


def _gather_approval_ready(repo_root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.trust.cockpit import build_trust_cockpit
        cockpit = build_trust_cockpit(repo_root)
        reg = (cockpit.get("approval_readiness") or {}).get("registry_exists", False)
        return {"approval_registry_exists": reg, "ready": reg}
    except Exception as e:
        return {"error": str(e), "ready": False}


def _gather_simulate_available(repo_root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.acceptance.journeys import gather_run_first_simulate
        # Use a known workflow for founder; any runnable job/routine suffices
        out = gather_run_first_simulate(repo_root, "replay_cli_demo")
        if not out.get("runnable"):
            out = gather_run_first_simulate(repo_root, "first_value_steps")
        return {"runnable": out.get("runnable", False), **out}
    except Exception as e:
        return {"error": str(e), "runnable": False}


def _packs_dir(repo_root: Path) -> Path:
    return repo_root / "data/local/packs"


def _gather_pack_registry_ready(repo_root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.packs.pack_registry import list_installed_packs
        from workflow_dataset.packs.registry_index import get_registry_index_path
        pd = _packs_dir(repo_root)
        packs = list_installed_packs(pd)
        idx_path = get_registry_index_path(pd)
        return {"registry_ready": idx_path.exists(), "installed_count": len(packs), "ready": idx_path.exists()}
    except Exception as e:
        return {"error": str(e), "ready": False}


def _gather_behavior_resolution(repo_root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.packs.behavior_resolver import get_active_behavior_summary
        summary = get_active_behavior_summary(packs_dir=_packs_dir(repo_root))
        return {"resolved": bool(summary), "ready": bool(summary)}
    except Exception as e:
        return {"error": str(e), "ready": False}


def _gather_workspace_command_query(repo_root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.workspace.state import build_active_work_context
        ctx = build_active_work_context(repo_root)
        return {"work_context_available": ctx is not None, "ready": ctx is not None}
    except Exception as e:
        return {"error": str(e), "ready": False}


def _gather_upgrade_blockers(repo_root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.local_deployment.install_check import run_install_check
        check = run_install_check(repo_root=repo_root)
        return {"install_passed": check.get("passed", False), "blockers": check.get("missing_prereqs", [])[:5], "blocked": not check.get("passed", True)}
    except Exception as e:
        return {"error": str(e), "blocked": True}


def _gather_pack_health(repo_root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.packs.pack_registry import list_installed_packs
        from workflow_dataset.packs.pack_activation import get_suspended_pack_ids
        pd = _packs_dir(repo_root)
        packs = list_installed_packs(pd)
        suspended = get_suspended_pack_ids(pd)
        return {"installed_count": len(packs), "suspended_count": len(suspended), "healthy": len(packs) >= 0}
    except Exception as e:
        return {"error": str(e), "healthy": False}


def _gather_approval_registry_ready(repo_root: Path) -> dict[str, Any]:
    return _gather_approval_ready(repo_root)


def _gather_progress_board_ready(repo_root: Path) -> dict[str, Any]:
    try:
        from workflow_dataset.progress.board import build_progress_board
        board = build_progress_board(repo_root)
        return {"board_available": True, "active_projects": board.get("active_projects", [])[:5]}
    except Exception as e:
        return {"error": str(e), "board_available": False}


def _run_step(step_id: str, repo_root: Path, scenario_id: str) -> dict[str, Any]:
    """Run a single step: either via acceptance journey or custom gather."""
    acceptance_steps = {
        "install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack",
        "run_first_simulate", "inspect_trust", "inspect_inbox",
    }
    if step_id in acceptance_steps:
        results = _run_acceptance_steps([step_id], repo_root, scenario_id)
        if results:
            return results[0].get("actual", {})
        return {}
    # Custom steps
    if step_id == "project_plan_ready":
        return _gather_project_plan_ready(repo_root)
    if step_id == "approval_ready":
        return _gather_approval_ready(repo_root)
    if step_id == "simulate_available":
        return _gather_simulate_available(repo_root)
    if step_id == "pack_registry_ready":
        return _gather_pack_registry_ready(repo_root)
    if step_id == "behavior_resolution":
        return _gather_behavior_resolution(repo_root)
    if step_id == "workspace_command_query":
        return _gather_workspace_command_query(repo_root)
    if step_id == "upgrade_blockers":
        return _gather_upgrade_blockers(repo_root)
    if step_id == "pack_health":
        return _gather_pack_health(repo_root)
    if step_id == "approval_registry_ready":
        return _gather_approval_registry_ready(repo_root)
    if step_id == "progress_board_ready":
        return _gather_progress_board_ready(repo_root)
    return {"skipped": True, "reason": f"Unknown step {step_id}"}


def _map_step_to_subsystem(step_id: str, path: GoldenPathScenario) -> str:
    """Map step index to subsystem from path.subsystem_tags if available."""
    if not path.subsystem_tags:
        return step_id
    step_index = path.step_ids.index(step_id) if step_id in path.step_ids else 0
    if step_index < len(path.subsystem_tags):
        return path.subsystem_tags[step_index]
    return path.subsystem_tags[-1] if path.subsystem_tags else step_id


def classify_run_result(
    path: GoldenPathScenario,
    steps_results: list[dict[str, Any]],
) -> tuple[str, int | None, str | None, list[str]]:
    """
    Classify overall outcome from step results.
    Returns (outcome, failure_step_index, subsystem, reasons).
    pass: all critical steps met.
    degraded: usable but some non-critical steps weak.
    blocked: prerequisite missing (install, pack, approval).
    fail: unexpected error or critical step failed.
    """
    reasons: list[str] = []
    failure_index: int | None = None
    subsystem: str | None = None

    for i, sr in enumerate(steps_results):
        step_id = sr.get("step_id", "")
        actual = sr.get("actual", {})
        if actual.get("error"):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append(f"Step {step_id}: {actual.get('error')}")
            return "fail", failure_index, subsystem, reasons

        # Step-specific pass/fail
        if step_id == "install_readiness" and not actual.get("passed", False):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Install check did not pass.")
            return "blocked", failure_index, subsystem, reasons
        if step_id == "bootstrap_profile" and not actual.get("profile_exists"):
            reasons.append("Bootstrap profile not created.")
            if failure_index is None:
                failure_index = i
                subsystem = _map_step_to_subsystem(step_id, path)
            # Continue to see if we're only partial
        if step_id == "select_pack" and not actual.get("requested_kit_found"):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Requested kit not found.")
            return "blocked", failure_index, subsystem, reasons
        if step_id == "run_first_simulate" and not actual.get("runnable"):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("First simulate workflow not runnable.")
            return "blocked", failure_index, subsystem, reasons
        if step_id == "project_plan_ready" and not actual.get("plan_ready"):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Project/plan not ready.")
            return "blocked", failure_index, subsystem, reasons
        if step_id == "approval_ready" and not actual.get("ready"):
            reasons.append("Approval registry not ready.")
            if failure_index is None:
                failure_index = i
                subsystem = _map_step_to_subsystem(step_id, path)
        if step_id == "simulate_available" and not actual.get("runnable"):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Simulate not available.")
            return "blocked", failure_index, subsystem, reasons
        if step_id == "pack_registry_ready" and not actual.get("ready"):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Pack registry not ready.")
            return "blocked", failure_index, subsystem, reasons
        if step_id == "behavior_resolution" and not actual.get("ready"):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Behavior resolution failed.")
            return "blocked", failure_index, subsystem, reasons
        if step_id == "workspace_command_query" and not actual.get("ready"):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Workspace command context not available.")
            return "degraded", failure_index, subsystem, reasons
        if step_id == "upgrade_blockers" and actual.get("blocked"):
            failure_index = i
            subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Upgrade/install blocked.")
            return "blocked", failure_index, subsystem, reasons
        if step_id == "approval_registry_ready" and not actual.get("ready"):
            if failure_index is None:
                failure_index = i
                subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Approval registry not ready.")
        if step_id == "progress_board_ready" and not actual.get("board_available"):
            if failure_index is None:
                failure_index = i
                subsystem = _map_step_to_subsystem(step_id, path)
            reasons.append("Progress board not available.")

    if reasons:
        return "degraded", failure_index, subsystem, reasons
    return "pass", None, None, ["All steps met."]


def run_golden_path(
    path_id: str,
    repo_root: Path | str | None = None,
    scenario_id: str = "founder_first_run",
    save: bool = True,
) -> dict[str, Any]:
    """
    Run one golden path: execute each step, classify outcome, optionally save.
    Returns ReliabilityRunResult as dict plus steps_results.
    """
    root = _repo_root(repo_root)
    path = get_path(path_id)
    if not path:
        return {
            "path_id": path_id,
            "outcome": "fail",
            "reasons": [f"Golden path {path_id} not found"],
            "failure_step_index": None,
            "failure_step_id": None,
            "subsystem": None,
            "steps_results": [],
        }

    steps_results: list[dict[str, Any]] = []
    for step_id in path.step_ids:
        actual = _run_step(step_id, root, scenario_id)
        steps_results.append({"step_id": step_id, "actual": actual})

    outcome, failure_step_index, subsystem, reasons = classify_run_result(path, steps_results)
    failure_step_id = None
    if failure_step_index is not None and 0 <= failure_step_index < len(steps_results):
        failure_step_id = steps_results[failure_step_index].get("step_id")

    try:
        from workflow_dataset.utils.dates import utc_now_iso
    except Exception:
        from datetime import datetime, timezone
        def utc_now_iso() -> str:
            return datetime.now(timezone.utc).isoformat()

    run_id = utc_now_iso().replace(":", "-").replace(".", "-").replace("+", "-")[:23]
    run_id = f"rel_{run_id}"

    result = ReliabilityRunResult(
        run_id=run_id,
        path_id=path.path_id,
        path_name=path.name,
        outcome=outcome,
        failure_step_index=failure_step_index,
        failure_step_id=failure_step_id,
        subsystem=subsystem,
        reasons=reasons,
        steps_results=steps_results,
        timestamp=utc_now_iso(),
    )
    out = result.to_dict()
    if save:
        save_reliability_run(out, repo_root=root)
    return out
