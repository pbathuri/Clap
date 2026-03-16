"""
M23J: Job-level trust and approval policy. Refuse clearly if policy fails.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.job_packs.schema import JobPack
from workflow_dataset.capability_discovery.approval_registry import get_registry_path, load_approval_registry
from workflow_dataset.desktop_bench.trusted_actions import get_trusted_real_actions

TrustLevel = str  # simulate_only | trusted_for_real | approval_required_every_run | approval_valid_for_scope | experimental | benchmark_only


def check_job_policy(
    job: JobPack,
    mode: str,
    params: dict[str, Any],
    repo_root: Path | str | None = None,
) -> tuple[bool, str]:
    """
    Return (allowed, message). If not allowed, message explains why.
    - simulate_only job cannot run real.
    - trusted_for_real / approval_required_every_run / approval_valid_for_scope require registry for real.
    - experimental/benchmark_only: real only if job.real_mode_eligibility and registry allows.
    """
    if mode not in ("simulate", "real"):
        return False, f"Invalid mode: {mode}. Use simulate or real."

    if mode == "simulate":
        if not job.simulate_support:
            return False, "Job has simulate_support=false."
        return True, ""

    # Real mode
    if job.trust_level == "simulate_only":
        return False, "Job is simulate_only; cannot run in real mode."
    if not job.real_mode_eligibility:
        return False, "Job has real_mode_eligibility=false. Use --mode simulate."

    root = Path(repo_root).resolve() if repo_root else None
    reg_path = get_registry_path(root)
    if not reg_path.exists() or not reg_path.is_file():
        return False, "Real mode requires approval registry at data/local/capability_discovery/approvals.yaml."

    if job.trust_level in ("approval_required_every_run", "approval_valid_for_scope", "trusted_for_real"):
        # Ensure trusted actions include what this job needs
        trusted = get_trusted_real_actions(root)
        if not trusted.get("trusted_actions"):
            return False, "No trusted real actions in registry; add approved_action_scopes for this job's adapters/actions."

    return True, ""
