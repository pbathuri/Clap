"""
M23N Phase 3: First-run product summary. What the product can do safely,
what is benchmarked/trusted, what is simulate-only, which jobs/routines are ready,
recommended first workflow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.onboarding.bootstrap_profile import (
    build_bootstrap_profile,
    load_bootstrap_profile,
    BootstrapProfile,
)


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root().resolve()
    except Exception:
        return Path.cwd().resolve()


def build_first_run_summary(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> dict[str, Any]:
    """
    Build first-run product summary from bootstrap profile and job/copilot data.
    Returns: what_can_do_safely, trusted_benchmarked, simulate_only, ready_jobs_routines, recommended_first_workflow.
    """
    root = _repo_root(repo_root)
    profile = load_bootstrap_profile(root)
    if profile is None:
        profile = build_bootstrap_profile(repo_root=root, config_path=config_path)

    what_can_do_safely: list[str] = []
    if profile.ready_for_real:
        what_can_do_safely.append("Execute trusted real actions (file inspect, list directory, notes read/summarize) on approved paths.")
    what_can_do_safely.append("Run all adapters in simulate mode (no real writes or app control).")
    what_can_do_safely.append("Use the operator console (workflow-dataset console) for setup, suggestions, materialize, apply with confirmation.")
    what_can_do_safely.append("Use dashboard (workflow-dataset dashboard) for readiness, workspaces, packages, next actions.")
    if profile.recommended_job_packs:
        what_can_do_safely.append(f"Run job packs: {', '.join(profile.recommended_job_packs[:5])} (simulate or real if approved).")

    trusted_benchmarked: list[str] = []
    for a in profile.trusted_real_actions:
        trusted_benchmarked.append(f"{a.get('adapter_id', '')}.{a.get('action_id', '')}")
    if not trusted_benchmarked and profile.adapter_ids:
        trusted_benchmarked.append("(None yet — add approved paths and action scopes in approvals.yaml to enable trusted real execution.)")

    simulate_only: list[str] = list(profile.simulate_only_adapters)[:10]
    for s in profile.simulate_only_actions[:5]:
        simulate_only.append(f"{s.get('adapter_id', '')}.{s.get('action_id', '')}")

    ready_jobs = list(profile.recommended_job_packs)[:10]
    ready_routines = list(profile.recommended_routines)[:5]

    recommended_first_workflow = "workflow-dataset onboard bootstrap"
    if profile.approval_registry_exists and profile.recommended_job_packs:
        recommended_first_workflow = f"workflow-dataset jobs run {profile.recommended_job_packs[0]} --mode simulate"
    elif profile.setup_session_id:
        recommended_first_workflow = "workflow-dataset console"
    elif not profile.approval_registry_exists:
        recommended_first_workflow = "workflow-dataset onboard bootstrap"

    return {
        "what_can_do_safely": what_can_do_safely,
        "trusted_benchmarked": trusted_benchmarked,
        "simulate_only": simulate_only,
        "ready_job_packs": ready_jobs,
        "ready_routines": ready_routines,
        "recommended_first_workflow": recommended_first_workflow,
        "ready_for_real": profile.ready_for_real,
        "approval_registry_exists": profile.approval_registry_exists,
    }


def format_first_run_summary(summary: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Format first-run product summary as human-readable text."""
    if summary is None:
        summary = build_first_run_summary(repo_root=repo_root)
    lines = [
        "# First-run product summary",
        "",
        "## What the product can do safely now",
        "",
    ]
    for s in summary.get("what_can_do_safely", []):
        lines.append(f"- {s}")
    lines.extend(["", "## Trusted / benchmarked (real execution when approved)", ""])
    for t in summary.get("trusted_benchmarked", []):
        lines.append(f"- {t}")
    lines.extend(["", "## Simulate-only (no real execution)", ""])
    for s in summary.get("simulate_only", []):
        if isinstance(s, dict):
            lines.append(f"- {s.get('adapter_id', '')}.{s.get('action_id', '')}")
        else:
            lines.append(f"- {s}")
    lines.extend(["", "## Personal jobs / routines ready", ""])
    lines.append(f"- Job packs: {', '.join(summary.get('ready_job_packs', []) or ['(none)'])}")
    lines.append(f"- Routines: {', '.join(summary.get('ready_routines', []) or ['(none)'])}")
    lines.extend([
        "",
        "## Recommended first workflow",
        "",
        summary.get("recommended_first_workflow", "workflow-dataset onboard"),
        "",
    ])
    return "\n".join(lines)
