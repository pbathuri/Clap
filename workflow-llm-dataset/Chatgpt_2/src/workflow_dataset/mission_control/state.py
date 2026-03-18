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

    # 4b. Candidate model studio (M42E–M42H) — top candidate, latest slice, quarantined, next eval step
    try:
        from workflow_dataset.candidate_model_studio.report import get_mission_control_candidate_studio_state
        studio = get_mission_control_candidate_studio_state(repo_root=root)
        out["candidate_model_studio_state"] = studio
        out["local_sources"]["candidate_model_studio_root"] = str((root / "data/local/candidate_model_studio").resolve())
    except Exception as e:
        out["candidate_model_studio_state"] = {"error": str(e)}

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

    # 6b. Observation runtime (M31) — enabled sources, blocked, recent counts, consent posture
    try:
        from workflow_dataset.observe.state import load_observation_state
        from workflow_dataset.observe.boundaries import get_boundary_state
        from workflow_dataset.observe.local_events import load_events
        event_log_dir = root / "data/local/event_log"
        state_dir = root / "data/local"
        state = load_observation_state(state_dir)
        if state.get("enabled_sources") is not None:
            obs_enabled = bool(state.get("observation_enabled", True))
            allowed = list(state.get("enabled_sources", []))
        else:
            try:
                from workflow_dataset.settings import load_settings
                s = load_settings(str(root / "configs/settings.yaml"))
                agent = s.agent
                obs_enabled = agent.observation_enabled if agent else False
                allowed = list(agent.allowed_observation_sources or []) if agent else []
            except Exception:
                obs_enabled = False
                allowed = []
        boundary = get_boundary_state(obs_enabled, allowed, file_root_paths=None)
        recent_count = 0
        if event_log_dir.exists():
            recent_count = len(load_events(event_log_dir, limit=500))
        out["observation_state"] = {
            "observation_enabled": boundary["observation_enabled"],
            "enabled_sources": boundary["enabled_sources"],
            "blocked_sources": boundary["blocked_sources"],
            "stub_sources": boundary["stub_sources"],
            "recent_events_count": recent_count,
            "next_recommended": "observe enable --source file" if not boundary["enabled_sources"] else ("observe run" if "file" in boundary["enabled_sources"] else "observe run"),
        }
        out["local_sources"]["event_log_dir"] = str(event_log_dir.resolve())
    except Exception as e:
        out["observation_state"] = {"error": str(e)}

    # 6c. Live work context (M32) — current inferred project/task, work mode, recent shifts
    try:
        from workflow_dataset.live_context.state import get_live_context_state, get_recent_transitions
        live_dir = root / "data/local/live_context"
        current_ctx = get_live_context_state(root / "data/local")
        transitions = get_recent_transitions(root / "data/local", limit=10)
        if current_ctx is None:
            out["live_context_state"] = {
                "current_project": None,
                "current_work_mode": None,
                "confidence": 0,
                "is_stale": True,
                "recent_transitions_count": 0,
                "next_assist_opportunity": "run live-context now to compute context",
            }
        else:
            out["live_context_state"] = {
                "current_project": current_ctx.inferred_project.label if current_ctx.inferred_project else None,
                "current_task_family": current_ctx.inferred_task_family.label if current_ctx.inferred_task_family else None,
                "current_work_mode": current_ctx.work_mode.value,
                "activity_mode": current_ctx.activity_mode.value,
                "focus_state": current_ctx.focus_state.kind.value if current_ctx.focus_state else None,
                "confidence": current_ctx.overall_confidence,
                "is_stale": current_ctx.is_stale,
                "recent_transitions_count": len(transitions),
                "recent_transition_kinds": [t.kind.value for t in transitions[:5]],
                "next_assist_opportunity": "live-context explain" if current_ctx.is_stale else "assist or copilot recommend",
            }
        out["local_sources"]["live_context_dir"] = str(live_dir.resolve())
    except Exception as e:
        out["live_context_state"] = {"error": str(e)}

    # 6d. Memory curation (M44E–M44H) — growth pressure, compression candidates, protected, forgetting awaiting review, next action
    try:
        from workflow_dataset.memory_curation.report import mission_control_slice
        out["memory_curation_state"] = mission_control_slice(repo_root=root)
        out["local_sources"]["memory_curation_dir"] = str((root / "data/local/memory_curation").resolve())
    except Exception as e:
        out["memory_curation_state"] = {"error": str(e)}

    # 6e. Memory intelligence (M44I–M44L) — memory-backed recommendations, weak cautions, top prior case, next review
    try:
        from workflow_dataset.memory_intelligence.store import list_recent_recommendations
        from workflow_dataset.memory_intelligence.explanation import list_weak_memory_cautions
        recs = list_recent_recommendations(limit=50, repo_root=root)
        weak = list_weak_memory_cautions(limit=20, repo_root=root)
        weak_fusion = weak.get("weak_memories_from_fusion", [])
        weak_recs = weak.get("weak_cautions_from_recommendations", [])
        top_prior = None
        if recs:
            first = recs[0]
            prior = first.get("prior_cases") or []
            if prior:
                top_prior = {"recommendation_id": first.get("recommendation_id"), "snippet": (prior[0].get("snippet") or prior[0].get("relevance_summary", ""))[:120]}
        most_influential = recs[0] if recs else None
        out["memory_intelligence_state"] = {
            "memory_backed_recommendation_count": len(recs),
            "weak_memory_caution_count": len(weak_fusion) + len(weak_recs),
            "top_retrieved_prior_case": top_prior,
            "most_influential_recommendation_id": most_influential.get("recommendation_id") if most_influential else None,
            "next_recommended_memory_review": "memory-intelligence prior-cases --project <id> then memory-intelligence explain --id <rec_id>" if recs else "memory-intelligence suggest --project <id>",
        }
        out["local_sources"]["memory_intelligence_dir"] = str((root / "data/local/memory_intelligence").resolve())
    except Exception as e:
        out["memory_intelligence_state"] = {"error": str(e)}

    # 6f. Memory OS (M44A–M44D) — surfaces, weak-memory warnings, next review
    try:
        from workflow_dataset.memory_os.mission_control import memory_os_slice
        out["memory_os_state"] = memory_os_slice(repo_root=root)
        out["local_sources"]["memory_os"] = str((root / "data/local/memory_substrate").resolve())
    except Exception as e:
        out["memory_os_state"] = {"error": str(e)}

    # 6g. Shadow execution (M45E–M45H) — active shadow runs, lowest-confidence step, next gate, takeover candidate, safe-to-promote
    try:
        from workflow_dataset.shadow_execution.store import list_shadow_runs
        runs = list_shadow_runs(limit=20, repo_root=root)
        active = [r for r in runs if r.get("status") in ("pending", "running")]
        takeover_candidates = [r for r in runs if r.get("forced_takeover")]
        lowest_conf_run = None
        lowest_conf_score = 1.0
        for r in runs[:10]:
            run_full = None
            try:
                from workflow_dataset.shadow_execution.store import load_shadow_run
                run_full = load_shadow_run(r["shadow_run_id"], repo_root=root)
            except Exception:
                pass
            if run_full and run_full.get("confidence_loop"):
                sc = run_full["confidence_loop"].get("score", 1.0)
                if sc < lowest_conf_score:
                    lowest_conf_score = sc
                    lowest_conf_run = r.get("shadow_run_id")
        next_gate_run = takeover_candidates[0] if takeover_candidates else (runs[0] if runs else None)
        safe_to_promote = next((r for r in runs if r.get("status") == "completed" and not r.get("forced_takeover")), None)
        out["shadow_execution_state"] = {
            "active_shadow_run_count": len(active),
            "lowest_confidence_run_id": lowest_conf_run,
            "lowest_confidence_score": lowest_conf_score if lowest_conf_run else None,
            "next_intervention_gate_run_id": next_gate_run.get("shadow_run_id") if next_gate_run else None,
            "forced_takeover_candidate_count": len(takeover_candidates),
            "recent_safe_to_promote_run_id": safe_to_promote.get("shadow_run_id") if safe_to_promote else None,
        }
        out["local_sources"]["shadow_execution_dir"] = str((root / "data/local/shadow_execution").resolve())
    except Exception as e:
        out["shadow_execution_state"] = {"error": str(e)}

    # 6h. Adaptive execution (M45A–M45D) — active loop, next step, remaining steps, takeover point
    try:
        from workflow_dataset.adaptive_execution.mission_control import adaptive_execution_slice
        out["adaptive_execution_state"] = adaptive_execution_slice(repo_root=root)
        out["local_sources"]["adaptive_execution"] = str((root / "data/local/adaptive_execution").resolve())
    except Exception as e:
        out["adaptive_execution_state"] = {"error": str(e)}

    # 6i. M46E–M46H Repair loops — top repair-needed, active loop, failed requiring escalation, verified, next action
    try:
        from workflow_dataset.repair_loops.mission_control import repair_loops_mission_control_slice
        out["repair_loops_state"] = repair_loops_mission_control_slice(repo_root=root)
        out["local_sources"]["repair_loops"] = str((root / "data/local/repair_loops").resolve())
    except Exception as e:
        out["repair_loops_state"] = {"error": str(e)}

    # 6j. M47A–M47D Vertical excellence (Pane 1) — first-value stage, friction, recommend-next, blocked cases
    try:
        from workflow_dataset.vertical_excellence.mission_control import vertical_excellence_slice
        out["vertical_excellence_state"] = vertical_excellence_slice(repo_root=root)
    except Exception as e:
        out["vertical_excellence_state"] = {"error": str(e)}

    # 6j2. M47E–M47H Vertical speed (Pane 2) — top workflow, friction cluster, speed-up candidate, repeat-value bottleneck
    try:
        from workflow_dataset.vertical_speed.mission_control import vertical_speed_slice
        out["vertical_speed_state"] = vertical_speed_slice(repo_root=root)
    except Exception as e:
        out["vertical_speed_state"] = {"error": str(e)}

    # 6j3. M48A–M48D Governance — role map, scope-bound authority, blocked attempts, next review
    try:
        from workflow_dataset.governance.mission_control import governance_slice
        out["governance_state"] = governance_slice(repo_root=root)
    except Exception as e:
        out["governance_state"] = {"error": str(e)}

    # 6j4. M49A–M49D Continuity bundle — latest bundle, transfer-sensitive, excluded local-only
    try:
        from workflow_dataset.continuity_bundle.mission_control import continuity_bundle_slice
        out["continuity_bundle_state"] = continuity_bundle_slice(repo_root=root)
    except Exception as e:
        out["continuity_bundle_state"] = {"error": str(e)}

    # 6k. M48E–M48H Review domains — active domains, domain-blocked approvals, required escalations, most sensitive pending
    try:
        from workflow_dataset.review_domains.mission_control import review_domains_mission_control_slice
        out["review_domains_state"] = review_domains_mission_control_slice(repo_root=root)
    except Exception as e:
        out["review_domains_state"] = {"error": str(e)}

    # 6l. M49E–M49H Migration restore — latest candidate, blockers, reconcile-required, confidence, next action
    try:
        from workflow_dataset.migration_restore.mission_control import migration_restore_mission_control_slice
        out["migration_restore_state"] = migration_restore_mission_control_slice(repo_root=root)
    except Exception as e:
        out["migration_restore_state"] = {"error": str(e)}

    # 6m. M50A–M50D V1 contract — active contract, quarantined, excluded, next freeze action
    try:
        from workflow_dataset.v1_contract.mission_control import v1_contract_slice
        out["v1_contract_state"] = v1_contract_slice(repo_root=root)
    except Exception as e:
        out["v1_contract_state"] = {"error": str(e)}

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

    # 9a. Action cards (M32I–M32L) — guided action cards, handoffs, blocked, outcomes
    try:
        from workflow_dataset.action_cards.store import load_all_cards, list_cards
        from workflow_dataset.action_cards.models import CardState, TrustRequirement
        all_cards = load_all_cards(root)
        pending = list_cards(root, state=CardState.PENDING, limit=50)
        accepted = list_cards(root, state=CardState.ACCEPTED, limit=50)
        executed = list_cards(root, state=CardState.EXECUTED, limit=20)
        blocked = list_cards(root, state=CardState.BLOCKED, limit=20)
        approval_required = [c for c in all_cards if c.trust_requirement == TrustRequirement.APPROVAL_REQUIRED and c.state in (CardState.PENDING, CardState.ACCEPTED)]
        highest = (pending + accepted)[:1]
        recent_outcomes = [(c.card_id, c.outcome_summary or "—") for c in executed[:5]]
        out["action_cards_summary"] = {
            "total_cards": len(all_cards),
            "pending_count": len(pending),
            "accepted_count": len(accepted),
            "executed_count": len(executed),
            "blocked_count": len(blocked),
            "awaiting_approval_count": len(approval_required),
            "highest_value_card": highest[0].to_dict() if highest else None,
            "blocked_card_ids": [c.card_id for c in blocked[:10]],
            "recent_executed_card_ids": [c.card_id for c in executed[:10]],
            "recent_outcomes": recent_outcomes,
            "next_action": "action-cards list" if all_cards else "action-cards refresh",
        }
        out["local_sources"]["action_cards"] = str((root / "data/local/action_cards").resolve())
    except Exception as e:
        out["action_cards_summary"] = {"error": str(e)}

    # 9a1. M34A–M34D Trigger engine + recurring workflow definitions — active/suppressed/blocked triggers, last matched, next scheduled
    try:
        from workflow_dataset.automations.evaluate import evaluate_active_triggers
        _, summary = evaluate_active_triggers(repo_root=root)
        out["automations_state"] = {
            "active_trigger_ids": summary.active_trigger_ids,
            "suppressed_trigger_ids": summary.suppressed_trigger_ids,
            "blocked_trigger_ids": summary.blocked_trigger_ids,
            "last_matched_trigger_id": summary.last_matched_trigger_id or None,
            "next_scheduled_workflow_id": summary.next_scheduled_workflow_id or None,
        }
        out["local_sources"]["automations"] = str((root / "data/local/automations").resolve())
    except Exception as e:
        out["automations_state"] = {"error": str(e)}

    # 9b. M34E–M34H Bounded background runner — active runs, blocked, retryable, next, outcomes, needs review
    try:
        from workflow_dataset.background_run.runner import build_run_summary
        summary = build_run_summary(repo_root=root, recent_limit=10)
        out["background_runner_state"] = {
            "active_run_ids": summary.active_run_ids,
            "blocked_run_ids": summary.blocked_run_ids,
            "retryable_run_ids": summary.retryable_run_ids,
            "next_automation_id": summary.next_automation_id,
            "next_plan_ref": summary.next_plan_ref,
            "queue_length": summary.queue_length,
            "recent_outcomes": summary.recent_outcomes[:10],
            "needs_review_automation_ids": summary.needs_review_automation_ids,
            "next_action": "background run" if summary.queue_length else "background queue --add <id> --plan-ref <ref>",
        }
        out["local_sources"]["background_run"] = str((root / "data/local/background_run").resolve())
    except Exception as e:
        out["background_runner_state"] = {"error": str(e)}

    # 9b2. M34I–M34L Automation inbox — unseen results, most important blocked, latest digest, next follow-up; M34L.1 handoff
    try:
        from workflow_dataset.automation_inbox import (
            build_automation_inbox,
            build_morning_automation_digest,
            get_recommended_handoff,
        )
        items = build_automation_inbox(repo_root=root, status="pending", limit=50)
        unseen_count = len(items)
        most_important_blocked = ""
        for i in items:
            if i.kind in ("blocked_automation", "failed_suppressed_automation"):
                most_important_blocked = i.item_id
                break
        digest = build_morning_automation_digest(repo_root=root, runs_limit=20)
        handoff = get_recommended_handoff(repo_root=root)
        out["automation_inbox"] = {
            "unseen_automation_results_count": unseen_count,
            "most_important_blocked_automation_id": most_important_blocked or None,
            "latest_recurring_digest_id": digest.digest_id,
            "latest_digest_generated_at": digest.generated_at[:19],
            "background_completed_since_session_label": "recent runs" if unseen_count else "no pending",
            "next_recommended_follow_up": digest.most_important_follow_up,
            "recommended_handoff_label": handoff.label if handoff else None,
            "recommended_handoff_command": handoff.command if handoff else None,
        }
        out["local_sources"]["automation_inbox"] = str((root / "data/local/automation_inbox").resolve())
    except Exception as e:
        out["automation_inbox"] = {"error": str(e)}

    # 9b3. M35I–M35L Sensitive gates + audit ledger — pending gates, latest signed-off, rejected/deferred, audit anomalies, next sign-off
    try:
        from workflow_dataset.sensitive_gates import load_gates, load_ledger_entries
        gates = load_gates(repo_root=root)
        pending = [g for g in gates if g.status == "pending"]
        rejected_deferred = [g for g in gates if g.status in ("rejected", "deferred")]
        latest_signed = [g for g in gates if g.status == "approved"][:10]
        ledger = load_ledger_entries(repo_root=root, limit=50)
        anomalies = [e for e in ledger if e.execution_result and e.execution_result.outcome in ("failed", "blocked")][:5]
        next_signoff_id = pending[0].gate_id if pending else None
        out["sensitive_gates"] = {
            "pending_gate_ids": [g.gate_id for g in pending],
            "pending_count": len(pending),
            "latest_signed_off_gate_ids": [g.gate_id for g in latest_signed],
            "rejected_deferred_gate_ids": [g.gate_id for g in rejected_deferred],
            "recent_audit_anomaly_entry_ids": [e.entry_id for e in anomalies],
            "next_required_signoff_gate_id": next_signoff_id,
            "next_action": "gates list" if pending else "gates show --id <gate_id>",
        }
        out["local_sources"]["sensitive_gates"] = str((root / "data/local/sensitive_gates").resolve())
    except Exception as e:
        out["sensitive_gates"] = {"error": str(e)}

    # 9a2. Workflow episodes (M33A–M33D) — current episode, stage, handoff gaps, recent transitions
    try:
        from workflow_dataset.workflow_episodes.store import get_current_episode, load_recent_transitions
        from workflow_dataset.workflow_episodes.stage_detection import infer_stage, infer_handoff_gaps, infer_next_step_candidates
        current = get_current_episode(root)
        transitions = load_recent_transitions(root, limit=10)
        if current is None:
            out["workflow_episodes"] = {
                "current_episode_id": None,
                "current_stage": None,
                "likely_next_step": None,
                "handoff_gaps_count": 0,
                "handoff_gaps_summary": [],
                "recent_transitions_count": len(transitions),
                "recent_transition_kinds": [t.kind for t in transitions[:5]],
                "next_action": "workflow-episodes now (after observe run)",
            }
        else:
            stage, _ = infer_stage(current)
            gaps = infer_handoff_gaps(current, root)
            next_candidates = infer_next_step_candidates(current)
            out["workflow_episodes"] = {
                "current_episode_id": current.episode_id,
                "current_stage": stage.value,
                "activities_count": len(current.linked_activities),
                "project_label": current.inferred_project.label if current.inferred_project else None,
                "likely_next_step": next_candidates[0].label if next_candidates else None,
                "handoff_gaps_count": len(gaps),
                "handoff_gaps_summary": [g.summary for g in gaps[:5]],
                "recent_transitions_count": len(transitions),
                "recent_transition_kinds": [t.kind for t in transitions[:5]],
                "next_action": "workflow-episodes stage --latest" if gaps else "workflow-episodes explain --latest",
            }
        out["local_sources"]["workflow_episodes"] = str((root / "data/local/workflow_episodes").resolve())
    except Exception as e:
        out["workflow_episodes"] = {"error": str(e)}

    # 9a3. Live workflow (M33E–M33H) — active run, current step, escalation, blocked, next assist
    try:
        from workflow_dataset.live_workflow.state import get_live_workflow_run
        run = get_live_workflow_run(repo_root=root)
        if run is None:
            out["live_workflow_state"] = {
                "active_run_id": None,
                "current_step_index": None,
                "escalation_level": None,
                "blocked_real_time_step": None,
                "next_recommended_assist": None,
                "state": "no_workflow",
                "next_action": "live-workflow now --goal \"<goal>\"",
            }
        else:
            current = run.steps[run.current_step_index] if run.steps and run.current_step_index < len(run.steps) else None
            out["live_workflow_state"] = {
                "active_run_id": run.run_id,
                "goal_text": (run.goal_text or "")[:100],
                "plan_ref": run.plan_ref,
                "bundle_id": run.bundle_id or None,
                "current_step_index": run.current_step_index,
                "next_step_index": run.next_step_index,
                "escalation_level": run.current_escalation_tier.value,
                "blocked_real_time_step": run.blocked_step.model_dump() if run.blocked_step else None,
                "next_recommended_assist": current.hint_text if current else (run.escalation_path_summary or ""),
                "state": run.state.value,
                "steps_count": len(run.steps),
                "alternate_path_recommendations_count": len(run.alternate_path_recommendations),
                "next_action": "live-workflow steps --latest" if run.steps else "live-workflow now --goal \"<goal>\"",
            }
            # M33H.1: Stall detection for mission control
            try:
                from workflow_dataset.live_workflow.stall import detect_stall, suggest_recovery_paths
                stall_result = detect_stall(run, idle_threshold_seconds=600.0)
                stall_result.suggested_recovery_paths = suggest_recovery_paths(run, stall_result, root)
                if run.alternate_path_recommendations:
                    from workflow_dataset.live_workflow.models import AlternatePathRecommendation
                    stall_result.alternate_paths = [AlternatePathRecommendation.model_validate(a) for a in run.alternate_path_recommendations]
                out["live_workflow_state"]["stall_detected"] = stall_result.stalled
                out["live_workflow_state"]["stall_reason"] = stall_result.reason if stall_result.stalled else None
                out["live_workflow_state"]["recovery_paths_count"] = len(stall_result.suggested_recovery_paths)
            except Exception:
                out["live_workflow_state"]["stall_detected"] = False
                out["live_workflow_state"]["stall_reason"] = None
        out["local_sources"]["live_workflow"] = str((root / "data/local/live_workflow").resolve())
    except Exception as e:
        out["live_workflow_state"] = {"error": str(e)}

    # 9b. Personal work graph (M31E–M31H) — routines, patterns, uncertain
    try:
        from workflow_dataset.personal.graph_reports import (
            graph_status,
            list_recent_routines,
            list_strong_patterns,
            uncertain_patterns,
        )
        st = graph_status(repo_root=root)
        recent_routines = list_recent_routines(repo_root=root, limit=10)
        strong = list_strong_patterns(repo_root=root, min_confidence=0.5, limit=15)
        uncertain = uncertain_patterns(repo_root=root, max_confidence=0.65, limit=10)
        # M31H.1 graph review inbox counts
        try:
            from workflow_dataset.personal.graph_review_inbox import list_pending_routines, list_pending_patterns
            pending_routines = list_pending_routines(repo_root=root, limit=100)
            pending_patterns = list_pending_patterns(repo_root=root, limit=100)
        except Exception:
            pending_routines = []
            pending_patterns = []
        out["personal_graph_summary"] = {
            "graph_exists": st.get("exists", False),
            "nodes_total": st.get("nodes_total", 0),
            "edges_total": st.get("edges_total", 0),
            "routines_count": st.get("routines_count", 0),
            "projects_count": st.get("projects_count", 0),
            "tool_apps_count": st.get("tool_apps_count", 0),
            "recently_learned_routines": [r.get("label") for r in recent_routines[:5]],
            "strongest_patterns_count": len(strong),
            "strong_pattern_types": list({p.get("pattern_type") for p in strong if p.get("pattern_type")}),
            "uncertain_patterns_count": len(uncertain),
            "uncertain_needing_confirmation": [p.get("pattern_type") for p in uncertain[:5]],
            "graph_review_pending_routines": len(pending_routines),
            "graph_review_pending_patterns": len(pending_patterns),
            "next_action": "personal graph ingest" if st.get("exists") else "observe then personal graph ingest",
        }
        out["local_sources"]["personal_graph"] = st.get("graph_path", "")
    except Exception as e:
        out["personal_graph_summary"] = {"error": str(e)}

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

    # 10b. Teaching / skills (M26I–M26L) — candidate skills, recently accepted, pack-linked, needing review
    try:
        from workflow_dataset.teaching.skill_store import list_skills
        from workflow_dataset.teaching.report import build_skill_report
        skill_report = build_skill_report(repo_root=root)
        out["teaching_skills"] = {
            "candidate_skills_count": skill_report.get("draft_count", 0),
            "candidate_skill_ids": skill_report.get("draft_ids", [])[:10],
            "recently_accepted_skills": skill_report.get("recent_accepted", [])[:5],
            "pack_linked_skills_count": skill_report.get("pack_linked_count", 0),
            "pack_linked_skill_ids": skill_report.get("pack_linked_ids", [])[:10],
            "skills_needing_review_count": skill_report.get("needing_review_count", 0),
            "skills_needing_review_ids": skill_report.get("needing_review_ids", [])[:10],
        }
        out["local_sources"]["teaching_skills"] = str((root / "data/local/teaching/skills").resolve())
    except Exception as e:
        out["teaching_skills"] = {"error": str(e)}

    # 11. Runtime mesh (M23T/M23S) + M42A–M42D model registry/routing — backends, catalog, recommend, integrations, summary, validation, llama.cpp optional
    try:
        from workflow_dataset.runtime_mesh.backend_registry import list_backend_profiles
        from workflow_dataset.runtime_mesh.model_catalog import load_model_catalog
        from workflow_dataset.runtime_mesh.policy import recommend_for_task_class
        from workflow_dataset.runtime_mesh.integration_registry import list_integrations
        from workflow_dataset.runtime_mesh.summary import build_runtime_summary
        from workflow_dataset.runtime_mesh.validate import run_runtime_validate
        from workflow_dataset.runtime_mesh.llama_cpp_check import llama_cpp_check
        backends = list_backend_profiles(root)
        available = [b.backend_id for b in backends if b.status in ("available", "configured")]
        missing = [b.backend_id for b in backends if b.status == "missing"]
        rec_copilot = recommend_for_task_class("desktop_copilot", root)
        rec_code = recommend_for_task_class("codebase_task", root)
        integrations = list_integrations(root)
        runtime_summary = build_runtime_summary(root)
        validation = run_runtime_validate(root, include_models=False)
        llama = llama_cpp_check(root)
        # M42A–M42D: model registry and task-aware routing visibility
        try:
            from workflow_dataset.runtime_mesh.routing import availability_check, route_for_task, TASK_FAMILIES
            avail = availability_check(root)
            production_safe_routes = len([tf for tf in TASK_FAMILIES if tf in (avail.get("task_families_with_route") or [])])
            degraded_or_missing = (avail.get("missing_backend_ids") or []) + (avail.get("task_families_degraded") or [])
            most_used_route_task = "desktop_copilot" if rec_copilot.get("backend_id") else (rec_code.get("backend_id") and "codebase_task" or "")
            next_recommended_runtime_review = "workflow-dataset models fallback-report" if (avail.get("task_families_degraded") or avail.get("missing_backend_ids")) else "workflow-dataset models availability"
        except Exception:
            production_safe_routes = 0
            degraded_or_missing = []
            most_used_route_task = ""
            next_recommended_runtime_review = "workflow-dataset models availability"
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
            "runtime_validation_passed": validation.get("passed", False),
            "task_class_dependencies_count": len(runtime_summary.get("task_class_dependencies") or []),
            "llama_cpp_available": llama.get("available", False),
            "llama_cpp_status": llama.get("status", "optional"),
            "active_registry_count": len(load_model_catalog(root)),
            "production_safe_route_count": production_safe_routes,
            "degraded_or_missing_runtimes": degraded_or_missing[:10],
            "most_used_route_task": most_used_route_task,
            "next_recommended_runtime_review": next_recommended_runtime_review,
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

    # 13. M23V/M23Q Trust cockpit summary (additive: benchmark, approval, release gates, safe_to_expand)
    try:
        from workflow_dataset.trust.cockpit import build_trust_cockpit
        cockpit = build_trust_cockpit(root)
        gate_checks = cockpit.get("release_gate_checks") or []
        out["trust_cockpit"] = {
            "benchmark_trust_status": (cockpit.get("benchmark_trust") or {}).get("latest_trust_status"),
            "approval_registry_exists": (cockpit.get("approval_readiness") or {}).get("registry_exists"),
            "release_gate_staged_count": (cockpit.get("release_gate_status") or {}).get("staged_count", 0),
            "safe_to_expand": cockpit.get("safe_to_expand", False),
            "failed_gates": cockpit.get("failed_gates", []),
            "release_gate_checks_summary": [{"name": c.get("name"), "passed": c.get("passed")} for c in gate_checks[:10]],
        }
    except Exception as e:
        out["trust_cockpit"] = {"error": str(e)}

    # 13b. M35A–M35D Authority / trust contracts (additive)
    try:
        from workflow_dataset.trust.tiers import list_tiers, get_tier
        from workflow_dataset.trust.contracts import load_contracts
        from workflow_dataset.trust.scope import effective_contract
        from workflow_dataset.trust.explain_contract import explain_routine
        contracts = load_contracts(root)
        enabled_contracts = [c for c in contracts if c.enabled]
        tier_list = list_tiers()
        # Active authority tier posture: highest tier order among contracts in effect
        max_order = -1
        active_tier_id = ""
        for c in enabled_contracts:
            t = get_tier(c.authority_tier_id)
            if t and t.order > max_order:
                max_order = t.order
                active_tier_id = t.tier_id
        trusted_routine_ids = list({c.routine_id for c in enabled_contracts})
        blocked_routines: list[str] = []
        for c in enabled_contracts:
            exp = explain_routine(c.routine_id, context={}, repo_root=root)
            if exp.get("blocked"):
                blocked_routines.append(c.routine_id)
        from workflow_dataset.trust.scope import SCOPE_ORDER
        def _scope_rank(s: str) -> int:
            base = s.split(":")[0] if s and ":" in s else (s or "")
            try:
                return SCOPE_ORDER.index(base)
            except ValueError:
                return 0
        best_scope = "global"
        best_rank = -1
        for c in enabled_contracts:
            r = _scope_rank(c.scope)
            if r > best_rank:
                best_rank = r
                best_scope = c.scope
        out["authority_contracts_state"] = {
            "active_tier_posture": active_tier_id or "none",
            "trusted_routines_in_effect": trusted_routine_ids[:50],
            "trusted_routines_count": len(trusted_routine_ids),
            "routines_blocked_by_contract": blocked_routines[:30],
            "contracts_count": len(enabled_contracts),
            "highest_authority_scope": best_scope,
            "next_trust_review": "trust contracts list" if enabled_contracts else "add contracts in data/local/trust/contracts.json",
        }
        out["local_sources"]["trust_contracts"] = str((root / "data/local/trust").resolve())
    except Exception as e:
        out["authority_contracts_state"] = {"error": str(e)}

    # 13c. M35E–M35H Personal operator mode — pause state, revocation count, bundles, next action
    try:
        from workflow_dataset.operator_mode import (
            load_pause_state,
            load_suspension_revocation_state,
            list_responsibility_ids,
            list_bundle_ids,
        )
        pause = load_pause_state(repo_root=root)
        rev_state = load_suspension_revocation_state(repo_root=root)
        resp_ids = list_responsibility_ids(repo_root=root)
        bundle_ids = list_bundle_ids(repo_root=root)
        out["operator_mode_state"] = {
            "pause_kind": pause.kind.value,
            "pause_reason": pause.reason or "",
            "suspended_responsibility_count": len(rev_state.suspended_ids),
            "suspended_bundle_count": len(rev_state.suspended_bundle_ids),
            "responsibilities_count": len(resp_ids),
            "bundles_count": len(bundle_ids),
            "next_action": "operator-mode status" if not pause.kind.value or pause.kind.value == "none" else "operator-mode pause --clear to resume",
        }
        out["local_sources"]["operator_mode"] = str((root / "data/local/operator_mode").resolve())
    except Exception as e:
        out["operator_mode_state"] = {"error": str(e)}

    # 13d. M48I–M48L Governed operator mode + delegation safety
    try:
        from workflow_dataset.governed_operator import governed_operator_slice
        out["governed_operator_state"] = governed_operator_slice(repo_root=root)
        out["local_sources"]["governed_operator"] = str((root / "data/local/governed_operator").resolve())
    except Exception as e:
        out["governed_operator_state"] = {"error": str(e)}

    # 13e. M49I–M49L Continuity confidence (device-aware post-restore)
    try:
        from workflow_dataset.continuity_confidence import continuity_confidence_slice
        out["continuity_confidence_state"] = continuity_confidence_slice(repo_root=root)
    except Exception as e:
        out["continuity_confidence_state"] = {"error": str(e)}

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

    # 14b. M36A–M36D Workday state — current mode, pending transition, blocked, day progress, next best action
    try:
        from workflow_dataset.workday.store import load_workday_state
        from workflow_dataset.workday.surface import build_daily_operating_surface
        record = load_workday_state(root)
        surf = build_daily_operating_surface(root)
        out["workday_state"] = {
            "current_workday_mode": record.state,
            "state_entered_at_iso": record.entered_at_iso,
            "day_id": record.day_id,
            "day_started_at_iso": record.day_started_at_iso,
            "pending_state_transition_recommendation": surf.next_recommended_transition,
            "pending_transition_reason": surf.next_recommended_reason,
            "blocked_mode_transitions": [{"to": b.to_state, "reason": b.reason[:80]} for b in surf.blocked_transitions[:10]],
            "day_progress_snapshot": {
                "active_project_id": surf.active_project_id,
                "pending_approvals_count": surf.pending_approvals_count,
                "allowed_next_states": surf.allowed_next_states[:10],
            },
            "next_best_operating_action": surf.next_recommended_reason or f"day {surf.next_recommended_transition}" if surf.next_recommended_transition else "day status",
        }
        out["local_sources"]["workday"] = str((root / "data/local/workday").resolve())
    except Exception as e:
        out["workday_state"] = {"error": str(e)}

    # 14c. M37 Default experience — active profile, simplified mode mapping, advanced surfaces hidden, next default entry action
    try:
        from workflow_dataset.default_experience.store import get_active_default_profile_id
        from workflow_dataset.default_experience.profiles import get_profile
        from workflow_dataset.default_experience.modes import internal_state_to_user_mode, get_simplified_mode_mapping
        from workflow_dataset.default_experience.surfaces import surfaces_hidden_by_default
        from workflow_dataset.default_experience.onboarding_defaults import recommended_first_command
        profile_id = get_active_default_profile_id(repo_root=root)
        profile = get_profile(profile_id) if profile_id else None
        current_internal = out.get("workday_state", {}).get("current_workday_mode") or "not_started"
        user_mode = internal_state_to_user_mode(current_internal)
        mapping = get_simplified_mode_mapping()
        hidden = surfaces_hidden_by_default()
        next_entry = (profile.default_entry_command if profile and profile.default_entry_command else recommended_first_command())
        out["default_experience_state"] = {
            "active_profile_id": profile_id or "calm_default",
            "simplified_mode_for_current_state": user_mode,
            "simplified_mode_set": [m["mode_id"] for m in mapping],
            "advanced_surfaces_hidden_by_default_count": len(hidden),
            "next_recommended_default_entry_action": next_entry,
        }
    except Exception as e:
        out["default_experience_state"] = {"error": str(e)}

    # 14c2. M38A–M38D Cohort profile — active cohort, supported/experimental/blocked counts, blocked sample, trust posture, next readiness review
    try:
        from workflow_dataset.cohort.store import get_active_cohort_id
        from workflow_dataset.cohort.profiles import get_cohort_profile
        from workflow_dataset.cohort.surface_matrix import get_supported_surfaces, get_experimental_surfaces, get_blocked_surfaces
        active_id = get_active_cohort_id(repo_root=root)
        profile = get_cohort_profile(active_id) if active_id else None
        if profile:
            supported = get_supported_surfaces(active_id)
            experimental = get_experimental_surfaces(active_id)
            blocked = get_blocked_surfaces(active_id)
            gates_summary = ""
            recommended_transition = None
            try:
                from workflow_dataset.cohort.gates import get_gates_for_cohort, evaluate_gates
                from workflow_dataset.cohort.transitions import get_recommended_transition
                gates = get_gates_for_cohort(active_id)
                if gates:
                    results = evaluate_gates(active_id, root)
                    passed = sum(1 for r in results if r.get("passed"))
                    gates_summary = f"{passed}/{len(gates)} pass"
                rec = get_recommended_transition(active_id, root)
                if rec:
                    recommended_transition = {"direction": rec.get("direction"), "suggested_cohort_id": rec.get("suggested_cohort_id"), "reason": (rec.get("reason") or "")[:80]}
            except Exception:
                pass
            out["cohort_state"] = {
                "active_cohort_id": active_id,
                "cohort_label": profile.label,
                "supported_count": len(supported),
                "experimental_count": len(experimental),
                "blocked_count": len(blocked),
                "blocked_surfaces_sample": blocked[:10],
                "trust_posture": f"allowed_tiers={len(profile.allowed_trust_tier_ids)}  automation_scope={profile.allowed_automation_scope}",
                "required_readiness": profile.required_readiness,
                "next_readiness_review": f"workflow-dataset cohort explain --id {active_id}",
                "gates_summary": gates_summary,
                "recommended_transition": recommended_transition,
            }
        else:
            out["cohort_state"] = {
                "active_cohort_id": "",
                "cohort_label": "",
                "supported_count": 0,
                "experimental_count": 0,
                "blocked_count": 0,
                "blocked_surfaces_sample": [],
                "trust_posture": "",
                "required_readiness": "",
                "next_readiness_review": "workflow-dataset cohort profiles",
                "gates_summary": "",
                "recommended_transition": None,
            }
    except Exception as e:
        out["cohort_state"] = {"error": str(e)}

    # 14c3. M39A–M39D Vertical selection — recommended primary/secondary, active vertical, surfaces hidden by scope
    try:
        from workflow_dataset.vertical_selection import (
            get_active_vertical_id,
            recommend_primary_secondary,
            get_surfaces_hidden_by_scope,
        )
        active_id = get_active_vertical_id(repo_root=root)
        rec = recommend_primary_secondary(root)
        primary_id = (rec.get("primary") or {}).get("vertical_id") or ""
        primary_label = (rec.get("primary") or {}).get("label") or ""
        secondary_id = (rec.get("secondary") or {}).get("vertical_id") or ""
        secondary_label = (rec.get("secondary") or {}).get("label") or ""
        hidden_count = 0
        if active_id:
            hidden = get_surfaces_hidden_by_scope(active_id)
            hidden_count = len(hidden)
        out["vertical_selection_state"] = {
            "recommended_primary_vertical_id": primary_id,
            "recommended_primary_vertical_label": primary_label,
            "recommended_secondary_vertical_id": secondary_id,
            "recommended_secondary_vertical_label": secondary_label,
            "active_vertical_id": active_id,
            "surfaces_hidden_by_scope_count": hidden_count,
            "next_scope_review": "workflow-dataset verticals scope-report",
        }
    except Exception as e:
        out["vertical_selection_state"] = {"error": str(e)}

    # 14b. M36I–M36L Continuity engine — next start-of-day action, resume target, carry-forward, unresolved blocker, end-of-day readiness
    try:
        from workflow_dataset.continuity_engine import (
            build_morning_entry_flow,
            get_strongest_resume_target,
            build_carry_forward_list,
            load_last_shutdown,
        )
        morning = build_morning_entry_flow(repo_root=root)
        resume_label, resume_cmd = get_strongest_resume_target(root)
        carry = build_carry_forward_list(root)
        last_shut = load_last_shutdown(root)
        most_important_carry = carry[0].label[:80] if carry else None
        unresolved_blocker = None
        if last_shut and last_shut.blocked_or_high_risk:
            unresolved_blocker = last_shut.blocked_or_high_risk[0][:80]
        end_of_day_readiness = last_shut.end_of_day_readiness if last_shut else ""
        out["continuity_engine_state"] = {
            "next_best_start_of_day_action": morning.recommended_first_command or "workflow-dataset continuity morning",
            "strongest_resume_target_label": resume_label,
            "strongest_resume_target_command": resume_cmd,
            "most_important_carry_forward": most_important_carry,
            "unresolved_blocker_carried": unresolved_blocker,
            "end_of_day_readiness": end_of_day_readiness or "unknown",
        }
        out["local_sources"]["continuity_engine"] = str((root / "data/local/continuity_engine").resolve())
    except Exception as e:
        out["continuity_engine_state"] = {"error": str(e)}

    # 14d. M37I–M37L State durability — state health, resume quality, stale/corrupt warnings, recommended recovery
    try:
        from workflow_dataset.state_durability import (
            build_startup_readiness,
            build_resume_target,
            build_startup_readiness_summary,
        )
        readiness = build_startup_readiness(repo_root=root)
        target = build_resume_target(repo_root=root)
        summary = build_startup_readiness_summary(repo_root=root)
        corrupt_count = len(readiness.corrupt_notes)
        stale_count = len(readiness.stale_markers)
        recommended_recovery = "workflow-dataset state health" if corrupt_count else (readiness.recommended_first_action or "workflow-dataset continuity morning")
        out["state_durability_state"] = {
            "state_health_ready": readiness.ready,
            "degraded_but_usable": readiness.degraded_but_usable,
            "resume_target_label": target.label,
            "resume_target_command": target.command,
            "resume_quality": target.quality,
            "stale_or_corrupt_warnings": corrupt_count + stale_count,
            "corrupt_count": corrupt_count,
            "stale_count": stale_count,
            "recommended_recovery_action": recommended_recovery,
            "startup_summary_lines": summary[:5],
        }
        out["local_sources"]["state_durability"] = str((root / "data/local/state_durability").resolve())
    except Exception as e:
        out["state_durability_state"] = {"error": str(e)}

    # 15. M23P Macro composer: available macros, last run, paused, awaiting approval, blocked
    try:
        from workflow_dataset.macros.runner import list_macros
        from workflow_dataset.macros.run_state import (
            list_paused_runs,
            list_awaiting_approval_runs,
            list_all_macro_runs,
        )
        macros = list_macros(root)
        paused = list_paused_runs(root, limit=20)
        awaiting = list_awaiting_approval_runs(root, limit=20)
        recent = list_all_macro_runs(root, limit=10)
        last_run = recent[0] if recent else None
        out["macros"] = {
            "available_count": len(macros),
            "macro_trust_levels": [getattr(m, "mode", "simulate") for m in macros],
            "last_macro_run": {
                "run_id": last_run.get("run_id"),
                "macro_id": last_run.get("macro_id"),
                "status": last_run.get("status"),
                "executed_count": len(last_run.get("executed") or []),
            } if last_run else None,
            "paused_runs_count": len(paused),
            "paused_run_ids": [r.get("run_id") for r in paused],
            "awaiting_approval_count": len(awaiting),
            "awaiting_approval_run_ids": [r.get("run_id") for r in awaiting],
            "blocked_run_ids": [r.get("run_id") for r in recent if r.get("status") == "blocked"],
        }
    except Exception as e:
        out["macros"] = {"error": str(e)}

    # 16. M23W Environment health and incubator presence (additive)
    try:
        from workflow_dataset.validation.env_health import check_environment_health
        health = check_environment_health(root)
        out["environment_health"] = {
            "required_ok": health.get("required_ok", False),
            "optional_ok": health.get("optional_ok", False),
            "python_version": health.get("python_version", ""),
            "incubator_present": health.get("incubator_present", False),
        }
    except Exception as e:
        out["environment_health"] = {"error": str(e)}

    # 17. M23Y Starter kits — recommended kit from profile (additive)
    try:
        from workflow_dataset.starter_kits.recommend import recommend_kit_from_profile
        from workflow_dataset.starter_kits.registry import list_kits
        rec = recommend_kit_from_profile(profile=None, repo_root=root)
        kits = list_kits()
        kit = rec.get("kit")
        out["starter_kits"] = {
            "kits_count": len(kits),
            "recommended_kit_id": getattr(kit, "kit_id", None) if kit else None,
            "recommended_kit_name": getattr(kit, "name", None) if kit else None,
            "score": rec.get("score", 0),
        }
    except Exception as e:
        out["starter_kits"] = {"error": str(e)}

    # 18. M24A External capability activation — recommended, blocked, missing prereqs, plans pending review
    try:
        from workflow_dataset.external_capability.planner import plan_activations
        from workflow_dataset.external_capability.registry import list_external_sources
        from workflow_dataset.external_capability.plans import build_activation_plan
        result = plan_activations(repo_root=root)
        sources = list_external_sources(root)
        recommended_ids = [r.source_id for r in result.recommended]
        blocked_ids = [b.source_id for b in result.rejected_by_policy] + [b.source_id for b in result.not_worth_it]
        missing_prereqs = result.prerequisite_steps
        plans_pending = [s.source_id for s in sources if s.activation_status in ("missing", "not_installed") and s.source_id in recommended_ids]
        out["external_capabilities"] = {
            "recommended": recommended_ids[:30],
            "recommended_count": len(result.recommended),
            "blocked": blocked_ids[:30],
            "blocked_count": len(result.rejected_by_policy) + len(result.not_worth_it),
            "missing_prerequisites": missing_prereqs[:20],
            "plans_pending_review": plans_pending[:20],
            "resource_estimate": result.resource_estimate,
        }
    except Exception as e:
        out["external_capabilities"] = {"error": str(e)}

    # 18b. M24D Activation executor — pending/blocked requests, enabled, failed, rollback history
    try:
        from workflow_dataset.external_capability.activation_store import list_requests, load_history
        from workflow_dataset.runtime_mesh.integration_registry import list_integrations
        pending = list_requests(root, status="pending")
        blocked = list_requests(root, status="blocked")
        failed = list_requests(root, status="failed")
        history = load_history(root, limit=30)
        enabled_integrations = [m.integration_id for m in list_integrations(root) if m.enabled]
        rollback_entries = [e for e in history if e.get("outcome") == "executed" and (e.get("details") or {}).get("action") == "disable"]
        recommended_next_capability_action = ""
        if pending:
            recommended_next_capability_action = f"capabilities external execute --id {pending[0].activation_id} [--approved]"
        elif len(failed) > 0:
            recommended_next_capability_action = "capabilities external health"
        else:
            recommended_next_capability_action = "capabilities external recommend"
        out["activation_executor"] = {
            "pending_activation_requests": [r.activation_id for r in pending][:20],
            "pending_count": len(pending),
            "blocked_activation_requests": [r.activation_id for r in blocked][:20],
            "blocked_count": len(blocked),
            "enabled_external_capabilities": enabled_integrations,
            "failed_activations": [r.activation_id for r in failed][:20],
            "failed_count": len(failed),
            "rollback_history_count": len(rollback_entries),
            "recommended_next_capability_action": recommended_next_capability_action,
        }
    except Exception as e:
        out["activation_executor"] = {"error": str(e)}

    # 19. M24B Vertical value packs — recommended pack, first-run ready
    try:
        from workflow_dataset.value_packs.recommend import recommend_value_pack
        from workflow_dataset.value_packs.registry import list_value_packs
        rec = recommend_value_pack(profile=None, repo_root=root)
        pack_ids = list_value_packs()
        pack = rec.get("pack")
        out["value_packs"] = {
            "packs_count": len(pack_ids),
            "recommended_pack_id": getattr(pack, "pack_id", None) if pack else None,
            "recommended_pack_name": getattr(pack, "name", None) if pack else None,
            "missing_prerequisites_count": len(rec.get("missing_prerequisites") or []),
        }
    except Exception as e:
        out["value_packs"] = {"error": str(e)}

    # 19b. M24E Provisioning — provisioned packs, failed runs, recommended next first-value, missing prereqs
    try:
        from workflow_dataset.specialization.recipe_runs_storage import list_runs as list_recipe_runs
        from workflow_dataset.provisioning.domain_environment import domain_environment_summary
        from workflow_dataset.value_packs.recommend import recommend_value_pack
        runs = list_recipe_runs(repo_root=root, limit=20)
        completed = [r for r in runs if r.status == "completed"]
        failed = [r for r in runs if r.status == "failed"]
        provisioned_pack_ids = list({r.target_value_pack_id for r in completed if r.target_value_pack_id})
        rec = recommend_value_pack(profile=None, repo_root=root)
        pack = rec.get("pack")
        recommended_first_value_flow = ""
        missing_prereqs: list[str] = []
        if pack:
            env = domain_environment_summary(pack.pack_id, repo_root=root)
            recommended_first_value_flow = env.get("recommended_first_value_run") or ""
            missing_prereqs = list(rec.get("missing_prerequisites") or [])
        out["provisioning"] = {
            "provisioned_packs": provisioned_pack_ids,
            "provisioned_count": len(provisioned_pack_ids),
            "recipe_runs_count": len(runs),
            "failed_provisioning_runs": [r.run_id for r in failed][:10],
            "failed_count": len(failed),
            "recommended_next_first_value_flow": recommended_first_value_flow,
            "missing_prerequisites": missing_prereqs[:15],
        }
        out["local_sources"]["provisioning"] = str((root / "data/local/provisioning").resolve())
        out["local_sources"]["recipe_runs"] = str((root / "data/local/specialization/recipe_runs").resolve())
    except Exception as e:
        out["provisioning"] = {"error": str(e)}

    # 20. M24C Acceptance harness — latest run, scenarios, ready for trial
    try:
        from workflow_dataset.acceptance.scenarios import list_scenarios
        from workflow_dataset.acceptance.storage import load_latest_run, list_runs
        scenarios = list_scenarios()
        latest = load_latest_run(root)
        runs = list_runs(root, limit=5)
        out["acceptance"] = {
            "scenarios_count": len(scenarios),
            "scenario_ids": scenarios[:15],
            "latest_run_scenario_id": latest.get("scenario_id") if latest else None,
            "latest_run_outcome": latest.get("outcome") if latest else None,
            "latest_run_ready_for_trial": latest.get("ready_for_trial") if latest else None,
            "runs_count": len(runs),
        }
    except Exception as e:
        out["acceptance"] = {"error": str(e)}

    # 21. M24F Rollout — status, demo readiness, blocked items, support bundle freshness, next operator action
    try:
        from workflow_dataset.rollout.tracker import load_rollout_state
        from workflow_dataset.rollout.demos import list_demos
        rollout_state = load_rollout_state(root)
        demo_ids = list_demos()
        target_id = rollout_state.get("target_scenario_id")
        demo_ready = False
        if target_id:
            for did, sid in [("founder_demo", "founder_first_run"), ("analyst_demo", "analyst_first_run"), ("developer_demo", "developer_first_run"), ("document_worker_demo", "document_worker_first_run")]:
                if sid == target_id:
                    demo_ready = rollout_state.get("current_stage") == "ready_for_trial"
                    break
        out["rollout"] = {
            "rollout_status": rollout_state.get("current_stage") or "not_started",
            "target_scenario_id": target_id,
            "demo_readiness": "ready" if demo_ready else ("blocked" if rollout_state.get("blocked_items") else "in_progress"),
            "blocked_rollout_items": rollout_state.get("blocked_items") or [],
            "next_rollout_action": rollout_state.get("next_required_action") or "Run 'workflow-dataset rollout launch --id founder_demo' to start.",
            "demos_available": demo_ids,
        }
        # Support bundle freshness: last dir under data/local/rollout matching support_bundle_*
        rollout_dir = root / "data/local/rollout"
        if rollout_dir.exists():
            bundles = sorted(rollout_dir.glob("support_bundle_*"), key=lambda p: p.stat().st_mtime if p.is_dir() else 0, reverse=True)
            if bundles and bundles[0].is_dir():
                out["rollout"]["support_bundle_freshness"] = str(bundles[0])
                out["rollout"]["support_bundle_latest_mtime"] = bundles[0].stat().st_mtime
            else:
                out["rollout"]["support_bundle_freshness"] = None
        else:
            out["rollout"]["support_bundle_freshness"] = None
    except Exception as e:
        out["rollout"] = {"error": str(e)}

    # 22. M24J–M24M Active session — session id, pack, board summary, artifacts, next action
    try:
        from workflow_dataset.session import get_current_session, build_session_board
        from workflow_dataset.session.artifacts import list_artifacts
        session = get_current_session(root)
        if session:
            board = build_session_board(session, root)
            artifacts = list_artifacts(session.session_id, root, limit=20)
            rec_next = "session board" if (board.queued or board.blocked) else "session artifacts"
            out["active_session"] = {
                "session_id": session.session_id,
                "pack_id": session.value_pack_id,
                "queued_count": len(board.queued),
                "blocked_count": len(board.blocked),
                "ready_count": len(board.ready),
                "artifacts_count": len(artifacts),
                "recommended_next_session_action": rec_next,
            }
        else:
            out["active_session"] = None
    except Exception as e:
        out["active_session"] = {"error": str(e)}

    # 23. M24N–M24Q Outcomes — session memory, recurring blockers, high-value jobs/macros, next recommended improvement
    try:
        from workflow_dataset.outcomes.store import list_session_outcomes, load_outcome_history
        from workflow_dataset.outcomes.signals import generate_improvement_signals
        from workflow_dataset.outcomes.bridge import next_run_recommendations
        sessions = list_session_outcomes(limit=10, repo_root=root)
        history = load_outcome_history(root, limit=20)
        signals = generate_improvement_signals(repo_root=root)
        recs = next_run_recommendations(repo_root=root)
        latest_session_ids = [s.session_id for s in sessions[:5]]
        recurring_blockers = [s.get("cause_code", "") + ":" + s.get("source_ref", "") for s in signals.get("recurring_blockers", [])[:5]]
        high_value = [s.get("source_ref", "") for s in signals.get("macro_or_job_highly_useful", [])[:5]]
        next_improvement = (recs[0].get("title") or "") if recs else ""
        out["outcomes"] = {
            "latest_session_outcomes_count": len(sessions),
            "latest_session_ids": latest_session_ids,
            "outcome_history_count": len(history),
            "recurring_blockers": recurring_blockers,
            "high_value_jobs_macros": high_value,
            "next_recommended_improvement": next_improvement,
            "first_value_flow_weak": signals.get("first_value_flow_weak", False),
        }
        out["local_sources"]["outcomes"] = str((root / "data/local/outcomes").resolve())
    except Exception as e:
        out["outcomes"] = {"error": str(e)}

    # 24. M24R–M24U Distribution — deploy readiness, install bundles, handoff
    try:
        from workflow_dataset.distribution.readiness import build_deploy_readiness
        readiness = build_deploy_readiness(root)
        bundles_dir = root / "data/local/distribution/bundles"
        bundle_count = len(list(bundles_dir.glob("*.json"))) if bundles_dir.exists() else 0
        deploy_ready = readiness.get("rollout_first_user_ready", False) or readiness.get("package_ready_for_first_user", False)
        blocks = []
        if not readiness.get("install_check_passed", False):
            blocks.append("install_check")
        if not readiness.get("package_ready_for_first_user", False):
            blocks.append("first_user_install")
        if not readiness.get("rollout_demo_ready", False):
            blocks.append("demo_ready")
        out["distribution"] = {
            "deploy_ready": deploy_ready,
            "blocks": blocks[:5],
            "install_bundles_count": bundle_count,
            "next_action": "deploy bundle" if bundle_count == 0 else "deploy readiness",
        }
        out["local_sources"]["distribution"] = str((root / "data/local/distribution").resolve())
    except Exception as e:
        out["distribution"] = {"error": str(e)}

    # 25a. M25A–M25D Pack registry — installed by version, update availability, verification, channel policy (M25D.1)
    try:
        from workflow_dataset.packs.install_flows import list_installed_with_updates
        from workflow_dataset.packs.registry_index import load_local_registry
        from workflow_dataset.packs.verify import verify_pack
        from workflow_dataset.packs.registry_policy import load_registry_policy
        from workflow_dataset.packs.pack_state import get_active_role
        packs_dir = root / "data/local/packs"
        installed_with_updates = list_installed_with_updates(packs_dir)
        registry_entries = load_local_registry(packs_dir)
        verification_failures = []
        for rec in installed_with_updates:
            pid = rec.get("pack_id", "")
            if not pid:
                continue
            valid, _w, _e = verify_pack(pid, packs_dir, strict_signature=False)
            if not valid:
                verification_failures.append(pid)
        policy = load_registry_policy(packs_dir)
        channels = policy.get("channels", {})
        block_channels = [c for c, a in channels.items() if a == "block"]
        warn_channels = [c for c, a in channels.items() if a == "warn"]
        active_role = get_active_role(packs_dir)
        out["pack_registry"] = {
            "installed_count": len(installed_with_updates),
            "installed_by_version": {r.get("pack_id", ""): r.get("version", "") for r in installed_with_updates if r.get("pack_id")},
            "update_available_count": sum(1 for r in installed_with_updates if r.get("update_available")),
            "update_available_pack_ids": [r.get("pack_id", "") for r in installed_with_updates if r.get("update_available")],
            "verification_failures": verification_failures[:20],
            "registry_entries_count": len(registry_entries),
            "channel_policy": {"block": block_channels, "warn": warn_channels, "active_role": active_role},
            "next_action": "packs registry list" if not registry_entries else ("packs update --id <pack_id>" if any(r.get("update_available") for r in installed_with_updates) else "packs verify --id <pack_id>"),
        }
    except Exception as e:
        out["pack_registry"] = {"error": str(e)}

    # 25. M25E–M25H Pack behavior — active overrides, prompt source, task defaults, excluded, why
    try:
        from workflow_dataset.packs.behavior_resolver import get_active_behavior_summary
        packs_dir = root / "data/local/packs"
        summary = get_active_behavior_summary(packs_dir=packs_dir)
        out["pack_behavior"] = {
            "winning_pack_id": summary.get("winning_pack_id", ""),
            "active_pack_ids": summary.get("active_pack_ids", []),
            "primary_pack_id": summary.get("primary_pack_id", ""),
            "pinned_pack_id": summary.get("pinned_pack_id", ""),
            "prompt_asset_count": summary.get("prompt_asset_count", 0),
            "prompt_asset_sources": summary.get("prompt_asset_sources", []),
            "task_defaults": summary.get("task_defaults", {}),
            "retrieval_profile": summary.get("retrieval_profile", {}),
            "output_profile": summary.get("output_profile", {}),
            "retrieval_profile_source_pack": summary.get("retrieval_profile_source_pack", ""),
            "output_profile_source_pack": summary.get("output_profile_source_pack", ""),
            "retrieval_profile_preset_id": summary.get("retrieval_profile_preset_id", ""),
            "output_profile_preset_id": summary.get("output_profile_preset_id", ""),
            "why_retrieval_profile": summary.get("why_retrieval_profile", ""),
            "why_output_profile": summary.get("why_output_profile", ""),
            "parser_output_hints_count": summary.get("parser_output_hints_count", 0),
            "excluded_pack_ids": summary.get("excluded_pack_ids", []),
            "exclusion_reasons": summary.get("exclusion_reasons", {}),
            "conflict_summary": summary.get("conflict_summary", ""),
            "why_current_behavior": summary.get("why_current_behavior", ""),
            "conflicts": summary.get("conflicts", []),
            "why_excluded": summary.get("why_excluded", []),
        }
        out["local_sources"]["packs"] = str(packs_dir.resolve())
    except Exception as e:
        out["pack_behavior"] = {"error": str(e)}

    # 26. M25I–M25L Pack authoring — draft packs, uncertified, blocked, certifiable, highest-value certifiable
    try:
        import json
        from workflow_dataset.packs.pack_state import load_pack_state
        from workflow_dataset.packs.certification import run_certification, CERT_STATUS_CERTIFIABLE, CERT_STATUS_BLOCKED
        packs_dir = root / "data/local/packs"
        state = load_pack_state(packs_dir)
        installed_ids = list(state.keys())
        draft_packs = []
        if packs_dir.exists():
            for d in packs_dir.iterdir():
                if d.is_dir() and (d / "manifest.json").exists() and d.name not in installed_ids:
                    draft_packs.append(d.name)
        uncertified = []
        blocked = []
        certifiable = []
        certifiable_with_count = []
        for pid in installed_ids:
            try:
                cert = run_certification(pid, packs_dir=packs_dir)
                s = cert.get("status", "")
                if s == CERT_STATUS_CERTIFIABLE:
                    certifiable.append(pid)
                    try:
                        data = json.loads((packs_dir / pid / "manifest.json").read_text(encoding="utf-8"))
                        n = len(data.get("templates") or []) + len(data.get("workflow_templates") or [])
                        certifiable_with_count.append((pid, n))
                    except Exception:
                        certifiable_with_count.append((pid, 0))
                elif s == CERT_STATUS_BLOCKED:
                    blocked.append(pid)
                elif s not in (CERT_STATUS_CERTIFIABLE,):
                    uncertified.append(pid)
            except Exception:
                uncertified.append(pid)
        certifiable_with_count.sort(key=lambda x: -x[1])
        highest_value_certifiable = [pid for pid, _ in certifiable_with_count[:10]]
        out["pack_authoring"] = {
            "draft_packs": draft_packs[:20],
            "uncertified_packs": uncertified[:20],
            "blocked_certification": blocked[:20],
            "certifiable_packs": certifiable[:20],
            "highest_value_certifiable": highest_value_certifiable[:5],
        }
    except Exception as e:
        out["pack_authoring"] = {"error": str(e)}

    # 27. M26A–M26D Goal-to-plan — active goal, latest plan, blocked steps, next checkpoint, expected artifacts
    try:
        from workflow_dataset.planner.store import load_current_goal, load_latest_plan
        active_goal = load_current_goal(root)
        plan = load_latest_plan(root)
        if plan:
            blocked_count = len(plan.blocked_conditions)
            next_checkpoint = plan.checkpoints[0].step_index if plan.checkpoints else None
            expected = [a.label for a in plan.expected_artifacts[:10]]
            out["goal_plan"] = {
                "active_goal": active_goal[:200] if active_goal else "",
                "latest_plan_id": plan.plan_id,
                "plan_step_count": len(plan.steps),
                "blocked_step_count": blocked_count,
                "next_checkpoint_index": next_checkpoint,
                "expected_artifacts": expected,
                "next_action": "planner preview --latest" if plan.steps else "planner compile --goal \"<your goal>\"",
            }
        else:
            out["goal_plan"] = {
                "active_goal": active_goal[:200] if active_goal else "",
                "latest_plan_id": "",
                "plan_step_count": 0,
                "blocked_step_count": 0,
                "next_checkpoint_index": None,
                "expected_artifacts": [],
                "next_action": "planner compile --goal \"<your goal>\"",
            }
    except Exception as e:
        out["goal_plan"] = {"error": str(e)}

    # 27a. M27A–M27D Project/case — active project, goal stack, blockers, recommended next
    try:
        from workflow_dataset.project_case import get_current_project_id, get_project_summary
        current_project_id = get_current_project_id(root)
        if current_project_id:
            summary = get_project_summary(current_project_id, root)
            if not summary.get("error"):
                out["project_case"] = {
                    "active_project_id": current_project_id,
                    "active_project_title": summary.get("title", ""),
                    "goal_stack_summary": {
                        "goals_count": summary.get("goals_count", 0),
                        "active": summary.get("project_state", {}).get("active_goals_count", 0),
                        "blocked": summary.get("project_state", {}).get("blocked_goals_count", 0),
                        "deferred": summary.get("project_state", {}).get("deferred_goals_count", 0),
                        "complete": summary.get("project_state", {}).get("complete_goals_count", 0),
                    },
                    "project_blockers": summary.get("blocked_goals", [])[:10],
                    "latest_linked": summary.get("latest_linked", {}),
                    "recommended_next_project_action": summary.get("recommended_next_action"),
                }
            else:
                out["project_case"] = {"active_project_id": current_project_id, "error": summary.get("error", "")}
        else:
            out["project_case"] = {
                "active_project_id": None,
                "goal_stack_summary": {},
                "project_blockers": [],
                "recommended_next_project_action": None,
                "next_action": "projects create --id <id> then projects set-current --id <id>",
            }
        out["local_sources"]["project_case"] = str((root / "data/local/project_case").resolve())
    except Exception as e:
        out["project_case"] = {"error": str(e)}

    # 27b. M27I–M27L Progress / Replan — replan-needed, stalled, advancing, recent impact, next intervention
    try:
        from workflow_dataset.progress.board import build_progress_board
        board = build_progress_board(repo_root=root)
        out["progress_replan"] = {
            "replan_needed_projects": board.get("replan_needed_projects", [])[:10],
            "stalled_projects": board.get("stalled_projects", [])[:10],
            "advancing_projects": board.get("advancing_projects", [])[:10],
            "recent_replan_signals_count": len(board.get("recent_replan_signals", [])),
            "recurring_blockers_count": len(board.get("recurring_blockers", [])),
            "positive_impact_count": len(board.get("positive_impact_signals", [])),
            "next_intervention_candidate": board.get("next_intervention_candidate", ""),
        }
        out["local_sources"]["progress"] = str((root / "data/local/progress").resolve())
    except Exception as e:
        out["progress_replan"] = {"error": str(e)}

    # M26E–M26H Executor (safe action runtime)
    try:
        from workflow_dataset.executor.hub import list_runs, load_run
        runs = list_runs(limit=5, repo_root=root)
        active_run_id = runs[0]["run_id"] if runs else None
        active_run = load_run(active_run_id, root) if active_run_id else None
        if active_run:
            out["executor"] = {
                "active_run_id": active_run.run_id,
                "plan_id": active_run.plan_id,
                "plan_ref": active_run.plan_ref,
                "status": active_run.status,
                "current_step_index": active_run.current_step_index,
                "next_checkpoint": active_run.approval_required_before_step,
                "blocked_action": active_run.blocked[-1] if active_run.blocked else None,
                "produced_artifacts_count": len(active_run.artifacts),
                "executed_count": len(active_run.executed),
                "blocked_count": len(active_run.blocked),
                "next_action": "executor resume --run " + active_run.run_id if active_run.status == "awaiting_approval" else ("executor run --plan-ref " + active_run.plan_ref if active_run.status == "completed" else "executor status --run " + active_run.run_id),
            }
        else:
            out["executor"] = {
                "active_run_id": None,
                "plan_id": "",
                "plan_ref": "",
                "status": "",
                "current_step_index": 0,
                "next_checkpoint": None,
                "blocked_action": None,
                "produced_artifacts_count": 0,
                "executed_count": 0,
                "blocked_count": 0,
                "next_action": "executor run --plan-ref <routine_id|job_id>",
            }
    except Exception as e:
        out["executor"] = {"error": str(e)}

    # M27E–M27H Supervised agent loop
    try:
        from workflow_dataset.supervised_loop.summary import build_cycle_summary
        summary = build_cycle_summary(root)
        out["supervised_loop"] = {
            "cycle_id": summary.cycle_id,
            "project_slug": summary.project_slug,
            "goal_text": (summary.goal_text or "")[:200],
            "status": summary.status or "idle",
            "blocked_reason": summary.blocked_reason or "",
            "pending_queue_count": summary.pending_queue_count,
            "approved_count": summary.approved_count,
            "rejected_count": summary.rejected_count,
            "deferred_count": summary.deferred_count,
            "last_handoff_status": summary.last_handoff_status or "",
            "last_run_id": summary.last_run_id or "",
            "next_proposed_action_label": (summary.next_proposed_action_label or "")[:100],
            "next_proposed_action_id": summary.next_proposed_action_id or "",
        }
        out["local_sources"]["supervised_loop"] = str((root / "data/local/supervised_loop").resolve())
    except Exception as e:
        out["supervised_loop"] = {"error": str(e)}

    # M45I–M45L Supervisory control panel — active/paused/awaiting/takeover, most urgent
    try:
        from workflow_dataset.supervisory_control.panel import mission_control_slice
        out["supervisory_control_state"] = mission_control_slice(repo_root=root)
        out["local_sources"]["supervisory_control"] = str((root / "data/local/supervisory_control").resolve())
    except Exception as e:
        out["supervisory_control_state"] = {"error": str(e)}

    # M46A–M46D Long-run health — current alert, strongest drift, top degraded, operator burden trend, next maintenance
    try:
        from workflow_dataset.long_run_health.mission_control import long_run_health_slice
        out["long_run_health_state"] = long_run_health_slice(repo_root=root)
        out["local_sources"]["long_run_health"] = str((root / "data/local/long_run_health").resolve())
    except Exception as e:
        out["long_run_health_state"] = {"error": str(e)}

    # M28 Portfolio router (Pane 1 — merge first: routing)
    try:
        from workflow_dataset.portfolio import build_portfolio
        portfolio = build_portfolio(repo_root=root)
        priority_stack = [
            {"project_id": e.project_id, "rank_index": e.priority.rank_index, "tier": e.priority.tier}
            for e in portfolio.entries[:20]
        ]
        next_rec = portfolio.next_recommended_project
        top_int = portfolio.top_intervention
        out["portfolio_router"] = {
            "priority_stack": priority_stack,
            "top_intervention_candidate": top_int.project_id if top_int else "",
            "next_recommended_project": next_rec.project_id if next_rec else "",
            "most_blocked_project": portfolio.most_blocked_project_id,
            "most_valuable_ready_project": portfolio.most_valuable_ready_project_id,
            "health_total_active": portfolio.health.total_active,
            "health_labels": portfolio.health.labels,
        }
        out["local_sources"]["portfolio"] = str((root / "data/local/portfolio").resolve())
    except Exception as e:
        out["portfolio_router"] = {"error": str(e)}

    # M28E–M28H Worker lanes (Pane 3 — merge second: bounded delegation)
    try:
        from workflow_dataset.lanes.store import list_lanes
        all_lanes = list_lanes(limit=50, repo_root=root)
        active_lanes = [L for L in all_lanes if L.get("status") in ("open", "running")]
        blocked_lanes = [L for L in all_lanes if L.get("status") == "blocked"]
        completed_awaiting = [L for L in all_lanes if L.get("status") == "completed"]
        project_to_lanes: dict[str, list[str]] = {}
        for L in all_lanes:
            pid = L.get("project_id") or ""
            if pid:
                project_to_lanes.setdefault(pid, []).append(L.get("lane_id", ""))
        next_handoff = completed_awaiting[0]["lane_id"] if completed_awaiting else ""
        out["worker_lanes"] = {
            "active_lanes": active_lanes[:20],
            "blocked_lanes": blocked_lanes[:20],
            "results_awaiting_review": completed_awaiting[:10],
            "parent_project_to_lanes": {k: v[:5] for k, v in project_to_lanes.items()},
            "next_handoff_needed": next_handoff,
            "total_lanes": len(all_lanes),
        }
        out["local_sources"]["lanes"] = str((root / "data/local/lanes").resolve())
    except Exception as e:
        out["worker_lanes"] = {"error": str(e)}

    # M28I–M28L Human policy engine (Pane 2 — merge third: policy/override)
    try:
        from workflow_dataset.human_policy.board import list_active_effects, list_overrides
        from workflow_dataset.human_policy.store import get_policy_dir
        current_project = None
        try:
            from workflow_dataset.project_case.store import get_current_project_id
            current_project = get_current_project_id(root) or ""
        except Exception:
            pass
        effects = list_active_effects(project_id=current_project or "", pack_id="", repo_root=root)
        overrides = list_overrides(active_only=True, repo_root=root)
        out["human_policy"] = {
            "active_restrictions_count": len([e for e in effects if e.effect_key in ("always_manual", "simulate_only") and e.effect_value]),
            "active_overrides_count": len(overrides),
            "override_ids": [o.override_id for o in overrides[:10]],
            "blocked_behaviors": "execute_trusted_real requires approval; delegation off by default",
            "intervention_candidates": "policy board to review overrides; policy evaluate for action",
        }
        out["local_sources"]["human_policy"] = str(get_policy_dir(root).resolve())
    except Exception as e:
        out["human_policy"] = {"error": str(e)}

    # M29I–M29L Review studio: timeline, intervention inbox, next recommended
    try:
        from workflow_dataset.review_studio.inbox import build_inbox
        from workflow_dataset.review_studio.timeline import build_timeline
        from workflow_dataset.review_studio.store import load_inbox_snapshot
        inbox_items = build_inbox(root, status="pending", limit=100)
        timeline_events = build_timeline(root, limit=20)
        snapshot = load_inbox_snapshot(root)
        urgent = [i for i in inbox_items if i.priority in ("urgent", "high")]
        out["review_studio"] = {
            "recent_timeline_count": len(timeline_events),
            "inbox_count": len(inbox_items),
            "urgent_count": len(urgent),
            "oldest_unresolved_id": snapshot.get("oldest_item_id", ""),
            "next_recommended_intervention_id": snapshot.get("next_recommended_id", ""),
        }
        out["local_sources"]["review_studio"] = str((root / "data/local/review_studio").resolve())
    except Exception as e:
        out["review_studio"] = {"error": str(e)}

    # M30I–M30L Release readiness and supportability
    try:
        from workflow_dataset.release_readiness import build_release_readiness, load_latest_handoff_pack
        readiness = build_release_readiness(root)
        handoff = load_latest_handoff_pack(root)
        out["release_readiness"] = {
            "status": readiness.status,
            "blocker_count": len(readiness.blockers),
            "warning_count": len(readiness.warnings),
            "highest_severity_blocker": readiness.blockers[0].summary if readiness.blockers else "",
            "known_limitations_count": len(readiness.known_limitations),
            "supportability_confidence": readiness.supportability.confidence,
            "guidance": readiness.supportability.guidance,
            "handoff_pack_freshness": handoff.get("generated_at") if handoff else "",
        }
        out["local_sources"]["release_readiness"] = str((root / "data/local/release_readiness").resolve())
    except Exception as e:
        out["release_readiness"] = {"error": str(e)}

    # M40I–M40L Production launch — launch decision, failed gates, highest blocker, support readiness, next action
    # M40L.1: post-deployment guidance, latest review cycle, sustained-use checkpoint, ongoing summary one-liner
    try:
        from workflow_dataset.production_launch import (
            build_launch_decision_pack,
            evaluate_production_gates,
            build_post_deployment_guidance,
            get_latest_review_cycle,
            list_sustained_use_checkpoints,
            build_ongoing_production_summary,
        )
        pack = build_launch_decision_pack(root)
        gate_results = evaluate_production_gates(root)
        failed_gates = [g for g in gate_results if not g.passed]
        blockers = pack.get("open_blockers", [])
        highest_blocker = blockers[0].get("summary", "") if blockers else ""
        guidance = build_post_deployment_guidance(root)
        latest_cycle = get_latest_review_cycle(root)
        checkpoints = list_sustained_use_checkpoints(root, limit=1)
        latest_checkpoint = checkpoints[0] if checkpoints else {}
        ongoing = build_ongoing_production_summary(root)
        out["production_launch"] = {
            "recommended_decision": pack.get("recommended_decision", "pause"),
            "failed_gate_ids": [g.gate_id for g in failed_gates],
            "failed_gates_count": len(failed_gates),
            "highest_severity_blocker": highest_blocker[:200] if highest_blocker else "",
            "support_readiness": pack.get("support_posture", "")[:100],
            "next_launch_review_action": "workflow-dataset launch-decision explain" if failed_gates or blockers else "workflow-dataset launch-decision pack --write",
            "post_deployment_guidance": guidance.get("guidance", "continue"),
            "post_deployment_reason": (guidance.get("reason", "") or "")[:120],
            "latest_review_cycle_at": latest_cycle.get("at_iso", "") if latest_cycle else "",
            "latest_sustained_use_checkpoint_kind": latest_checkpoint.get("kind", ""),
            "ongoing_summary_one_liner": ongoing.get("one_liner", "")[:150],
        }
    except Exception as e:
        out["production_launch"] = {"error": str(e)}

    # M46I–M46L Sustained deployment reviews — current recommendation, top risk, next review, watch/degraded/repair state
    try:
        from workflow_dataset.stability_reviews import (
            build_stability_decision_pack,
            build_decision_output,
            load_latest_review,
        )
        pack = build_stability_decision_pack(root)
        decision_out = build_decision_output(pack)
        latest_sdr = load_latest_review(root)
        rec = decision_out.get("decision", "continue")
        # Map to watch/degraded/repair-needed state
        watch_state = "ok"
        if rec in ("continue_with_watch", "narrow"):
            watch_state = "watch"
        elif rec == "repair":
            watch_state = "repair_needed"
        elif rec in ("pause", "rollback"):
            watch_state = "degraded"
        top_risk = ""
        if pack.evidence_bundle and pack.evidence_bundle.drift_signals:
            top_risk = pack.evidence_bundle.drift_signals[0][:120]
        elif pack.evidence_bundle and pack.evidence_bundle.health_summary:
            top_risk = pack.evidence_bundle.health_summary[:120]
        elif decision_out.get("rationale"):
            top_risk = decision_out["rationale"][:120]
        next_review_iso = latest_sdr.get("next_scheduled_review_iso", "") if latest_sdr else ""
        if not next_review_iso and latest_sdr:
            next_review_iso = latest_sdr.get("decision_pack", {}).get("generated_at_iso", "")
        strongest_continue = decision_out.get("rationale", "") if rec in ("continue", "continue_with_watch") else ""
        strongest_pause = decision_out.get("rationale", "") if rec in ("pause", "rollback", "repair") else ""
        out["stability_reviews"] = {
            "current_sustained_use_recommendation": rec,
            "recommendation_label": decision_out.get("label", ""),
            "top_stability_risk": top_risk,
            "next_scheduled_deployment_review_iso": next_review_iso,
            "watch_degraded_repair_state": watch_state,
            "strongest_reason_to_continue": strongest_continue[:150] if strongest_continue else "",
            "strongest_reason_to_pause": strongest_pause[:150] if strongest_pause else "",
        }
        out["local_sources"]["stability_reviews"] = str((root / "data/local/stability_reviews").resolve())
    except Exception as e:
        out["stability_reviews"] = {"error": str(e)}

    # M47I–M47L Quality signals + operator guidance
    try:
        from workflow_dataset.quality_guidance.signals import build_quality_signals
        from workflow_dataset.quality_guidance.surfaces import (
            ready_now_states,
            ambiguity_report,
            weak_guidance_report,
            next_recommended_guidance_improvement,
        )
        from workflow_dataset.quality_guidance.guidance import blocked_state_guidance
        signals = build_quality_signals(root)
        ready = ready_now_states(root)
        strongest_ready = (ready[0] if ready else {}) or signals.get("strongest_ready_to_act")
        if strongest_ready and isinstance(strongest_ready, dict):
            strongest_label = strongest_ready.get("label", "")[:80]
            strongest_rationale = strongest_ready.get("rationale", "")[:120]
        else:
            strongest_label = ""
            strongest_rationale = ""
        amb = ambiguity_report(root)
        most_ambiguous = (amb.get("most_ambiguous") or {}).get("message", "")[:100]
        weak = weak_guidance_report(root)
        weakest_surface = weak.get("weakest_guidance_surface") or {}
        weakest_summary = (weakest_surface.get("summary") or "")[:80] if isinstance(weakest_surface, dict) else ""
        blocked_g = blocked_state_guidance(repo_root=root)
        best_recovered = ((blocked_g.summary + " " + blocked_g.rationale)[:120]) if blocked_g else ""
        next_imp = next_recommended_guidance_improvement(root)
        out["quality_guidance"] = {
            "strongest_ready_to_act_item": strongest_label,
            "strongest_ready_rationale": strongest_rationale,
            "most_ambiguous_current_guidance": most_ambiguous,
            "best_recovered_blocked_state": best_recovered,
            "weakest_guidance_surface": weakest_summary,
            "next_recommended_guidance_improvement": next_imp.get("suggested_action", "")[:120],
        }
        out["local_sources"]["quality_guidance"] = str((root / "data/local/quality_guidance").resolve())
    except Exception as e:
        out["quality_guidance"] = {"error": str(e)}

    # M41E–M41H Council — active reviews, highest-risk pending, disagreement-heavy, latest promoted/quarantined
    try:
        from workflow_dataset.council import list_reviews
        reviews = list_reviews(root, limit=50)
        promoted = [r for r in reviews if r.get("synthesis_decision") == "promote"]
        quarantined = [r for r in reviews if r.get("synthesis_decision") == "quarantine"]
        # Highest risk: quarantine or reject, pick most recent
        high_risk = [r for r in reviews if r.get("synthesis_decision") in ("quarantine", "reject")]
        # Disagreement-heavy: would need full review to count notes; use quarantine as proxy for "needs attention"
        disagreement_heavy = high_risk[0].get("subject_id", "") if high_risk else ""
        out["council"] = {
            "active_reviews_count": len(reviews),
            "highest_risk_pending_subject_id": high_risk[0].get("subject_id", "") if high_risk else "",
            "disagreement_heavy_candidate_id": disagreement_heavy,
            "latest_promoted_subject_id": promoted[0].get("subject_id", "") if promoted else "",
            "latest_quarantined_subject_id": quarantined[0].get("subject_id", "") if quarantined else "",
        }
    except Exception as e:
        out["council"] = {"error": str(e)}

    # M30A–M30D Install / upgrade visibility
    try:
        from workflow_dataset.install_upgrade.version import get_current_version_display
        from workflow_dataset.install_upgrade.upgrade_plan import build_upgrade_plan
        from workflow_dataset.install_upgrade.apply_upgrade import list_rollback_checkpoints
        version_str, source = get_current_version_display(root)
        plan = build_upgrade_plan(repo_root=root)
        checkpoints = list_rollback_checkpoints(root)
        out["install_upgrade"] = {
            "current_version": version_str,
            "version_source": source,
            "target_version": plan.target_version,
            "upgrade_available": plan.current_version != plan.target_version and plan.can_proceed,
            "blocked_reasons": plan.blocked_reasons,
            "migration_warnings": plan.incompatible_warnings,
            "rollback_available": len(checkpoints) > 0,
            "rollback_checkpoints_count": len(checkpoints),
            "latest_checkpoint_id": checkpoints[0].checkpoint_id if checkpoints else "",
        }
        out["local_sources"]["install_dir"] = str((root / "data/local/install").resolve())
    except Exception as e:
        out["install_upgrade"] = {"error": str(e)}

    # M30E–M30H Reliability harness — golden-path health, regressions, top recovery, release confidence
    try:
        from workflow_dataset.reliability import load_latest_run, list_runs, list_path_ids, suggest_recovery
        latest = load_latest_run(root)
        runs = list_runs(root, limit=10)
        path_ids = list_path_ids()
        # Golden-path health: latest run outcome per path (simplified: use latest run only for summary)
        golden_path_health = "unknown"
        recent_regressions = []
        top_recovery_case = ""
        release_confidence_summary = "no_runs"
        if latest:
            golden_path_health = latest.get("outcome", "unknown")
            release_confidence_summary = "pass" if latest.get("outcome") == "pass" else ("degraded" if latest.get("outcome") == "degraded" else "blocked_or_fail")
            if latest.get("outcome") in ("blocked", "fail") and latest.get("subsystem"):
                top_recovery_case = suggest_recovery(subsystem=latest["subsystem"]).get("case_id", "")
        # Recent regressions: runs that are blocked/fail in last N
        for r in runs[:5]:
            if r.get("outcome") in ("blocked", "fail"):
                recent_regressions.append(f"{r.get('path_id', '')}:{r.get('subsystem', '')}")
        out["reliability"] = {
            "golden_path_health": golden_path_health,
            "latest_path_id": latest.get("path_id", "") if latest else "",
            "latest_run_id": latest.get("run_id", "") if latest else "",
            "recent_regressions": recent_regressions[:5],
            "degraded_but_usable": golden_path_health == "degraded",
            "top_recovery_case": top_recovery_case,
            "release_confidence_summary": release_confidence_summary,
            "golden_path_ids": path_ids,
        }
        out["local_sources"]["reliability"] = str((root / "data/local/reliability").resolve())
    except Exception as e:
        out["reliability"] = {"error": str(e)}

    # M32E–M32H Just-in-time assist engine: top suggestion, queue depth, repeated dismissed, focus-safe
    try:
        from workflow_dataset.assist_engine.queue import get_queue
        from workflow_dataset.assist_engine.store import list_dismissed_patterns, list_suggestions
        pending = list_suggestions(repo_root=root, status_filter="pending", limit=50)
        queue_visible = get_queue(repo_root=root, status_filter="pending", limit=30)
        top = queue_visible[0] if queue_visible else None
        dismissed = list_dismissed_patterns(repo_root=root, limit=20)
        repeated = []
        seen = set()
        for d in dismissed:
            key = (d.get("suggestion_type", ""), (d.get("reason_title") or "")[:40])
            if key in seen:
                repeated.append(key)
            seen.add(key)
        out["assist_engine"] = {
            "top_suggestion_id": top.suggestion_id if top else "",
            "top_suggestion_title": top.title if top else "",
            "top_suggestion_type": top.suggestion_type if top else "",
            "queue_depth": len(pending),
            "visible_queue_count": len(queue_visible),
            "repeated_dismissed_patterns": repeated[:10],
            "highest_confidence_next": queue_visible[0].confidence if queue_visible else 0.0,
            "focus_safe": len(queue_visible) == 0 or (queue_visible[0].interruptiveness_score < 0.3 and queue_visible[0].confidence >= 0.7),
        }
        out["local_sources"]["assist_engine"] = str((root / "data/local/assist_engine").resolve())
    except Exception as e:
        out["assist_engine"] = {"error": str(e)}

    # M37E–M37H Signal quality: suppressed count, resurfacing candidates, focus protected, top high-signal, calmness
    try:
        from workflow_dataset.unified_queue import build_unified_queue, rank_unified_queue
        from workflow_dataset.signal_quality.attention import get_protected_focus
        from workflow_dataset.signal_quality.quieting import apply_queue_quieting
        from workflow_dataset.signal_quality.reports import build_quality_report, build_resurfacing_report
        from workflow_dataset.signal_quality.scoring import rank_by_high_signal, score_queue_item
        items = build_unified_queue(repo_root=root, limit=50)
        items = rank_unified_queue(items, repo_root=root)
        focus = get_protected_focus(root)
        visible, suppressed = apply_queue_quieting(items, repo_root=root, focus=focus)
        top_id = ""
        if visible:
            ranked = rank_by_high_signal(visible, score_queue_item, {"focus_mode_active": focus.active})
            if ranked:
                top_id = getattr(ranked[0], "item_id", "")
        quality = build_quality_report(repo_root=root, queue_items=items, suppressed=suppressed, top_high_signal_id=top_id)
        resurfacing = build_resurfacing_report(repo_root=root, queue_items=items)
        out["signal_quality"] = {
            "suppressed_low_value_count": quality.get("suppressed_count", 0),
            "resurfacing_candidates_count": resurfacing.get("resurfacing_candidates_count", 0),
            "focus_protected_active": quality.get("focus_protected_active", False),
            "top_high_signal_item_id": quality.get("top_high_signal_item_id", ""),
            "noise_level": quality.get("noise_level", 0.0),
            "calmness_score": quality.get("calmness_score", 1.0),
        }
    except Exception as e:
        out["signal_quality"] = {"error": str(e)}

    # M38E–M38H Triage / cohort health: highest-severity issue, repeated cluster, cohort health, recommended mitigation
    try:
        from workflow_dataset.triage.store import list_issues
        from workflow_dataset.triage.health import build_cohort_health_summary
        from workflow_dataset.triage.loop import group_duplicates_or_related
        from workflow_dataset.triage.models import TriageStatus
        issues = list_issues(repo_root=root, limit=100)
        unresolved = [i for i in issues if i.triage_status not in (TriageStatus.RESOLVED, TriageStatus.MITIGATED)]
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        highest_issue_id = ""
        highest_severity = "none"
        if unresolved:
            top = min(unresolved, key=lambda x: severity_order.get(x.severity, 2))
            highest_issue_id = top.issue_id
            highest_severity = top.severity
        groups = group_duplicates_or_related(unresolved)
        repeated_cluster = list(groups.values())[:3] if groups else []
        health = build_cohort_health_summary(repo_root=root)
        out["triage"] = {
            "highest_severity_issue_id": highest_issue_id,
            "highest_severity": highest_severity,
            "repeated_issue_clusters": repeated_cluster,
            "open_issue_count": health.get("open_issue_count", 0),
            "unresolved_supported_surface_count": health.get("unresolved_supported_surface_count", 0),
            "recommended_mitigation": health.get("recommended_mitigation", ""),
            "recommended_downgrade": health.get("recommended_downgrade", False),
        }
    except Exception as e:
        out["triage"] = {"error": str(e)}

    # M38I–M38L Safe adaptation: candidates, quarantined, supported-surface deltas, recent accept/reject, next review
    try:
        from workflow_dataset.safe_adaptation import list_candidates, list_quarantined, list_recent_decisions
        from workflow_dataset.cohort.surface_matrix import get_matrix
        pending = list_candidates(repo_root=root, review_status="pending", limit=50)
        quarantined = list_quarantined(repo_root=root, limit=20)
        recent_decisions = list_recent_decisions(repo_root=root, limit=10)
        supported_pending = [c for c in pending if c.affected_surface_ids and any(
            (get_matrix(c.cohort_id).get(s, "") == "supported") for s in c.affected_surface_ids
        )]
        out["adaptation_state"] = {
            "safe_to_review_candidates_count": len(pending),
            "quarantined_count": len(quarantined),
            "supported_surface_deltas_pending_count": len(supported_pending),
            "recent_accepted_count": len([d for d in recent_decisions if d.decision == "accept"]),
            "recent_rejected_count": len([d for d in recent_decisions if d.decision == "reject"]),
            "next_recommended_adaptation_review_id": pending[0].adaptation_id if pending else "",
            "quarantined_sample_ids": [q.candidate_id for q in quarantined[:5]],
        }
        out["local_sources"]["safe_adaptation"] = str((root / "data/local/safe_adaptation").resolve())
    except Exception as e:
        out["adaptation_state"] = {"error": str(e)}

    # M39E–M39H Curated vertical packs: active pack, first-value path progress, next milestone, blocked step
    try:
        from workflow_dataset.vertical_packs.progress import build_milestone_progress_output
        vp = build_milestone_progress_output(repo_root=root)
        out["vertical_packs_state"] = {
            "active_curated_pack_id": vp.get("active_curated_pack_id", ""),
            "current_first_value_path_id": vp.get("path_id", ""),
            "next_vertical_milestone": vp.get("next_milestone_id", ""),
            "next_vertical_milestone_label": vp.get("next_milestone_label", ""),
            "reached_milestone_ids": vp.get("reached_milestone_ids", []),
            "blocked_vertical_onboarding_step": vp.get("blocked_onboarding_step", {}),
            "strongest_value_path_id": vp.get("strongest_value_path_id", vp.get("path_id", "")),
            "suggested_next_command": vp.get("suggested_next_command", ""),
        }
        out["local_sources"]["vertical_packs"] = str((root / "data/local/vertical_packs").resolve())
    except Exception as e:
        out["vertical_packs_state"] = {"error": str(e)}

    # M39I–M39L Vertical launch: active launch kit, first-value progress, success-proof status, launch blockers, next operator action
    try:
        from workflow_dataset.vertical_launch import get_active_launch, build_success_proof_report
        from workflow_dataset.vertical_packs.progress import build_milestone_progress_output
        active = get_active_launch(repo_root=root)
        launch_kit_id = active.get("active_launch_kit_id", "")
        vp = build_milestone_progress_output(repo_root=root) if launch_kit_id else {}
        proof_report = build_success_proof_report(launch_kit_id, repo_root=root) if launch_kit_id else {}
        blocked = vp.get("blocked_onboarding_step") or {}
        next_action = vp.get("suggested_next_command", "workflow-dataset launch-kit list")
        if blocked:
            next_action = blocked.get("escalation_command", next_action)
        # M39L.1: Value dashboard and rollout review for active vertical
        value_dashboard_summary = {}
        recommended_rollout_decision = ""
        try:
            from workflow_dataset.vertical_launch.dashboard import build_value_dashboard
            from workflow_dataset.vertical_launch.rollout_review import build_rollout_review_pack
            if launch_kit_id:
                dash = build_value_dashboard(launch_kit_id, repo_root=root)
                value_dashboard_summary = {
                    "what_is_working": dash.get("what_is_working", [])[:5],
                    "what_is_not_working": dash.get("what_is_not_working", [])[:5],
                    "operator_summary": (dash.get("operator_summary", "") or "")[:200],
                }
                review = build_rollout_review_pack(launch_kit_id, repo_root=root)
                recommended_rollout_decision = review.recommended_decision
        except Exception:
            pass
        out["launch_kit_state"] = {
            "active_launch_kit_id": launch_kit_id,
            "launch_started_at_utc": active.get("launch_started_at_utc", ""),
            "first_value_progress_path_id": vp.get("path_id", ""),
            "first_value_progress_next_milestone": vp.get("next_milestone_id", ""),
            "proof_of_value_met_count": proof_report.get("met_count", 0),
            "proof_of_value_pending_count": proof_report.get("pending_count", 0),
            "first_value_milestone_reached": proof_report.get("first_value_milestone_reached", False),
            "launch_blockers": blocked if blocked else None,
            "next_operator_support_action": next_action,
            "suggested_success_proof_report": "workflow-dataset success-proof report --id " + launch_kit_id if launch_kit_id else "",
            "value_dashboard_summary": value_dashboard_summary,
            "recommended_rollout_decision": recommended_rollout_decision,
            "suggested_rollout_review": "workflow-dataset rollout-review show --id " + launch_kit_id.replace("_launch", "") if launch_kit_id else "",
        }
        out["local_sources"]["vertical_launch"] = str((root / "data/local/vertical_launch").resolve())
    except Exception as e:
        out["launch_kit_state"] = {"error": str(e)}

    # M40A–M40D Production cut: active cut, included/excluded/quarantined counts, primary workflows, top scope risk
    try:
        from workflow_dataset.production_cut import get_active_cut, build_frozen_scope_report
        cut = get_active_cut(repo_root=root)
        if cut:
            report = build_frozen_scope_report(cut=cut, repo_root=str(root))
            out["production_cut_state"] = {
                "active_cut_id": cut.cut_id,
                "vertical_id": cut.vertical_id,
                "label": cut.label,
                "frozen_at_utc": cut.frozen_at_utc,
                "included_surface_count": len(cut.included_surface_ids),
                "excluded_surface_count": len(cut.excluded_surface_ids),
                "quarantined_surface_count": len(cut.quarantined_surface_ids),
                "primary_workflow_ids": (cut.supported_workflows.workflow_ids[:8] if cut.supported_workflows else []) or (cut.chosen_vertical.primary_workflow_ids[:8] if cut.chosen_vertical else []),
                "top_scope_risk": report.get("top_scope_risk", ""),
                "next_freeze_review": "workflow-dataset production-cut scope",
            }
            out["local_sources"]["production_cut"] = str((root / "data/local/production_cut").resolve())
        else:
            out["production_cut_state"] = {"active_cut_id": "", "next_freeze_review": "workflow-dataset production-cut lock --id <vertical_id>"}
    except Exception as e:
        out["production_cut_state"] = {"error": str(e)}

    # M41A–M41D Learning lab: top experiment, recent accepted/rejected, pattern mappings, next review
    try:
        from workflow_dataset.learning_lab import (
            list_experiments,
            get_active_experiment_id,
            get_current_profile_id,
            get_templates_allowed_for_profile,
            build_pattern_mapping_report,
        )
        active_id = get_active_experiment_id(repo_root=root)
        experiments = list_experiments(limit=30, repo_root=root)
        pending = [e for e in experiments if e.status == "pending"]
        promoted = [e for e in experiments if e.status == "promoted"][:3]
        rejected = [e for e in experiments if e.status == "rejected"][:3]
        quarantined = [e for e in experiments if e.status == "quarantined"]
        pattern_report = build_pattern_mapping_report(include_rejected=False)
        current_profile = get_current_profile_id(repo_root=root)
        local_templates = get_templates_allowed_for_profile(current_profile, production_adjacent=False)
        prod_adj_templates = get_templates_allowed_for_profile(current_profile, production_adjacent=True)
        out["learning_lab_state"] = {
            "active_experiment_id": active_id,
            "top_active_experiment": pending[0].experiment_id if pending else "",
            "recent_promoted": [e.experiment_id for e in promoted],
            "recent_rejected": [e.experiment_id for e in rejected],
            "pattern_mappings_in_use_count": pattern_report.get("adopted_count", 0),
            "quarantined_experiments_count": len(quarantined),
            "next_improvement_review": "workflow-dataset learning-lab experiments" if (pending or active_id) else "workflow-dataset learning-lab create --from issue_cluster:<id>",
            "current_profile_id": current_profile,
            "safe_templates_local_count": len(local_templates),
            "safe_templates_production_adjacent_count": len(prod_adj_templates),
        }
        out["local_sources"]["learning_lab"] = str((root / "data/local/learning_lab").resolve())
    except Exception as e:
        out["learning_lab_state"] = {"error": str(e)}

    # M40E–M40H Production deployment bundle: active bundle, upgrade/rollback readiness, recovery posture, blocked risks
    try:
        from workflow_dataset.deploy_bundle import build_deployment_health_summary
        health = build_deployment_health_summary(bundle_id="", repo_root=root)
        out["deploy_bundle_state"] = {
            "active_bundle_id": health.active_bundle_id,
            "bundle_id": health.bundle_id,
            "validation_passed": health.validation_passed,
            "upgrade_readiness": health.upgrade_readiness,
            "upgrade_readiness_reason": health.upgrade_readiness_reason,
            "rollback_readiness": health.rollback_readiness,
            "rollback_readiness_reason": health.rollback_readiness_reason,
            "recovery_posture_summary": health.recovery_posture_summary[:200] if health.recovery_posture_summary else "",
            "blocked_deployment_risks": health.blocked_deployment_risks[:5],
        }
        out["local_sources"]["deploy_bundle"] = str((root / "data/local/deploy_bundle").resolve())
    except Exception as e:
        out["deploy_bundle_state"] = {"error": str(e)}

    # M41I–M41L Ops jobs: next due, blocked, overdue, recent outcome, recommended action
    try:
        from workflow_dataset.ops_jobs import build_ops_maintenance_report
        ops_report = build_ops_maintenance_report(repo_root=root)
        out["ops_jobs_state"] = {
            "next_due_job_id": ops_report.get("next_due_job_id", ""),
            "blocked_job_id": ops_report.get("blocked_job_id", ""),
            "overdue_job_ids": [d.get("job_id") for d in ops_report.get("overdue_jobs", [])],
            "highest_value_overdue_id": ops_report.get("highest_value_overdue_id", ""),
            "recent_outcome_job_id": ops_report.get("recent_outcome", {}).get("job_id", ""),
            "recent_outcome_result": ops_report.get("recent_outcome", {}).get("outcome", ""),
            "recommended_action": ops_report.get("recommended_action", ""),
        }
        out["local_sources"]["ops_jobs"] = str((root / "data/local/ops_jobs").resolve())
    except Exception as e:
        out["ops_jobs_state"] = {"error": str(e)}

    # M42I–M42L Benchmark board: top candidate awaiting decision, latest promoted, quarantined, rollback-ready, next action
    try:
        from workflow_dataset.benchmark_board import build_benchmark_board_report
        bb = build_benchmark_board_report(repo_root=root)
        out["benchmark_board_state"] = {
            "top_candidate_awaiting_decision": bb.get("top_candidate_awaiting_decision", ""),
            "latest_promoted_id": bb.get("latest_promoted_id", ""),
            "latest_promoted_scope": bb.get("latest_promoted_scope", ""),
            "quarantined_count": bb.get("quarantined_count", 0),
            "rollback_ready_promoted_id": bb.get("rollback_ready_promoted_id", ""),
            "next_benchmark_review_action": bb.get("next_benchmark_review_action", ""),
        }
        out["local_sources"]["benchmark_board"] = str((root / "data/local/benchmark_board").resolve())
    except Exception as e:
        out["benchmark_board_state"] = {"error": str(e)}

    # M50E–M50H v1 operational discipline: support posture, overdue maintenance, top v1 risk, recommended action, rollback readiness
    try:
        from workflow_dataset.v1_ops.mission_control import get_v1_ops_state
        v1_state = get_v1_ops_state(root)
        out["v1_ops_state"] = {
            "current_support_posture": v1_state.get("current_support_posture", {}),
            "overdue_maintenance_or_review": v1_state.get("overdue_maintenance_or_review", False),
            "top_unresolved_v1_risk": (v1_state.get("top_unresolved_v1_risk") or "")[:200],
            "recommended_stable_v1_support_action": (v1_state.get("recommended_stable_v1_support_action") or "")[:200],
            "rollback_readiness_posture": v1_state.get("rollback_readiness_posture", {}),
        }
    except Exception as e:
        out["v1_ops_state"] = {"error": str(e)}

    # M50I–M50L Stable v1 gate: current recommendation, top blocker, narrow condition, evidence for/against, next action
    try:
        from workflow_dataset.stable_v1_gate.mission_control import get_stable_v1_gate_state
        sv1 = get_stable_v1_gate_state(root)
        out["stable_v1_gate_state"] = {
            "current_stable_v1_recommendation": (sv1.get("current_stable_v1_recommendation") or "")[:80],
            "current_stable_v1_recommendation_label": (sv1.get("current_stable_v1_recommendation_label") or "")[:80],
            "top_final_blocker": (sv1.get("top_final_blocker") or "")[:200],
            "narrow_v1_condition": (sv1.get("narrow_v1_condition") or "")[:200],
            "strongest_evidence_for": (sv1.get("strongest_evidence_for") or "")[:200],
            "strongest_evidence_against": (sv1.get("strongest_evidence_against") or "")[:200],
            "next_required_final_action": (sv1.get("next_required_final_action") or "")[:200],
            "gate_passed": sv1.get("gate_passed", False),
            "blocker_count": sv1.get("blocker_count", 0),
            "warning_count": sv1.get("warning_count", 0),
        }
    except Exception as e:
        out["stable_v1_gate_state"] = {"error": str(e)}

    # M33I–M33L In-flow review: latest draft waiting review, active checkpoint, latest handoff, recent promoted
    try:
        from workflow_dataset.in_flow.store import list_drafts, list_handoffs, list_checkpoints
        drafts_waiting = list_drafts(repo_root=root, review_status="waiting_review", limit=10)
        checkpoints_pending = list_checkpoints(repo_root=root, status="pending", limit=10)
        handoffs_list = list_handoffs(repo_root=root, limit=5)
        promoted = list_drafts(repo_root=root, review_status="promoted", limit=5)
        latest_draft = drafts_waiting[0] if drafts_waiting else None
        active_checkpoint = checkpoints_pending[0] if checkpoints_pending else None
        latest_handoff = handoffs_list[0] if handoffs_list else None
        out["in_flow"] = {
            "latest_draft_waiting_review_id": latest_draft.draft_id if latest_draft else "",
            "latest_draft_title": latest_draft.title[:50] if latest_draft else "",
            "active_review_checkpoint_id": active_checkpoint.checkpoint_id if active_checkpoint else "",
            "latest_handoff_id": latest_handoff.handoff_id if latest_handoff else "",
            "latest_handoff_target": latest_handoff.target if latest_handoff else "",
            "recent_promoted_draft_ids": [d.draft_id for d in promoted[:5]],
            "drafts_waiting_count": len(drafts_waiting),
            "checkpoints_pending_count": len(checkpoints_pending),
        }
        out["local_sources"]["in_flow"] = str((root / "data/local/in_flow").resolve())
    except Exception as e:
        out["in_flow"] = {"error": str(e)}

    return out
