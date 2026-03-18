"""
M24C: Golden acceptance journeys — ordered steps with gather_actual (read-only).
No job/macro execution; only state gathering from existing APIs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

JOURNEY_STEP_IDS = [
    "install_readiness",
    "bootstrap_profile",
    "onboard_approvals",
    "select_pack",
    "run_first_simulate",
    "inspect_trust",
    "inspect_inbox",
]


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def gather_install_readiness(repo_root: Path | str | None) -> dict[str, Any]:
    """Gather install/readiness state. Read-only."""
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.local_deployment.install_check import run_install_check
        out = run_install_check(repo_root=root)
        return {"passed": out.get("passed"), "missing_prereqs": out.get("missing_prereqs", []), "summary": out.get("summary", "")}
    except Exception as e:
        return {"error": str(e), "passed": False}


def gather_bootstrap_profile(repo_root: Path | str | None) -> dict[str, Any]:
    """Gather bootstrap profile existence and key fields. Read-only."""
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.onboarding.bootstrap_profile import load_bootstrap_profile, get_bootstrap_profile_path
        path = get_bootstrap_profile_path(root)
        exists = path.exists() and path.is_file()
        profile = load_bootstrap_profile(root)
        return {
            "profile_exists": exists,
            "machine_id": profile.machine_id if profile else "",
            "ready_for_real": profile.ready_for_real if profile else False,
            "recommended_job_packs": list(profile.recommended_job_packs)[:10] if profile else [],
        }
    except Exception as e:
        return {"error": str(e), "profile_exists": False}


def gather_onboard_approvals(repo_root: Path | str | None) -> dict[str, Any]:
    """Gather onboarding/approval status. Read-only."""
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.onboarding.onboarding_flow import get_onboarding_status
        status = get_onboarding_status(repo_root=root)
        return {
            "profile_exists": status.get("profile_exists"),
            "env_ready": status.get("env_ready"),
            "approval_summary": status.get("approval_summary", {}),
            "blocked_or_unavailable": list(status.get("blocked_or_unavailable", []))[:10],
            "recommended_next_steps": list(status.get("recommended_next_steps", []))[:5],
        }
    except Exception as e:
        return {"error": str(e)}


def gather_select_pack(repo_root: Path | str | None, starter_kit_id: str) -> dict[str, Any]:
    """Gather starter kit recommendation and missing prereqs for the given kit. Read-only."""
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.starter_kits.recommend import recommend_kit_from_profile
        from workflow_dataset.starter_kits.registry import get_kit
        rec = recommend_kit_from_profile(profile=None, repo_root=root)
        kit = get_kit(starter_kit_id)
        k = rec.get("kit")
        recommended_kit_id = getattr(k, "kit_id", "") if k else ""
        return {
            "recommended_kit_id": recommended_kit_id,
            "requested_kit_id": starter_kit_id,
            "requested_kit_found": kit is not None,
            "missing_prerequisites": list(rec.get("missing_prerequisites", [])),
            "score": rec.get("score", 0),
        }
    except Exception as e:
        try:
            from workflow_dataset.starter_kits.registry import get_kit
            kit = get_kit(starter_kit_id)
            return {"requested_kit_id": starter_kit_id, "requested_kit_found": kit is not None, "error": str(e)}
        except Exception:
            return {"error": str(e), "requested_kit_found": False}


def gather_run_first_simulate(repo_root: Path | str | None, first_simulate_workflow_id: str) -> dict[str, Any]:
    """Gather whether first simulate workflow exists (job or routine). Does NOT run it. Read-only."""
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.job_packs import get_job_pack
        from workflow_dataset.copilot.routines import get_routine
        job = get_job_pack(first_simulate_workflow_id, root)
        routine = get_routine(first_simulate_workflow_id, root)
        return {
            "workflow_id": first_simulate_workflow_id,
            "job_exists": job is not None,
            "routine_exists": routine is not None,
            "runnable": job is not None or routine is not None,
        }
    except Exception as e:
        return {"error": str(e), "runnable": False}


def gather_inspect_trust(repo_root: Path | str | None) -> dict[str, Any]:
    """Gather trust cockpit state. Read-only."""
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.trust.cockpit import build_trust_cockpit
        cockpit = build_trust_cockpit(root)
        return {
            "benchmark_trust_status": (cockpit.get("benchmark_trust") or {}).get("latest_trust_status"),
            "approval_registry_exists": (cockpit.get("approval_readiness") or {}).get("registry_exists"),
            "release_gate_staged_count": (cockpit.get("release_gate_status") or {}).get("staged_count", 0),
        }
    except Exception as e:
        return {"error": str(e)}


def gather_inspect_inbox(repo_root: Path | str | None) -> dict[str, Any]:
    """Gather inbox/daily digest state. Read-only."""
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.daily.inbox import build_daily_digest
        digest = build_daily_digest(root)
        return {
            "relevant_jobs_count": len(digest.relevant_job_ids),
            "relevant_routines_count": len(digest.relevant_routine_ids),
            "blocked_count": len(digest.blocked_items),
            "reminders_due_count": len(digest.reminders_due),
            "recommended_next_action": digest.recommended_next_action or "",
        }
    except Exception as e:
        return {"error": str(e)}


def run_journey_steps(
    scenario_id: str,
    repo_root: Path | str | None,
    step_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Run journey steps in report mode: gather actual state for each step.
    Returns list of {step_id, actual, error?}.
    Does NOT execute jobs or macros; run_first_simulate only checks existence of job/routine.
    """
    from workflow_dataset.acceptance.scenarios import get_scenario
    from workflow_dataset.starter_kits.registry import get_kit

    scenario = get_scenario(scenario_id)
    if not scenario:
        return []
    root = _repo_root(repo_root)
    steps = step_ids or scenario.first_value_steps or JOURNEY_STEP_IDS
    kit = get_kit(scenario.starter_kit_id) if scenario.starter_kit_id else None
    first_workflow_id = (kit.first_simulate_only_workflow if kit else "") or ""

    results: list[dict[str, Any]] = []
    for step_id in steps:
        actual: dict[str, Any] = {}
        try:
            if step_id == "install_readiness":
                actual = gather_install_readiness(root)
            elif step_id == "bootstrap_profile":
                actual = gather_bootstrap_profile(root)
            elif step_id == "onboard_approvals":
                actual = gather_onboard_approvals(root)
            elif step_id == "select_pack":
                actual = gather_select_pack(root, scenario.starter_kit_id)
            elif step_id == "run_first_simulate":
                actual = gather_run_first_simulate(root, first_workflow_id)
            elif step_id == "inspect_trust":
                actual = gather_inspect_trust(root)
            elif step_id == "inspect_inbox":
                actual = gather_inspect_inbox(root)
            else:
                actual = {"skipped": True, "reason": f"Unknown step {step_id}"}
        except Exception as e:
            actual = {"error": str(e)}
        results.append({"step_id": step_id, "actual": actual})
    return results
