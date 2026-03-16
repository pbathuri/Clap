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

    # 5. Coordination graph (advisory; M23F-F1) — task demos → graph summary
    try:
        from workflow_dataset.task_demos.store import list_tasks, get_task
        from workflow_dataset.coordination_graph.build import task_definition_to_graph
        ids = list_tasks(root)
        total_nodes = total_edges = 0
        for tid in ids:
            task = get_task(tid, root)
            if task:
                g = task_definition_to_graph(task)
                total_nodes += len(g.nodes)
                total_edges += len(g.edges)
        out["coordination_graph_summary"] = {
            "tasks_count": len(ids),
            "total_nodes": total_nodes,
            "total_edges": total_edges,
        }
        out["local_sources"]["task_demonstrations"] = str((root / "data/local/task_demonstrations").resolve())
    except Exception as e:
        out["coordination_graph_summary"] = {"error": str(e)}

    # 6. Desktop bridge (M23H) — adapters, approvals, task demos, coordination
    try:
        from workflow_dataset.desktop_adapters.registry import list_adapters
        from workflow_dataset.capability_discovery.approval_registry import get_registry_path, load_approval_registry
        adapters = list_adapters()
        adapter_ids = [a.adapter_id for a in adapters]
        reg_path = get_registry_path(root)
        registry = load_approval_registry(root) if reg_path.exists() and reg_path.is_file() else None
        cg = out.get("coordination_graph_summary") or {}
        out["desktop_bridge"] = {
            "adapters_count": len(adapter_ids),
            "adapter_ids": adapter_ids,
            "approvals_path": str(reg_path),
            "approvals_file_exists": reg_path.exists() and reg_path.is_file(),
            "approved_paths_count": len(registry.approved_paths) if registry else 0,
            "approved_action_scopes_count": len(registry.approved_action_scopes) if registry else 0,
            "tasks_count": cg.get("tasks_count", 0),
            "coordination_nodes": cg.get("total_nodes", 0),
            "coordination_edges": cg.get("total_edges", 0),
        }
        out["local_sources"]["approval_registry"] = str(reg_path)
    except Exception as e:
        out["desktop_bridge"] = {"error": str(e)}

    # 7. Job packs (M23J) — personal reusable jobs
    try:
        from workflow_dataset.job_packs import list_job_packs, job_packs_report
        ids = list_job_packs(root)
        report = job_packs_report(root)
        out["job_packs"] = {
            "total": len(ids),
            "job_pack_ids": ids,
            "simulate_only_count": len(report.get("simulate_only_jobs", [])),
            "trusted_for_real_count": len(report.get("trusted_for_real_jobs", [])),
            "approval_blocked_count": len(report.get("approval_blocked_jobs", [])),
            "recent_successful_count": len(report.get("recent_successful", [])),
        }
        out["local_sources"]["job_packs"] = str((root / "data/local/job_packs").resolve())
    except Exception as e:
        out["job_packs"] = {"error": str(e)}

    # 8. Copilot (M23K) — recommended jobs, routines, reminders, recent plan runs
    try:
        from workflow_dataset.copilot.recommendations import recommend_jobs
        from workflow_dataset.copilot.routines import list_routines
        from workflow_dataset.copilot.run import list_plan_runs
        from workflow_dataset.copilot.reminders import list_reminders
        recs = recommend_jobs(root, limit=15)
        routines = list_routines(root)
        runs = list_plan_runs(limit=5, repo_root=root)
        reminders = list_reminders(root)
        blocked = [r["job_pack_id"] for r in recs if r.get("blocking_issues")]
        out["copilot"] = {
            "recommended_jobs_count": len(recs),
            "recommended_job_ids": [r["job_pack_id"] for r in recs][:10],
            "blocked_jobs_count": len(blocked),
            "routines_count": len(routines),
            "routine_ids": routines[:10],
            "recent_plan_runs_count": len(runs),
            "reminders_count": len(reminders),
            "upcoming_reminders": reminders[:5],
            "next_copilot_action": "run copilot recommend" if recs else "run jobs seed then copilot recommend",
        }
        out["local_sources"]["copilot"] = str((root / "data/local/copilot").resolve())
    except Exception as e:
        out["copilot"] = {"error": str(e)}

    # 9. Work context (M23L) — context snapshot, context-aware recommendations, drift
    try:
        from workflow_dataset.context.snapshot import load_snapshot
        from workflow_dataset.context.work_state import build_work_state
        from workflow_dataset.copilot.recommendations import recommend_jobs
        from workflow_dataset.context.drift import load_latest_and_previous, compare_snapshots
        latest_ws = load_snapshot("latest", root)
        if latest_ws is None:
            latest_ws = build_work_state(root)
        recs_ctx = recommend_jobs(root, limit=15, context_snapshot=latest_ws)
        blocked_ctx = [r["job_pack_id"] for r in recs_ctx if r.get("blocking_issues")]
        latest_id = getattr(latest_ws, "snapshot_id", "") or ""
        drift_summary: list[str] = []
        newly_recommendable: list[str] = []
        prev_ws = load_snapshot("previous", root)
        if prev_ws and latest_ws:
            drift = compare_snapshots(prev_ws, latest_ws)
            drift_summary = drift.summary[:5]
            newly_recommendable = drift.newly_recommendable_jobs[:10]
        out["work_context"] = {
            "latest_snapshot_id": latest_id,
            "context_recommendations_count": len(recs_ctx),
            "context_blocked_count": len(blocked_ctx),
            "newly_recommendable_jobs": newly_recommendable,
            "reminders_due_count": len(latest_ws.reminders_due_sample) if latest_ws else 0,
            "recent_state_changes": drift_summary,
            "next_recommended_action": "copilot recommend --context latest" if recs_ctx else "context refresh then copilot recommend",
        }
        out["local_sources"]["context"] = str((root / "data/local/context").resolve())
    except Exception as e:
        out["work_context"] = {"error": str(e)}

    # 10. Corrections (M23M) — operator correction loop, proposed/applied/reverted, advisory review
    try:
        from workflow_dataset.corrections.store import list_corrections
        from workflow_dataset.corrections.propose import propose_updates
        from workflow_dataset.corrections.history import list_applied_updates, list_reverted_updates
        from workflow_dataset.corrections.eval_bridge import advisory_review_for_corrections
        corrections = list_corrections(limit=20, repo_root=root)
        proposed = propose_updates(root)
        applied = list_applied_updates(limit=10, repo_root=root)
        reverted = list_reverted_updates(limit=5, repo_root=root)
        advisories = advisory_review_for_corrections(root, limit=50, min_count=2)
        out["corrections"] = {
            "recent_corrections_count": len(corrections),
            "proposed_updates_count": len(proposed),
            "applied_updates_count": len(applied),
            "reverted_updates_count": len(reverted),
            "review_recommended": [a.get("job_or_routine_id") for a in advisories[:5]],
            "next_corrections_action": "corrections propose-updates" if proposed else ("corrections report" if corrections else ""),
        }
        out["local_sources"]["corrections"] = str((root / "data/local/corrections").resolve())
    except Exception as e:
        out["corrections"] = {"error": str(e)}

    # 11. Runtime mesh (M23T) — backends, catalog, recommended model by task, integrations, local vs remote
    try:
        from workflow_dataset.runtime_mesh.backend_registry import list_backend_profiles
        from workflow_dataset.runtime_mesh.policy import recommend_for_task_class
        from workflow_dataset.runtime_mesh.integration_registry import list_integrations
        backends = list_backend_profiles(root)
        available = [b.backend_id for b in backends if b.status in ("available", "configured")]
        missing = [b.backend_id for b in backends if b.status == "missing"]
        rec_copilot = recommend_for_task_class("desktop_copilot", root)
        rec_code = recommend_for_task_class("codebase_task", root)
        integrations = list_integrations(root)
        out["runtime_mesh"] = {
            "available_backends": available,
            "missing_runtimes": missing,
            "backend_count": len(backends),
            "recommended_backend_desktop_copilot": rec_copilot.get("backend_id"),
            "recommended_model_class_desktop_copilot": rec_copilot.get("model_class"),
            "recommended_backend_codebase_task": rec_code.get("backend_id"),
            "recommended_model_class_codebase_task": rec_code.get("model_class"),
            "integrations_count": len(integrations),
            "integrations_local_only": all(i.local and not i.optional_remote for i in integrations),
            "integrations_enabled_count": sum(1 for i in integrations if i.enabled),
        }
        out["local_sources"]["runtime_mesh"] = str((root / "data/local/runtime").resolve())
    except Exception as e:
        out["runtime_mesh"] = {"error": str(e)}

    # 12. M23V Daily inbox summary (additive)
    try:
        from workflow_dataset.daily.inbox import build_daily_digest
        digest = build_daily_digest(root)
        out["daily_inbox"] = {
            "relevant_jobs_count": len(digest.relevant_job_ids),
            "relevant_routines_count": len(digest.relevant_routine_ids),
            "blocked_count": len(digest.blocked_items),
            "reminders_due_count": len(digest.reminders_due),
            "recommended_next_action": digest.recommended_next_action,
        }
    except Exception as e:
        out["daily_inbox"] = {"error": str(e)}

    # 13. M23V Trust cockpit summary (additive)
    try:
        from workflow_dataset.trust.cockpit import build_trust_cockpit
        cockpit = build_trust_cockpit(root)
        out["trust_cockpit"] = {
            "benchmark_trust_status": (cockpit.get("benchmark_trust") or {}).get("latest_trust_status"),
            "approval_registry_exists": (cockpit.get("approval_readiness") or {}).get("registry_exists"),
            "release_gate_staged_count": (cockpit.get("release_gate_status") or {}).get("staged_count", 0),
        }
    except Exception as e:
        out["trust_cockpit"] = {"error": str(e)}

    # 14. M23V Package readiness summary (additive)
    try:
        from workflow_dataset.package_readiness.summary import build_readiness_summary
        ready = build_readiness_summary(root)
        out["package_readiness"] = {
            "machine_ready": (ready.get("current_machine_readiness") or {}).get("ready"),
            "ready_for_first_install": ready.get("ready_for_first_real_user_install"),
        }
    except Exception as e:
        out["package_readiness"] = {"error": str(e)}

    return out
