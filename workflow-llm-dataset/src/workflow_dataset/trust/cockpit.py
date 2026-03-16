"""
M23V: Trust / evidence cockpit — aggregate benchmark trust, coverage, approval readiness, job/macro trust, corrections, release gates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def build_trust_cockpit(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Aggregate trust and evidence from local sources only.
    Returns: benchmark_trust, trusted_real_coverage, simulate_only_coverage, approval_readiness,
    job_macro_trust_state, unresolved_corrections, release_gate_status.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "benchmark_trust": {},
        "trusted_real_coverage": 0.0,
        "simulate_only_coverage": 0.0,
        "approval_readiness": {},
        "job_macro_trust_state": {},
        "unresolved_corrections": {},
        "release_gate_status": {},
        "errors": [],
    }

    # Desktop benchmark board
    try:
        from workflow_dataset.desktop_bench.board import board_report
        br = board_report(limit_runs=10, root=root)
        out["benchmark_trust"] = {
            "latest_run_id": br.get("latest_run_id"),
            "latest_outcome": br.get("latest_outcome"),
            "latest_trust_status": br.get("latest_trust_status"),
            "simulate_only_coverage": br.get("simulate_only_coverage"),
            "trusted_real_coverage": br.get("trusted_real_coverage"),
            "missing_approval_blockers": br.get("missing_approval_blockers", []),
            "regressions": br.get("regressions", []),
            "recommended_next_action": br.get("recommended_next_action"),
        }
        out["simulate_only_coverage"] = br.get("simulate_only_coverage") or 0.0
        out["trusted_real_coverage"] = br.get("trusted_real_coverage") or 0.0
    except Exception as e:
        out["errors"].append(f"desktop_bench: {e}")

    # Approval readiness (desktop_bridge from mission_control-style)
    try:
        from workflow_dataset.capability_discovery.approval_registry import get_registry_path, load_approval_registry
        reg_path = get_registry_path(root)
        registry = load_approval_registry(root) if reg_path.exists() and reg_path.is_file() else None
        out["approval_readiness"] = {
            "registry_exists": reg_path.exists() and reg_path.is_file(),
            "registry_path": str(reg_path),
            "approved_paths_count": len(registry.approved_paths) if registry else 0,
            "approved_action_scopes_count": len(registry.approved_action_scopes) if registry else 0,
        }
    except Exception as e:
        out["errors"].append(f"approval: {e}")

    # Job / macro (routine) trust state
    try:
        from workflow_dataset.job_packs import job_packs_report
        from workflow_dataset.copilot.routines import list_routines
        jp = job_packs_report(root)
        routines = list_routines(root)
        out["job_macro_trust_state"] = {
            "total_jobs": jp.get("total_jobs", 0),
            "simulate_only_count": len(jp.get("simulate_only_jobs", [])),
            "trusted_for_real_count": len(jp.get("trusted_for_real_jobs", [])),
            "approval_blocked_count": len(jp.get("approval_blocked_jobs", [])),
            "recent_successful_count": len(jp.get("recent_successful", [])),
            "routines_count": len(routines),
        }
    except Exception as e:
        out["errors"].append(f"job_packs: {e}")

    # Unresolved corrections
    try:
        from workflow_dataset.corrections.propose import propose_updates
        from workflow_dataset.corrections.eval_bridge import advisory_review_for_corrections
        proposed = propose_updates(root)
        advisories = advisory_review_for_corrections(root, limit=20, min_count=2)
        out["unresolved_corrections"] = {
            "proposed_updates_count": len(proposed),
            "review_recommended_ids": [a.get("job_or_routine_id") for a in advisories if a.get("job_or_routine_id")][:10],
        }
    except Exception as e:
        out["errors"].append(f"corrections: {e}")

    # Release-gate status (from dashboard + release)
    try:
        from workflow_dataset.release.dashboard_data import get_dashboard_data
        from workflow_dataset.release.staging_board import load_staging_board
        dash = get_dashboard_data(repo_root=root)
        board = load_staging_board(repo_root=root)
        staging = dash.get("staging") or {}
        out["release_gate_status"] = {
            "unreviewed_count": (dash.get("review_package") or {}).get("unreviewed_count", 0),
            "package_pending_count": (dash.get("review_package") or {}).get("package_pending_count", 0),
            "staged_count": staging.get("staged_count", 0) or len((board.get("items") or [])),
            "release_readiness_report_exists": (root / "data/local/release/release_readiness_report.md").exists(),
        }
    except Exception as e:
        out["errors"].append(f"release: {e}")

    return out
