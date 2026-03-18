"""
M23X: First-value flow — ordered steps: bootstrap profile, check runtime, onboard approvals,
show recommended job, show inbox, run one safe simulate-only routine. No auto-run of workflows;
suggest commands for operator. Optional run of read-only status steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.operator_quickstart.first_run_tour import build_first_run_tour


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root().resolve()
    except Exception:
        return Path.cwd().resolve()


def build_first_value_flow(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build first-value flow: ordered steps with title, command, description, run_read_only.
    run_read_only=True means we can run this step (status/read-only) and show output; False means we only suggest the command.
    """
    root = _repo_root(repo_root)
    tour = build_first_run_tour(root)

    steps: list[dict[str, Any]] = [
        {
            "step": 1,
            "title": "Bootstrap profile",
            "description": "Create or refresh user work profile and bootstrap profile.",
            "command": "workflow-dataset profile bootstrap",
            "run_read_only": False,
            "suggested_next": "workflow-dataset profile show",
        },
        {
            "step": 2,
            "title": "Check runtime mesh",
            "description": "See available backends and recommended model classes.",
            "command": "workflow-dataset runtime backends",
            "run_read_only": True,
        },
        {
            "step": 3,
            "title": "Onboard approvals",
            "description": "Review onboarding status and optionally approve path/app/action scopes.",
            "command": "workflow-dataset onboard status",
            "run_read_only": True,
            "suggested_next": "workflow-dataset onboard bootstrap  # then onboard approve if you want real execution",
        },
        {
            "step": 4,
            "title": "Show recommended job pack",
            "description": "List job packs and see which are recommended (from profile/bootstrap).",
            "command": "workflow-dataset jobs list",
            "run_read_only": True,
            "suggested_next": "workflow-dataset copilot recommend  # for recommended jobs with reasons",
        },
        {
            "step": 5,
            "title": "Show inbox",
            "description": "Daily digest: relevant jobs/routines, blocked, reminders, top next action.",
            "command": "workflow-dataset inbox",
            "run_read_only": True,
        },
        {
            "step": 6,
            "title": "Run one safe simulate-only routine",
            "description": "Run a job or routine in simulate mode (no real execution; no approval required).",
            "command": tour.get("recommended_first_workflow", "workflow-dataset jobs run <job_id> --mode simulate"),
            "run_read_only": False,
            "note": "Replace <job_id> with a job from 'jobs list' or use the recommended first workflow above.",
        },
    ]

    # If we have a concrete recommended first workflow that is a job run, use it in step 6
    rec = tour.get("recommended_first_workflow", "")
    if "jobs run" in rec and "--mode simulate" in rec:
        steps[5]["command"] = rec
        steps[5]["note"] = "This is the recommended first workflow from your profile."

    return {
        "steps": steps,
        "intro": "First-value flow (M23X). Run steps in order. Steps marked run_read_only can be executed by the quickstart; others are suggested only.",
    }


def format_first_value_flow_text(flow: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Format first-value flow as plain text."""
    if flow is None:
        flow = build_first_value_flow(repo_root)
    lines = [flow.get("intro", "First-value flow"), ""]
    for s in flow.get("steps", []):
        lines.append(f"  Step {s['step']}: {s['title']}")
        lines.append(f"    {s['description']}")
        lines.append(f"    Command: {s['command']}")
        if s.get("suggested_next"):
            lines.append(f"    Then: {s['suggested_next']}")
        if s.get("note"):
            lines.append(f"    Note: {s['note']}")
        lines.append("")
    return "\n".join(lines)
