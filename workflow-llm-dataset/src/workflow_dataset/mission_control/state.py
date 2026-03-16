"""
M22B: Aggregate internal product-development state from local sources only. Read-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def get_mission_control_state(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Aggregate product state, evaluation state, development state, incubator state from local sources.
    No network; no writes. All paths in local_sources for provenance.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "product_state": {},
        "evaluation_state": {},
        "development_state": {},
        "incubator_state": {},
        "local_sources": {"repo_root": str(root.resolve())},
    }

    # 1. Product state (validated workflows, cohort, package/staging)
    try:
        from workflow_dataset.release.dashboard_data import get_dashboard_data
        from workflow_dataset.release.reporting_workspaces import REPORTING_WORKFLOWS
        dash = get_dashboard_data(repo_root=root)
        out["product_state"] = {
            "validated_workflows": list(REPORTING_WORKFLOWS),
            "cohort_recommendation": dash.get("cohort", {}).get("recommendation"),
            "cohort_sessions_count": dash.get("cohort", {}).get("sessions_count"),
            "avg_usefulness": dash.get("cohort", {}).get("avg_usefulness"),
            "review_package": dash.get("review_package", {}),
            "recent_workspaces_count": len(dash.get("recent_workspaces", [])),
            "staging": dash.get("staging", {}),
        }
        out["local_sources"]["pilot_dir"] = dash.get("local_sources", {}).get("pilot_dir", "")
        out["local_sources"]["workspaces_root"] = dash.get("local_sources", {}).get("workspaces_root", "")
    except Exception as e:
        out["product_state"]["error"] = str(e)

    # 2. Evaluation state (benchmark runs, regressions, best variant)
    try:
        from workflow_dataset.eval.board import board_report, list_runs
        br = board_report(limit_runs=5, root=root / "data/local/eval")
        runs = list_runs(limit=10, root=root / "data/local/eval")
        out["evaluation_state"] = {
            "latest_run_id": br.get("latest_run_id"),
            "latest_timestamp": br.get("latest_timestamp"),
            "recommendation": br.get("recommendation"),
            "best_run_id": br.get("best_run_id"),
            "runs_count": len(runs),
            "comparison": br.get("comparison_with_previous"),
            "workflows_tested": br.get("workflows_tested", []),
        }
        out["local_sources"]["eval_runs"] = str((root / "data/local/eval/runs").resolve())
    except Exception as e:
        out["evaluation_state"]["error"] = str(e)

    # 3. Development state (experiments, proposals, risks)
    try:
        from workflow_dataset.devlab.experiments import get_queue_status
        from workflow_dataset.devlab.proposals import list_proposals, proposal_queue_summary
        eq = get_queue_status(root / "data/local/devlab")
        pq = proposal_queue_summary(root / "data/local/devlab")
        proposals = list_proposals(root / "data/local/devlab")
        out["development_state"] = {
            "experiment_queue": eq,
            "proposal_queue": pq,
            "proposals_total": len(proposals),
            "pending_proposals": pq.get("pending", 0),
            "accepted_proposals": pq.get("accepted", 0),
            "rejected_proposals": pq.get("rejected", 0),
        }
        out["local_sources"]["devlab_root"] = str((root / "data/local/devlab").resolve())
    except Exception as e:
        out["development_state"]["error"] = str(e)

    # 4. Incubator state (candidates by stage, promotion recs, rejected)
    try:
        from workflow_dataset.incubator.registry import list_candidates
        candidates = list_candidates(root / "data/local/incubator")
        by_stage: dict[str, int] = {}
        promoted = rejected = hold = 0
        for c in candidates:
            s = c.get("stage", "idea")
            by_stage[s] = by_stage.get(s, 0) + 1
            d = c.get("promotion_decision", "none")
            if d == "promoted":
                promoted += 1
            elif d == "rejected":
                rejected += 1
            elif d == "hold":
                hold += 1
        out["incubator_state"] = {
            "candidates_by_stage": by_stage,
            "candidates_total": len(candidates),
            "promoted_count": promoted,
            "rejected_count": rejected,
            "hold_count": hold,
        }
        out["local_sources"]["incubator_root"] = str((root / "data/local/incubator").resolve())
    except Exception as e:
        out["incubator_state"]["error"] = str(e)

    return out
