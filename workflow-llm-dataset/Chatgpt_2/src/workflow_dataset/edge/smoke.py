"""
M23B-F3: Edge smoke checks — lightweight runtime validation for a tier.
Runs readiness checks and optionally minimal workflow runs (release demo) for selected workflows.
Local-only; reports pass/fail/skipped with degraded or missing-dependency reasons.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from workflow_dataset.edge.checks import run_readiness_checks, checks_summary
from workflow_dataset.edge.tiers import (
    EDGE_TIERS,
    TIER_LLM_REQUIREMENT,
    get_workflow_status_for_tier,
)

# Default workflows to smoke when not specified (representative subset)
DEFAULT_SMOKE_WORKFLOWS = ("weekly_status", "status_action_bundle")

# Timeout seconds for one workflow demo run
SMOKE_DEMO_TIMEOUT = 90


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd().resolve()


def _llm_config_exists(root: Path, config_path: str = "configs/settings.yaml") -> bool:
    """True if an LLM config path is present (e.g. configs/llm_training_full.yaml)."""
    llm_candidates = [
        root / "configs" / "llm_training_full.yaml",
        root / "configs" / "llm_training.yaml",
    ]
    return any(p.exists() for p in llm_candidates)


def run_smoke_check(
    tier: str,
    workflows: list[str] | None = None,
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
    run_demo: bool = True,
    demo_timeout: int = SMOKE_DEMO_TIMEOUT,
) -> dict[str, Any]:
    """
    Run smoke check for a tier: readiness checks + optional release-demo runs per workflow.
    Returns dict: readiness_summary, readiness_checks, workflow_results (list of {workflow, status, message, degraded_reason, missing_reason}), overall_pass.
    """
    root = _repo_root(repo_root)
    if tier not in EDGE_TIERS:
        return {
            "tier": tier,
            "error": f"Unknown tier. Use one of: {list(EDGE_TIERS)}",
            "readiness_summary": {},
            "readiness_checks": [],
            "workflow_results": [],
            "overall_pass": False,
        }
    workflows = workflows or list(DEFAULT_SMOKE_WORKFLOWS)
    status_map = get_workflow_status_for_tier(tier)
    llm_required = TIER_LLM_REQUIREMENT.get(tier, "required") == "required"
    has_llm = _llm_config_exists(root)

    checks = run_readiness_checks(repo_root=root, config_path=config_path)
    summary = checks_summary(checks)
    readiness_ok = summary.get("ready", False)

    workflow_results: list[dict[str, Any]] = []
    for wf in workflows:
        ws = status_map.get(wf) or {}
        wf_status = ws.get("status", "unavailable")
        reason = ws.get("reason", "")
        fallback = ws.get("fallback")
        missing = ws.get("missing_functionality") or []

        if wf_status == "unavailable":
            workflow_results.append({
                "workflow": wf,
                "status": "skipped",
                "message": "Workflow unavailable for this tier.",
                "degraded_reason": reason,
                "missing_reason": "Workflow not supported in tier.",
            })
            continue
        if llm_required and not has_llm:
            workflow_results.append({
                "workflow": wf,
                "status": "skipped",
                "message": "Skipped (LLM required but config missing).",
                "degraded_reason": None,
                "missing_reason": "LLM config (e.g. configs/llm_training_full.yaml) missing.",
            })
            continue
        if not run_demo:
            workflow_results.append({
                "workflow": wf,
                "status": "skipped",
                "message": "Demo run disabled (readiness only).",
                "degraded_reason": reason if wf_status == "degraded" else None,
                "missing_reason": None,
            })
            continue

        # Run release demo for this workflow (minimal context, no save)
        cli = [sys.executable, "-m", "workflow_dataset.cli"]
        args = [
            "release", "demo",
            "--workflow", wf,
            "--context-text", "Edge smoke test.",
            "--config", config_path,
        ]
        try:
            result = subprocess.run(
                cli + args,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=demo_timeout,
            )
            if result.returncode == 0:
                workflow_results.append({
                    "workflow": wf,
                    "status": "pass",
                    "message": "Demo completed successfully.",
                    "degraded_reason": reason if wf_status == "degraded" else None,
                    "missing_reason": None,
                })
            else:
                stderr = (result.stderr or "").strip()[:500]
                workflow_results.append({
                    "workflow": wf,
                    "status": "fail",
                    "message": stderr or f"Exit code {result.returncode}",
                    "degraded_reason": reason if wf_status == "degraded" else None,
                    "missing_reason": stderr if "not found" in stderr.lower() or "missing" in stderr.lower() else None,
                })
        except subprocess.TimeoutExpired:
            workflow_results.append({
                "workflow": wf,
                "status": "fail",
                "message": f"Demo timed out after {demo_timeout}s.",
                "degraded_reason": reason if wf_status == "degraded" else None,
                "missing_reason": None,
            })
        except Exception as e:
            workflow_results.append({
                "workflow": wf,
                "status": "fail",
                "message": str(e)[:300],
                "degraded_reason": reason if wf_status == "degraded" else None,
                "missing_reason": None,
            })

    passed = sum(1 for r in workflow_results if r.get("status") == "pass")
    failed = sum(1 for r in workflow_results if r.get("status") == "fail")
    skipped = sum(1 for r in workflow_results if r.get("status") == "skipped")
    overall_pass = readiness_ok and failed == 0

    return {
        "tier": tier,
        "readiness_summary": summary,
        "readiness_checks": checks,
        "readiness_ok": readiness_ok,
        "workflow_results": workflow_results,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "overall_pass": overall_pass,
    }
