"""
M22B: Format mission-control dashboard report. Read-only summary.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.mission_control.state import get_mission_control_state
from workflow_dataset.mission_control.next_action import recommend_next_action


def format_mission_control_report(state: dict[str, Any] | None = None, repo_root: Any = None) -> str:
    """Produce a console/dashboard report. If state is None, aggregates from repo_root."""
    if state is None:
        state = get_mission_control_state(repo_root)
    next_rec = recommend_next_action(state)
    lines: list[str] = []

    lines.append("=== Mission Control (local) ===")
    lines.append("")

    # Product state
    ps = state.get("product_state", {})
    if ps.get("error"):
        lines.append("[Product] error: " + str(ps["error"]))
    else:
        lines.append("[Product]")
        lines.append("  validated_workflows: " + ", ".join(ps.get("validated_workflows", [])))
        lines.append("  cohort: " + str(ps.get("cohort_recommendation") or "—") + "  sessions=" + str(ps.get("cohort_sessions_count", 0)))
        rp = ps.get("review_package", {})
        lines.append("  unreviewed: " + str(rp.get("unreviewed_count", 0)) + "  package_pending: " + str(rp.get("package_pending_count", 0)))
    lines.append("")

    # Evaluation state
    es = state.get("evaluation_state", {})
    if es.get("error"):
        lines.append("[Evaluation] error: " + str(es["error"]))
    else:
        lines.append("[Evaluation]")
        lines.append("  latest_run: " + str(es.get("latest_run_id") or "—") + "  recommendation: " + str(es.get("recommendation") or "—"))
        lines.append("  best_run: " + str(es.get("best_run_id") or "—") + "  runs_count: " + str(es.get("runs_count", 0)))
        comp = es.get("comparison")
        if comp:
            lines.append("  regressions: " + str(comp.get("regressions", [])))
            lines.append("  improvements: " + str(comp.get("improvements", [])))
    lines.append("")

    # Development state
    ds = state.get("development_state", {})
    if ds.get("error"):
        lines.append("[Development] error: " + str(ds["error"]))
    else:
        lines.append("[Development]")
        eq = ds.get("experiment_queue", {})
        lines.append("  experiments: queued=" + str(eq.get("queued", 0)) + " running=" + str(eq.get("running", 0)) + " done=" + str(eq.get("done", 0)))
        lines.append("  proposals: pending=" + str(ds.get("pending_proposals", 0)) + " accepted=" + str(ds.get("accepted_proposals", 0)) + " rejected=" + str(ds.get("rejected_proposals", 0)))
    lines.append("")

    # Incubator state
    ins = state.get("incubator_state", {})
    if ins.get("error"):
        lines.append("[Incubator] error: " + str(ins["error"]))
    else:
        lines.append("[Incubator]")
        lines.append("  candidates_by_stage: " + str(ins.get("candidates_by_stage", {})))
        lines.append("  promoted: " + str(ins.get("promoted_count", 0)) + "  rejected: " + str(ins.get("rejected_count", 0)) + "  hold: " + str(ins.get("hold_count", 0)))
    lines.append("")

    # Coordination graph (advisory)
    cg = state.get("coordination_graph_summary", {})
    if cg.get("error"):
        lines.append("[Coordination graph] error: " + str(cg["error"]))
    elif cg:
        lines.append("[Coordination graph] tasks=" + str(cg.get("tasks_count", 0)) + "  nodes=" + str(cg.get("total_nodes", 0)) + "  edges=" + str(cg.get("total_edges", 0)) + " (advisory)")
    lines.append("")

    # Desktop bridge (M23H)
    db = state.get("desktop_bridge", {})
    if db.get("error"):
        lines.append("[Desktop bridge] error: " + str(db["error"]))
    elif db:
        lines.append("[Desktop bridge] adapters=" + str(db.get("adapters_count", 0)) + "  " + ", ".join(db.get("adapter_ids", [])))
        lines.append("  approvals: " + ("present" if db.get("approvals_file_exists") else "missing") + "  path=" + str(db.get("approvals_path", "")))
        lines.append("  task_demos=" + str(db.get("tasks_count", 0)) + "  graph nodes=" + str(db.get("coordination_nodes", 0)) + " edges=" + str(db.get("coordination_edges", 0)))
        if db.get("approved_paths_count", 0) or db.get("approved_action_scopes_count", 0):
            lines.append("  approved_paths=" + str(db.get("approved_paths_count", 0)) + "  approved_action_scopes=" + str(db.get("approved_action_scopes_count", 0)))
    lines.append("")

    # Live work context (M32)
    lc = state.get("live_context_state", {})
    if lc.get("error"):
        lines.append("[Live context] error: " + str(lc["error"]))
    elif lc:
        lines.append("[Live context] project=" + str(lc.get("current_project") or "—") + "  task=" + str(lc.get("current_task_family") or "—") + "  mode=" + str(lc.get("current_work_mode") or "—"))
        lines.append("  confidence=" + str(lc.get("confidence", 0)) + "  stale=" + str(lc.get("is_stale", True)) + "  transitions=" + str(lc.get("recent_transitions_count", 0)))
        lines.append("  next: " + str(lc.get("next_assist_opportunity", "")))
    lines.append("")

    # M44A–M44D Memory OS (Pane 1: surfaces, weak-memory warnings, next review)
    mos = state.get("memory_os_state", {})
    if mos.get("error"):
        lines.append("[Memory OS] error: " + str(mos["error"]))
    elif mos:
        lines.append("[Memory OS] surfaces=" + str(len(mos.get("surfaces", []))) + "  weak_warnings=" + str(mos.get("weak_memory_warnings_count", 0)) + "  substrate_units=" + str(mos.get("substrate_units_count", 0)))
        if mos.get("next_recommended_memory_review"):
            lines.append("  next: " + str(mos["next_recommended_memory_review"]))
    lines.append("")

    # M44E–M44H Memory curation (Pane 2: summarization, forgetting, review, next action)
    mcur = state.get("memory_curation_state", {})
    if mcur.get("error"):
        lines.append("[Memory curation] error: " + str(mcur["error"]))
    elif mcur:
        lines.append("[Memory curation] summaries=" + str(mcur.get("summaries_count", 0)) + "  compression_candidates=" + str(mcur.get("compression_candidates_count", 0)) + "  forgetting=" + str(mcur.get("forgetting_candidates_count", 0)))
        lines.append("  forgetting_awaiting_review=" + str(mcur.get("forgetting_awaiting_review_count", 0)) + "  growth=" + str(mcur.get("memory_growth_pressure", "—")))
        if mcur.get("next_action"):
            nxt = mcur["next_action"]
            lines.append("  next: " + str(nxt.get("action", "") or nxt.get("message", "")))
    lines.append("")

    # M44I–M44L Memory intelligence (Pane 3: retrieval-grounded recommendations, weak cautions, next review)
    mi = state.get("memory_intelligence_state", {})
    if mi.get("error"):
        lines.append("[Memory intelligence] error: " + str(mi["error"]))
    elif mi:
        lines.append("[Memory intelligence] recs=" + str(mi.get("memory_backed_recommendation_count", 0)) + "  weak_cautions=" + str(mi.get("weak_memory_caution_count", 0)))
        if mi.get("top_retrieved_prior_case"):
            t = mi["top_retrieved_prior_case"]
            lines.append("  top_prior: " + str(t.get("snippet", "")[:60]) + "...")
        if mi.get("most_influential_recommendation_id"):
            lines.append("  most_influential: " + str(mi["most_influential_recommendation_id"]))
        lines.append("  next: " + str(mi.get("next_recommended_memory_review", "")))
    lines.append("")

    # M45E–M45H Shadow execution (active shadow runs, lowest confidence, next gate, takeover, safe-to-promote)
    se = state.get("shadow_execution_state", {})
    if se.get("error"):
        lines.append("[Shadow execution] error: " + str(se["error"]))
    elif se:
        lines.append("[Shadow execution] active=" + str(se.get("active_shadow_run_count", 0)) + "  takeover_candidates=" + str(se.get("forced_takeover_candidate_count", 0)))
        if se.get("lowest_confidence_run_id"):
            lines.append("  lowest_confidence: " + str(se["lowest_confidence_run_id"]) + "  score=" + str(se.get("lowest_confidence_score")))
        if se.get("next_intervention_gate_run_id"):
            lines.append("  next_gate: " + str(se["next_intervention_gate_run_id"]))
        if se.get("recent_safe_to_promote_run_id"):
            lines.append("  safe_to_promote: " + str(se["recent_safe_to_promote_run_id"]))
    lines.append("")

    # M45A–M45D Adaptive execution (active loop, next step, remaining steps, takeover point)
    ae_state = state.get("adaptive_execution_state", {})
    if ae_state.get("error"):
        lines.append("[Adaptive execution] error: " + str(ae_state["error"]))
    elif ae_state:
        lines.append("[Adaptive execution] active_loop=" + str(ae_state.get("active_loop_id") or "—") + "  running=" + str(ae_state.get("running_loop_count", 0)) + "  awaiting_takeover=" + str(ae_state.get("awaiting_takeover_count", 0)))
        if ae_state.get("next_step_index") is not None:
            lines.append("  next_step=" + str(ae_state["next_step_index"]) + "  remaining_safe_steps=" + str(ae_state.get("remaining_safe_steps") or "—") + "  branch=" + str(ae_state.get("current_branch_id") or "—"))
        if ae_state.get("next_takeover_step_index") is not None:
            lines.append("  next_takeover_at_step: " + str(ae_state["next_takeover_step_index"]))
        if ae_state.get("stop_reason") or ae_state.get("escalation_reason"):
            lines.append("  stop: " + str(ae_state.get("stop_reason") or "") + "  escalation: " + str(ae_state.get("escalation_reason") or ""))
    lines.append("")

    # M45I–M45L Supervisory control (active/paused/awaiting/takeover, most urgent)
    sc_state = state.get("supervisory_control_state", {})
    if sc_state.get("error"):
        lines.append("[Supervisory control] error: " + str(sc_state["error"]))
    elif sc_state:
        lines.append("[Supervisory control] active=" + str(sc_state.get("active_loops_count", 0)) + "  paused=" + str(sc_state.get("paused_loops_count", 0)) + "  awaiting=" + str(sc_state.get("awaiting_continuation_count", 0)) + "  taken_over=" + str(sc_state.get("taken_over_count", 0)))
        if sc_state.get("most_urgent_loop_id"):
            lines.append("  most_urgent: " + str(sc_state["most_urgent_loop_id"]) + "  reason=" + str(sc_state.get("most_urgent_reason", "")))
    lines.append("")

    # M46A–M46D Long-run health (alert, strongest drift, top degraded, next maintenance)
    lrh = state.get("long_run_health_state", {})
    if lrh.get("error"):
        lines.append("[Long-run health] error: " + str(lrh["error"]))
    elif lrh:
        lines.append("[Long-run health] alert=" + str(lrh.get("current_alert_state", "—")) + "  drift_count=" + str(lrh.get("drift_signal_count", 0)) + "  degraded=" + str(lrh.get("degraded_subsystem_count", 0)))
        if lrh.get("strongest_drift_signal_id"):
            lines.append("  strongest_drift: " + str(lrh["strongest_drift_signal_id"]))
        if lrh.get("top_degraded_subsystem_id"):
            lines.append("  top_degraded: " + str(lrh["top_degraded_subsystem_id"]))
        if lrh.get("next_recommended_maintenance") and lrh["next_recommended_maintenance"] != "none":
            lines.append("  next: " + str(lrh["next_recommended_maintenance"]))
    lines.append("")

    # M32E–M32H Just-in-time assist engine
    ae = state.get("assist_engine", {})
    if ae.get("error"):
        lines.append("[Assist] error: " + str(ae["error"]))
    elif ae:
        lines.append("[Assist] top=" + str(ae.get("top_suggestion_id", "") or "—") + "  title=" + str((ae.get("top_suggestion_title") or "—")[:40]))
        lines.append("  queue_depth=" + str(ae.get("queue_depth", 0)) + "  visible=" + str(ae.get("visible_queue_count", 0)) + "  repeated_dismissed=" + str(len(ae.get("repeated_dismissed_patterns", []))))
        lines.append("  highest_confidence=" + str(ae.get("highest_confidence_next", 0)) + "  focus_safe=" + str(ae.get("focus_safe", False)))
    lines.append("")

    # M37E–M37H Signal quality
    sq = state.get("signal_quality", {})
    if sq.get("error"):
        lines.append("[Signal quality] error: " + str(sq["error"]))
    elif sq:
        lines.append("[Signal quality] calmness=" + str(sq.get("calmness_score", "")) + "  noise=" + str(sq.get("noise_level", "")))
        lines.append("  suppressed=" + str(sq.get("suppressed_low_value_count", 0)) + "  resurfacing_candidates=" + str(sq.get("resurfacing_candidates_count", 0)))
        lines.append("  focus_protected=" + str(sq.get("focus_protected_active", False)) + "  top_high_signal=" + str(sq.get("top_high_signal_item_id", "") or "—"))
    lines.append("")

    # M38E–M38H Triage / Cohort health
    tr = state.get("triage", {})
    if tr.get("error"):
        lines.append("[Triage / Cohort health] error: " + str(tr["error"]))
    elif tr:
        lines.append("[Triage / Cohort health] open_issues=" + str(tr.get("open_issue_count", 0)) + "  highest_severity=" + str(tr.get("highest_severity", "—")) + "  top_issue=" + str(tr.get("highest_severity_issue_id", "") or "—"))
        lines.append("  unresolved_supported_surface=" + str(tr.get("unresolved_supported_surface_count", 0)) + "  recommended_downgrade=" + str(tr.get("recommended_downgrade", False)))
        lines.append("  recommended_mitigation: " + str(tr.get("recommended_mitigation", "") or "—"))

    # M38I–M38L Safe adaptation
    ad = state.get("adaptation_state", {})
    if ad.get("error"):
        lines.append("[Safe adaptation] error: " + str(ad["error"]))
    elif ad:
        lines.append("[Safe adaptation] safe_to_review=" + str(ad.get("safe_to_review_candidates_count", 0)) + "  quarantined=" + str(ad.get("quarantined_count", 0)) + "  supported_deltas_pending=" + str(ad.get("supported_surface_deltas_pending_count", 0)))
        lines.append("  recent_accepted=" + str(ad.get("recent_accepted_count", 0)) + "  recent_rejected=" + str(ad.get("recent_rejected_count", 0)))
        if ad.get("next_recommended_adaptation_review_id"):
            lines.append("  next_review: workflow-dataset adaptation show --id " + ad["next_recommended_adaptation_review_id"])
        if ad.get("quarantined_sample_ids"):
            lines.append("  quarantined_sample: " + ", ".join(ad["quarantined_sample_ids"][:5]))

    # M39I–M39L Vertical launch
    lk = state.get("launch_kit_state", {})
    if lk.get("error"):
        lines.append("[Vertical launch] error: " + str(lk["error"]))
    elif lk:
        lines.append("[Vertical launch] active_launch_kit=" + str(lk.get("active_launch_kit_id") or "—") + "  proof_met=" + str(lk.get("proof_of_value_met_count", 0)) + "  proof_pending=" + str(lk.get("proof_of_value_pending_count", 0)))
        lines.append("  first_value_milestone_reached=" + str(lk.get("first_value_milestone_reached", False)) + "  next_milestone=" + str(lk.get("first_value_progress_next_milestone") or "—"))
        if lk.get("launch_blockers"):
            lines.append("  launch_blockers: " + str(lk["launch_blockers"].get("symptom", "blocked")))
        if lk.get("next_operator_support_action"):
            lines.append("  next_operator_action: " + str(lk["next_operator_support_action"]))
        if lk.get("suggested_success_proof_report"):
            lines.append("  suggested: " + lk["suggested_success_proof_report"])
        if lk.get("recommended_rollout_decision"):
            lines.append("  recommended_rollout: " + lk["recommended_rollout_decision"])
        if lk.get("suggested_rollout_review"):
            lines.append("  rollout_review: " + lk["suggested_rollout_review"])
        vd = lk.get("value_dashboard_summary") or {}
        if vd.get("what_is_working"):
            lines.append("  working: " + "; ".join(vd["what_is_working"][:3]))
        if vd.get("what_is_not_working"):
            lines.append("  not_working: " + "; ".join(vd["what_is_not_working"][:3]))

    lines.append("")

    # M39E–M39H Curated vertical packs
    vp = state.get("vertical_packs_state", {})
    if vp.get("error"):
        lines.append("[Vertical packs] error: " + str(vp["error"]))
    elif vp:
        lines.append("[Vertical packs] active_pack=" + str(vp.get("active_curated_pack_id") or "—") + "  path=" + str(vp.get("current_first_value_path_id") or "—"))
        lines.append("  next_milestone=" + str(vp.get("next_vertical_milestone_label") or vp.get("next_vertical_milestone") or "—") + "  reached=" + str(vp.get("reached_milestone_ids", [])))
        if vp.get("blocked_vertical_onboarding_step"):
            lines.append("  blocked_step=" + str(vp["blocked_vertical_onboarding_step"].get("blocked_step_index", "")) + "  hint=" + str(vp["blocked_vertical_onboarding_step"].get("remediation_hint", "")))
        lines.append("  suggested: " + str(vp.get("suggested_next_command", "") or "—"))

    lines.append("")

    # M40E–M40H Deploy bundle
    db = state.get("deploy_bundle_state", {})
    if db.get("error"):
        lines.append("[Deploy bundle] error: " + str(db["error"]))
    elif db:
        lines.append("[Deploy bundle] active_bundle=" + str(db.get("active_bundle_id") or "—") + "  bundle=" + str(db.get("bundle_id") or "—"))
        lines.append("  validation_passed=" + str(db.get("validation_passed", False)) + "  upgrade_readiness=" + str(db.get("upgrade_readiness", False)) + "  rollback_readiness=" + str(db.get("rollback_readiness", False)))
        if db.get("blocked_deployment_risks"):
            lines.append("  blocked_risks: " + ", ".join(db["blocked_deployment_risks"][:3]))

    lines.append("")

    # M41I–M41L Ops jobs
    oj = state.get("ops_jobs_state", {})
    if oj.get("error"):
        lines.append("[Ops jobs] error: " + str(oj["error"]))
    elif oj:
        lines.append("[Ops jobs] next_due=" + str(oj.get("next_due_job_id") or "—") + "  blocked=" + str(oj.get("blocked_job_id") or "—") + "  overdue=" + str(oj.get("overdue_job_ids", [])))
        lines.append("  recent=" + str(oj.get("recent_outcome_job_id") or "—") + "  outcome=" + str(oj.get("recent_outcome_result") or "—"))
        lines.append("  recommended: " + str(oj.get("recommended_action", "") or "—"))

    lines.append("")

    # M46E–M46H Repair loops
    rl = state.get("repair_loops_state", {})
    if rl.get("error"):
        lines.append("[Repair loops] error: " + str(rl["error"]))
    elif rl:
        lines.append("[Repair loops] top_repair_needed=" + str(rl.get("top_repair_needed_subsystem") or "—") + "  active_loop=" + str(rl.get("active_repair_loop_id") or "—") + "  active_count=" + str(rl.get("active_repair_loop_count", 0)))
        lines.append("  failed_requiring_escalation=" + str(rl.get("failed_repair_requiring_escalation_id") or "—") + "  failed_count=" + str(rl.get("failed_repair_count", 0)) + "  escalated=" + str(rl.get("escalated_repair_count", 0)))
        lines.append("  verified_successful=" + str(rl.get("verified_successful_repair_id") or "—") + "  verified_count=" + str(rl.get("verified_repair_count", 0)))
        lines.append("  next: " + str(rl.get("next_recommended_maintenance_action", "—")))

    lines.append("")

    # M46I–M46L Sustained deployment reviews / stability decision pack
    sdr = state.get("stability_reviews", {})
    if sdr.get("error"):
        lines.append("[Stability reviews] error: " + str(sdr["error"]))
    elif sdr:
        lines.append("[Stability reviews] recommendation=" + str(sdr.get("current_sustained_use_recommendation", "—")) + "  state=" + str(sdr.get("watch_degraded_repair_state", "—")))
        if sdr.get("next_scheduled_deployment_review_iso"):
            lines.append("  next_review: " + str(sdr["next_scheduled_deployment_review_iso"])[:19])
        if sdr.get("top_stability_risk"):
            lines.append("  top_risk: " + str(sdr["top_stability_risk"])[:70] + "...")
    lines.append("")

    # M47A–M47D Vertical excellence (Pane 1) — first-value stage, friction, recommend-next, blocked
    ve = state.get("vertical_excellence_state", {})
    if ve.get("error"):
        lines.append("[Vertical excellence] error: " + str(ve["error"]))
    elif ve:
        stage = ve.get("current_first_value_stage", {})
        lines.append("[Vertical excellence] vertical=" + str(ve.get("vertical_id") or "—") + "  first_value_stage=" + str(stage.get("status") or "—") + "  step=" + str(stage.get("step_index", 0)) + "/" + str(stage.get("total_steps", 0)))
        lines.append("  strongest_friction=" + str(ve.get("strongest_friction_point_id") or "—") + "  blocked_cases=" + str(ve.get("blocked_first_value_cases_count", 0)))
        rec = ve.get("next_recommended_excellence_action")
        if rec:
            lines.append("  next: " + str(rec.get("command", "—")) + "  (" + str(rec.get("label", ""))[:40] + ")")
        if ve.get("top_default_path_improvement"):
            lines.append("  path_improvement: " + str(ve["top_default_path_improvement"])[:60])
    lines.append("")

    # M47E–M47H Vertical speed (Pane 2) — top workflow, friction cluster, speed-up candidate
    vs = state.get("vertical_speed_state", {})
    if vs.get("error"):
        lines.append("[Vertical speed] error: " + str(vs["error"]))
    elif vs:
        lines.append("[Vertical speed] vertical=" + str(vs.get("vertical_pack_id") or "—") + "  top_workflow=" + str(vs.get("highest_frequency_workflow_label") or "—"))
        lines.append("  friction_cluster=" + str(vs.get("biggest_friction_cluster_label") or "—") + "  speed_up_candidate=" + str(vs.get("strongest_speed_up_candidate_label") or "—"))
        lines.append("  repeat_value_bottleneck=" + str(vs.get("recent_repeat_value_bottleneck_id") or "—"))
        lines.append("  compressed=" + str(vs.get("compressed_workflow_count", "—")) + "  still_need_work=" + str(vs.get("still_needs_work_workflow_ids", []) or "—"))
        lines.append("  next: " + str(vs.get("next_recommended_friction_reduction_action", "—")))
    lines.append("")

    # M47I–M47L Quality signals + operator guidance (Pane 3)
    qg = state.get("quality_guidance", {})
    if qg.get("error"):
        lines.append("[Quality guidance] error: " + str(qg["error"]))
    elif qg:
        lines.append("[Quality guidance] ready_to_act=" + str(qg.get("strongest_ready_to_act_item", "—") or "—")[:50])
        lines.append("  most_ambiguous=" + str(qg.get("most_ambiguous_current_guidance", "—") or "—")[:50])
        lines.append("  next_improvement=" + str(qg.get("next_recommended_guidance_improvement", "—") or "—")[:60])
    lines.append("")

    # M48A–M48D Governance — preset, scope template, role map, sensitive scopes, blocked authority
    gov = state.get("governance_state", {})
    if gov.get("error"):
        lines.append("[Governance] error: " + str(gov["error"]))
    elif gov:
        lines.append("[Governance] preset=" + str(gov.get("active_governance_preset_id", "—")) + "  scope_template=" + str(gov.get("active_scope_template_id", "—")))
        lines.append("  posture=" + str(gov.get("active_governance_posture", "—")) + "  roles=" + str(len(gov.get("current_role_map", []))))
        for impl in (gov.get("preset_implications") or [])[:2]:
            lines.append("  imply: " + str(impl)[:70])
        lines.append("  sensitive_scopes=" + str(gov.get("most_sensitive_active_scopes", [])[:3]))
        lines.append("  blocked_authority_attempts=" + str(gov.get("blocked_authority_attempts_count", 0)))
        lines.append("  next: " + str(gov.get("next_recommended_governance_review", "—")))

    # M49A–M49D Continuity bundle — latest bundle, transfer-sensitive, excluded local-only
    cb = state.get("continuity_bundle_state", {})
    if cb.get("error"):
        lines.append("[Continuity bundle] error: " + str(cb["error"]))
    elif cb:
        lines.append("[Continuity bundle] latest=" + str(cb.get("latest_bundle_id", "—")) + "  profile=" + str(cb.get("bundle_profile_id", "—")))
        lines.append("  portable=" + str(cb.get("portable_count", cb.get("safe_to_transfer_count", 0))) + "  review_required=" + str(cb.get("review_required_count", "—")) + "  excluded=" + str(cb.get("excluded_count", "—")) + "  rebuild_only=" + str(cb.get("rebuild_only_count", "—")))
        lines.append("  summary: " + str(cb.get("portability_report_summary", ""))[:70])
        lines.append("  next: " + str(cb.get("next_portability_review", "—")))

    lines.append("")

    # M48E–M48H Review domains — active domains, domain-blocked approvals, required escalations, most sensitive pending
    rd = state.get("review_domains_state", {})
    if rd.get("error"):
        lines.append("[Review domains] error: " + str(rd["error"]))
    elif rd:
        lines.append("[Review domains] active=" + str(rd.get("active_review_domain_count", 0)) + "  domains=" + ", ".join(rd.get("active_review_domains", [])[:5]))
        lines.append("  domain_blocked_approvals=" + str(rd.get("domain_blocked_approvals_count", 0)) + "  required_escalations=" + str(rd.get("required_escalations_count", 0)))
        lines.append("  most_sensitive_pending=" + str(rd.get("most_sensitive_pending_review") or "—"))
        lines.append("  next: " + str(rd.get("next_recommended_review_domain_adjustment", "—")))

    lines.append("")

    # M49E–M49H Migration restore — latest candidate, blockers, reconcile-required, confidence
    mr = state.get("migration_restore_state", {})
    if mr.get("error"):
        lines.append("[Migration restore] error: " + str(mr["error"]))
    elif mr:
        lines.append("[Migration restore] latest_bundle=" + str(mr.get("latest_restore_candidate_bundle_ref") or "—") + "  blockers=" + str(mr.get("restore_blockers_count", 0)))
        lines.append("  restore_confidence=" + str(mr.get("restore_confidence_label") or "—") + "  score=" + str(mr.get("restore_confidence_score", "—")))
        lines.append("  next: " + str(mr.get("next_recommended_restore_action", "—")))

    # M50A–M50D V1 contract — vertical, core/advanced/quarantined/excluded, next freeze
    v1c = state.get("v1_contract_state", {})
    if v1c.get("error"):
        lines.append("[V1 contract] error: " + str(v1c["error"]))
    elif v1c:
        lines.append("[V1 contract] vertical=" + str(v1c.get("vertical_id", "—")) + "  has_cut=" + str(v1c.get("has_active_cut", False)))
        lines.append("  core=" + str(v1c.get("v1_core_count", 0)) + "  advanced=" + str(v1c.get("v1_advanced_count", 0)) + "  quarantined=" + str(v1c.get("quarantined_count", 0)) + "  excluded=" + str(v1c.get("excluded_count", 0)))
        lines.append("  next: " + str(v1c.get("next_freeze_action", "—"))[:60])

    lines.append("")

    # M42I–M42L Benchmark board
    bb = state.get("benchmark_board_state", {})
    if bb.get("error"):
        lines.append("[Benchmark board] error: " + str(bb["error"]))
    elif bb:
        lines.append("[Benchmark board] awaiting=" + str(bb.get("top_candidate_awaiting_decision", "—") or "—") + "  promoted=" + str(bb.get("latest_promoted_id", "—") or "—") + "  scope=" + str(bb.get("latest_promoted_scope", "—") or "—"))
        lines.append("  quarantined=" + str(bb.get("quarantined_count", 0)) + "  rollback_ready=" + str(bb.get("rollback_ready_promoted_id", "—") or "—"))
        lines.append("  next: " + str(bb.get("next_benchmark_review_action", "") or "—"))

    lines.append("")

    # M50E–M50H v1 operational discipline
    v1 = state.get("v1_ops_state", {})
    if v1.get("error"):
        lines.append("[v1 ops] error: " + str(v1["error"]))
    elif v1:
        post = v1.get("current_support_posture", {})
        lines.append("[v1 ops] support_level=" + str(post.get("support_level", "—") or "—") + "  rollback_ready=" + str(post.get("rollback_ready", False)))
        if v1.get("overdue_maintenance_or_review"):
            lines.append("  [yellow]overdue maintenance/review[/yellow]")
        if v1.get("top_unresolved_v1_risk"):
            lines.append("  top_risk: " + str(v1["top_unresolved_v1_risk"])[:80])
        lines.append("  recommended: " + str(v1.get("recommended_stable_v1_support_action", "—") or "—")[:80])

    # M50I–M50L Stable v1 gate
    sv1 = state.get("stable_v1_gate_state", {})
    if sv1.get("error"):
        lines.append("[stable v1 gate] error: " + str(sv1["error"]))
    elif sv1:
        lines.append("[stable v1 gate] " + str(sv1.get("current_stable_v1_recommendation_label", "—") or "—"))
        lines.append("  recommendation: " + str(sv1.get("current_stable_v1_recommendation", "—") or "—") + "  gate_passed=" + str(sv1.get("gate_passed", False)))
        if sv1.get("top_final_blocker"):
            lines.append("  top_blocker: " + str(sv1["top_final_blocker"])[:80])
        if sv1.get("narrow_v1_condition"):
            lines.append("  narrow_condition: " + str(sv1["narrow_v1_condition"])[:80])
        lines.append("  next_action: " + str(sv1.get("next_required_final_action", "—") or "—")[:80])

    lines.append("")

    # M33I–M33L In-flow review
    inf = state.get("in_flow", {})
    if inf.get("error"):
        lines.append("[In-flow] error: " + str(inf["error"]))
    elif inf:
        lines.append("[In-flow] draft_waiting=" + str(inf.get("latest_draft_waiting_review_id", "") or "—") + "  checkpoint=" + str(inf.get("active_review_checkpoint_id", "") or "—"))
        lines.append("  latest_handoff=" + str(inf.get("latest_handoff_id", "") or "—") + "  target=" + str(inf.get("latest_handoff_target", "") or "—"))
        lines.append("  drafts_waiting=" + str(inf.get("drafts_waiting_count", 0)) + "  promoted=" + str(len(inf.get("recent_promoted_draft_ids", []))))
    lines.append("")

    # Job packs (M23J)
    jp = state.get("job_packs", {})
    if jp.get("error"):
        lines.append("[Job packs] error: " + str(jp["error"]))
    elif jp:
        lines.append("[Job packs] total=" + str(jp.get("total", 0)) + "  simulate_only=" + str(jp.get("simulate_only_count", 0)) + "  trusted_for_real=" + str(jp.get("trusted_for_real_count", 0)) + "  approval_blocked=" + str(jp.get("approval_blocked_count", 0)) + "  recent_successful=" + str(jp.get("recent_successful_count", 0)))
    lines.append("")

    # Copilot (M23K)
    cp = state.get("copilot", {})
    if cp.get("error"):
        lines.append("[Copilot] error: " + str(cp["error"]))
    elif cp:
        lines.append("[Copilot] recommended_jobs=" + str(cp.get("recommended_jobs_count", 0)) + "  blocked=" + str(cp.get("blocked_jobs_count", 0)) + "  routines=" + str(cp.get("routines_count", 0)) + "  plan_runs=" + str(cp.get("recent_plan_runs_count", 0)) + "  reminders=" + str(cp.get("reminders_count", 0)))
        lines.append("  next: " + str(cp.get("next_copilot_action", "")))
    lines.append("")

    # Work context (M23L)
    wc = state.get("work_context", {})
    if wc.get("error"):
        lines.append("[Context] error: " + str(wc["error"]))
    elif wc:
        lines.append("[Context] snapshot=" + str(wc.get("latest_snapshot_id", "")) + "  context_recommendations=" + str(wc.get("context_recommendations_count", 0)) + "  context_blocked=" + str(wc.get("context_blocked_count", 0)))
        if wc.get("newly_recommendable_jobs"):
            lines.append("  newly_recommendable: " + ", ".join(wc["newly_recommendable_jobs"][:5]))
        if wc.get("recent_state_changes"):
            for s in wc["recent_state_changes"][:3]:
                lines.append("  " + str(s))
        lines.append("  next: " + str(wc.get("next_recommended_action", "")))
    lines.append("")

    # Action cards (M32I–M32L)
    ac = state.get("action_cards_summary", {})
    if ac.get("error"):
        lines.append("[Action cards] error: " + str(ac["error"]))
    elif ac:
        lines.append("[Action cards] total=" + str(ac.get("total_cards", 0)) + "  pending=" + str(ac.get("pending_count", 0)) + "  accepted=" + str(ac.get("accepted_count", 0)) + "  executed=" + str(ac.get("executed_count", 0)) + "  blocked=" + str(ac.get("blocked_count", 0)) + "  awaiting_approval=" + str(ac.get("awaiting_approval_count", 0)))
        hv = ac.get("highest_value_card")
        if hv:
            lines.append("  highest: " + str(hv.get("card_id", "")) + "  " + str(hv.get("title", "")[:40]))
        if ac.get("recent_outcomes"):
            for cid, out_sum in ac["recent_outcomes"][:3]:
                lines.append("  outcome " + str(cid) + ": " + str(out_sum)[:50])
        lines.append("  next: " + str(ac.get("next_action", "")))
    lines.append("")

    # M34E–M34H Bounded background runner
    br = state.get("background_runner_state", {})
    if br.get("error"):
        lines.append("[Background runner] error: " + str(br["error"]))
    elif br:
        lines.append("[Background runner] queue=" + str(br.get("queue_length", 0)) + "  next=" + str(br.get("next_automation_id") or "—") + " (" + str(br.get("next_plan_ref") or "—") + ")")
        lines.append("  active=" + str(len(br.get("active_run_ids", []))) + "  blocked=" + str(len(br.get("blocked_run_ids", []))) + "  retryable=" + str(len(br.get("retryable_run_ids", []))))
        if br.get("needs_review_automation_ids"):
            lines.append("  needs_review: " + ", ".join(br["needs_review_automation_ids"][:5]))
        lines.append("  next: " + str(br.get("next_action", "")))
    lines.append("")

    # M34I–M34L Automation inbox
    ai = state.get("automation_inbox", {})
    if ai.get("error"):
        lines.append("[Automation inbox] error: " + str(ai["error"]))
    elif ai:
        lines.append("[Automation inbox] unseen=" + str(ai.get("unseen_automation_results_count", 0)) + "  blocked_id=" + str(ai.get("most_important_blocked_automation_id") or "—"))
        lines.append("  latest_digest=" + str(ai.get("latest_recurring_digest_id") or "—") + "  next: " + str(ai.get("next_recommended_follow_up", ""))[:60])
    lines.append("")

    # Workflow episodes (M33A–M33D)
    we = state.get("workflow_episodes", {})
    if we.get("error"):
        lines.append("[Workflow episodes] error: " + str(we["error"]))
    elif we:
        ep_id = we.get("current_episode_id") or "—"
        stage = we.get("current_stage") or "—"
        next_step = we.get("likely_next_step") or "—"
        gaps_count = we.get("handoff_gaps_count", 0)
        lines.append("[Workflow episodes] episode=" + str(ep_id) + "  stage=" + str(stage) + "  next_step=" + str(next_step)[:40] + "  handoff_gaps=" + str(gaps_count))
        if we.get("handoff_gaps_summary"):
            for s in we["handoff_gaps_summary"][:3]:
                lines.append("  gap: " + str(s)[:60])
        lines.append("  next: " + str(we.get("next_action", "")))
    lines.append("")

    # Live workflow (M33E–M33H)
    lw = state.get("live_workflow_state", {})
    if lw.get("error"):
        lines.append("[Live workflow] error: " + str(lw["error"]))
    elif lw:
        run_id = lw.get("active_run_id") or "—"
        state_val = lw.get("state") or "—"
        step = lw.get("current_step_index")
        escalation = lw.get("escalation_level") or "—"
        blocked = lw.get("blocked_real_time_step")
        next_assist = (lw.get("next_recommended_assist") or "—")[:50]
        lines.append("[Live workflow] run_id=" + str(run_id) + "  state=" + str(state_val) + "  current_step=" + str(step) + "  escalation=" + str(escalation) + "  bundle=" + str(lw.get("bundle_id") or "—"))
        if blocked:
            lines.append("  blocked: " + str(blocked.get("blocked_reason", ""))[:60])
        if lw.get("stall_detected"):
            lines.append("  [yellow]stall:[/yellow] " + str(lw.get("stall_reason") or "")[:60] + "  recovery_paths=" + str(lw.get("recovery_paths_count", 0)))
        if lw.get("alternate_path_recommendations_count", 0) > 0:
            lines.append("  alternate_paths: " + str(lw.get("alternate_path_recommendations_count")) + " recommendations")
        lines.append("  next_assist: " + str(next_assist))
        lines.append("  next: " + str(lw.get("next_action", "")))
    lines.append("")

    # Automations (M34A–M34D)
    au = state.get("automations_state", {})
    if au.get("error"):
        lines.append("[Automations] error: " + str(au["error"]))
    elif au:
        lines.append("[Automations] active=" + str(len(au.get("active_trigger_ids", []))) + "  suppressed=" + str(len(au.get("suppressed_trigger_ids", []))) + "  blocked=" + str(len(au.get("blocked_trigger_ids", []))))
        lines.append("  last_matched=" + str(au.get("last_matched_trigger_id") or "—") + "  next_scheduled_workflow=" + str(au.get("next_scheduled_workflow_id") or "—"))
    lines.append("")

    # Gates + Audit (M35I–M35L)
    sg = state.get("sensitive_gates", {})
    if sg.get("error"):
        lines.append("[Gates] error: " + str(sg["error"]))
    elif sg:
        lines.append("[Gates] pending=" + str(sg.get("pending_count", 0)) + "  next_signoff=" + str(sg.get("next_required_signoff_gate_id") or "—"))
        lines.append("  rejected_deferred=" + str(len(sg.get("rejected_deferred_gate_ids", []))) + "  audit_anomalies=" + str(len(sg.get("recent_audit_anomaly_entry_ids", []))))
        lines.append("  next: " + str(sg.get("next_action", "")))
    lines.append("")

    # Corrections (M23M)
    cor = state.get("corrections", {})
    if cor.get("error"):
        lines.append("[Corrections] error: " + str(cor["error"]))
    elif cor:
        lines.append("[Corrections] recent=" + str(cor.get("recent_corrections_count", 0)) + "  proposed=" + str(cor.get("proposed_updates_count", 0)) + "  applied=" + str(cor.get("applied_updates_count", 0)) + "  reverted=" + str(cor.get("reverted_updates_count", 0)))
        if cor.get("review_recommended"):
            lines.append("  review_recommended: " + ", ".join(cor["review_recommended"][:5]))
        lines.append("  next: " + str(cor.get("next_corrections_action", "")))
    lines.append("")

    # Teaching / skills (M26I–M26L)
    ts = state.get("teaching_skills", {})
    if ts.get("error"):
        lines.append("[Teaching / skills] error: " + str(ts["error"]))
    elif ts:
        lines.append("[Teaching / skills] candidates=" + str(ts.get("candidate_skills_count", 0)) + "  accepted_recent=" + str(len(ts.get("recently_accepted_skills", []))) + "  pack_linked=" + str(ts.get("pack_linked_skills_count", 0)) + "  needing_review=" + str(ts.get("skills_needing_review_count", 0)))
        if ts.get("candidate_skill_ids"):
            lines.append("  candidate_ids: " + ", ".join(ts["candidate_skill_ids"][:5]))
    lines.append("")

    # Personal work graph (M31E–M31H)
    pg = state.get("personal_graph_summary", {})
    if pg.get("error"):
        lines.append("[Personal graph] error: " + str(pg["error"]))
    elif pg:
        lines.append("[Personal graph] exists=" + str(pg.get("graph_exists")) + "  nodes=" + str(pg.get("nodes_total", 0)) + "  edges=" + str(pg.get("edges_total", 0)) + "  routines=" + str(pg.get("routines_count", 0)) + "  strong_patterns=" + str(pg.get("strongest_patterns_count", 0)) + "  uncertain=" + str(pg.get("uncertain_patterns_count", 0)))
        if pg.get("recently_learned_routines"):
            lines.append("  recent_routines: " + ", ".join(pg["recently_learned_routines"][:5]))
        if pg.get("uncertain_needing_confirmation"):
            lines.append("  uncertain_types: " + ", ".join(str(x) for x in pg["uncertain_needing_confirmation"][:5]))
        if pg.get("graph_review_pending_routines") or pg.get("graph_review_pending_patterns"):
            lines.append("  graph_review: " + str(pg.get("graph_review_pending_routines", 0)) + " routines, " + str(pg.get("graph_review_pending_patterns", 0)) + " patterns pending")
        lines.append("  next: " + str(pg.get("next_action", "")))
    lines.append("")

    # Runtime mesh (M23T) + M42A–M42D model registry/routing
    rm = state.get("runtime_mesh", {})
    if rm.get("error"):
        lines.append("[Runtime mesh] error: " + str(rm["error"]))
    elif rm:
        lines.append("[Runtime mesh] backends=" + str(rm.get("available_backends", [])) + "  missing=" + str(rm.get("missing_runtimes", [])))
        lines.append("  desktop_copilot: backend=" + str(rm.get("recommended_backend_desktop_copilot")) + "  model_class=" + str(rm.get("recommended_model_class_desktop_copilot", "")))
        lines.append("  codebase_task: backend=" + str(rm.get("recommended_backend_codebase_task")) + "  model_class=" + str(rm.get("recommended_model_class_codebase_task", "")))
        lines.append("  integrations=" + str(rm.get("integrations_count", 0)) + "  local_only=" + str(rm.get("integrations_local_only", True)) + "  enabled=" + str(rm.get("integrations_enabled_count", 0)))
        if rm.get("active_registry_count") is not None:
            lines.append("  registry_models=" + str(rm.get("active_registry_count", 0)) + "  production_safe_routes=" + str(rm.get("production_safe_route_count", 0)) + "  degraded_or_missing=" + str(rm.get("degraded_or_missing_runtimes", [])[:5]))
        if rm.get("next_recommended_runtime_review"):
            lines.append("  next: " + str(rm.get("next_recommended_runtime_review", "")))
    lines.append("")

    # M23V Daily inbox
    di = state.get("daily_inbox", {})
    if di.get("error"):
        lines.append("[Inbox] error: " + str(di["error"]))
    elif di:
        lines.append("[Inbox] jobs=" + str(di.get("relevant_jobs_count", 0)) + "  routines=" + str(di.get("relevant_routines_count", 0)) + "  blocked=" + str(di.get("blocked_count", 0)) + "  reminders_due=" + str(di.get("reminders_due_count", 0)))
        lines.append("  next: " + str(di.get("recommended_next_action", "")))
    lines.append("")

    # M23V Trust cockpit
    tc = state.get("trust_cockpit", {})
    if tc.get("error"):
        lines.append("[Trust cockpit] error: " + str(tc["error"]))
    elif tc:
        lines.append("[Trust cockpit] benchmark=" + str(tc.get("benchmark_trust_status", "—")) + "  approvals=" + ("present" if tc.get("approval_registry_exists") else "missing") + "  staged=" + str(tc.get("release_gate_staged_count", 0)))
    lines.append("")

    # M35A–M35D Authority / trust contracts
    acs = state.get("authority_contracts_state", {})
    if acs.get("error"):
        lines.append("[Authority / Trust contracts] error: " + str(acs["error"]))
    elif acs:
        lines.append("[Authority / Trust contracts] active_tier=" + str(acs.get("active_tier_posture", "—")) + "  contracts=" + str(acs.get("contracts_count", 0)) + "  trusted_routines=" + str(acs.get("trusted_routines_count", 0)))
        if acs.get("routines_blocked_by_contract"):
            lines.append("  blocked_routines: " + ", ".join(acs["routines_blocked_by_contract"][:5]))
        lines.append("  highest_scope=" + str(acs.get("highest_authority_scope", "—")) + "  next: " + str(acs.get("next_trust_review", "")))
    lines.append("")

    # M36I–M36L Continuity engine
    ce = state.get("continuity_engine_state", {})
    if ce.get("error"):
        lines.append("[Continuity] error: " + str(ce["error"]))
    elif ce:
        sod = str(ce.get("next_best_start_of_day_action") or "—")[:50]
        res = str(ce.get("strongest_resume_target_label") or "—")[:40]
        cf = str(ce.get("most_important_carry_forward") or "—")[:50]
        ub = str(ce.get("unresolved_blocker_carried") or "—")[:40]
        lines.append("[Continuity] start_of_day=" + sod + "  resume=" + res)
        lines.append("  carry_forward=" + cf + "  unresolved_blocker=" + ub)
        lines.append("  end_of_day_readiness=" + str(ce.get("end_of_day_readiness", "—")))
    lines.append("")

    # M35E–M35H Personal operator mode
    om = state.get("operator_mode_state", {})
    if om.get("error"):
        lines.append("[Operator mode] error: " + str(om["error"]))
    elif om:
        lines.append("[Operator mode] pause=" + str(om.get("pause_kind", "—")) + "  suspended_resp=" + str(om.get("suspended_responsibility_count", 0)) + "  suspended_bundles=" + str(om.get("suspended_bundle_count", 0)))
        lines.append("  responsibilities=" + str(om.get("responsibilities_count", 0)) + "  bundles=" + str(om.get("bundles_count", 0)) + "  next: " + str(om.get("next_action", "")))
    lines.append("")

    # M48I–M48L Governed operator
    go = state.get("governed_operator_state", {})
    if go.get("error"):
        lines.append("[Governed operator] error: " + str(go["error"]))
    elif go:
        lines.append("[Governed operator] active=" + str(go.get("active_governed_delegation_scope_ids", [])) + "  suspended=" + str(go.get("suspended_delegation_scope_ids", [])))
        lines.append("  revoked=" + str(go.get("revoked_scope_ids", [])) + "  reauth_needed=" + str(go.get("reauthorization_needed_scope_ids", [])))
        lines.append("  highest_risk=" + str(go.get("highest_risk_active_scope_id", "—")) + "  next: " + str(go.get("next_governance_action", "")))
    lines.append("")

    # M49I–M49L Continuity confidence
    cc = state.get("continuity_confidence_state", {})
    if cc.get("error"):
        lines.append("[Continuity confidence] error: " + str(cc["error"]))
    elif cc:
        lines.append("[Continuity confidence] classification=" + str(cc.get("current_post_restore_confidence", "—")) + "  label=" + str(cc.get("current_post_restore_confidence_label", "—") or "—"))
        lines.append("  operator_mode_ready=" + str(cc.get("operator_mode_readiness_after_restore", "—")) + "  downgraded=" + str(cc.get("downgraded_runtime_profile_warnings", [])[:2] or "—"))
        lines.append("  next: " + str(cc.get("next_recommended_post_restore_review", "—")))
    lines.append("")

    # M23V Package readiness
    pr = state.get("package_readiness", {})
    if pr.get("error"):
        lines.append("[Package readiness] error: " + str(pr["error"]))
    elif pr:
        lines.append("[Package readiness] machine_ready=" + str(pr.get("machine_ready")) + "  ready_for_first_install=" + str(pr.get("ready_for_first_install")))
    lines.append("")

    # M37I–M37L State durability
    sd = state.get("state_durability_state", {})
    if sd.get("error"):
        lines.append("[State durability] error: " + str(sd["error"]))
    elif sd:
        lines.append("[State durability] ready=" + str(sd.get("state_health_ready", "—")) + "  degraded_ok=" + str(sd.get("degraded_but_usable", "—")) + "  resume=" + str(sd.get("resume_target_label", "—")[:35]))
        lines.append("  resume_cmd=" + str(sd.get("resume_target_command", "—")[:50]) + "  quality=" + str(sd.get("resume_quality", "—")))
        if sd.get("stale_or_corrupt_warnings", 0) > 0:
            lines.append("  warnings: corrupt=" + str(sd.get("corrupt_count", 0)) + "  stale=" + str(sd.get("stale_count", 0)) + "  recovery: " + str(sd.get("recommended_recovery_action", "—")[:45]))
    lines.append("")

    # M36A–M36D Workday
    wd = state.get("workday_state", {})
    if wd.get("error"):
        lines.append("[Workday] error: " + str(wd["error"]))
    elif wd:
        lines.append("[Workday] mode=" + str(wd.get("current_workday_mode", "—")) + "  day_id=" + str(wd.get("day_id", "—")))
        lines.append("  pending_transition=" + str(wd.get("pending_state_transition_recommendation", "—")) + "  next: " + str(wd.get("next_best_operating_action", ""))[:60])
        if wd.get("blocked_mode_transitions"):
            lines.append("  blocked: " + ", ".join(b.get("to", "") for b in wd["blocked_mode_transitions"][:3]))
    lines.append("")

    # M37 Default experience
    de = state.get("default_experience_state", {})
    if de.get("error"):
        lines.append("[Default experience] error: " + str(de["error"]))
    elif de:
        lines.append("[Default experience] profile=" + str(de.get("active_profile_id", "—")) + "  user_mode=" + str(de.get("simplified_mode_for_current_state", "—")))
        lines.append("  advanced_surfaces_hidden=" + str(de.get("advanced_surfaces_hidden_by_default_count", 0)))
        lines.append("  next_default_entry: " + str(de.get("next_recommended_default_entry_action", "—"))[:70])
    lines.append("")

    # M38A–M38D Cohort
    ch = state.get("cohort_state", {})
    if ch.get("error"):
        lines.append("[Cohort] error: " + str(ch["error"]))
    elif ch:
        lines.append("[Cohort] active=" + str(ch.get("active_cohort_id") or "—") + "  " + str(ch.get("cohort_label") or ""))
        lines.append("  supported=" + str(ch.get("supported_count", 0)) + "  experimental=" + str(ch.get("experimental_count", 0)) + "  blocked=" + str(ch.get("blocked_count", 0)))
        if ch.get("blocked_surfaces_sample"):
            lines.append("  blocked_sample: " + ", ".join(ch["blocked_surfaces_sample"][:5]))
        if ch.get("trust_posture"):
            lines.append("  " + str(ch["trust_posture"])[:60])
        if ch.get("gates_summary"):
            lines.append("  gates: " + str(ch["gates_summary"]))
        rec = ch.get("recommended_transition")
        if rec:
            lines.append("  recommend: " + str(rec.get("direction", "")) + " -> " + str(rec.get("suggested_cohort_id", "")) + "  " + str(rec.get("reason", ""))[:40])
        lines.append("  next: " + str(ch.get("next_readiness_review", "—"))[:60])
    lines.append("")

    # M39A–M39D Vertical selection
    vs = state.get("vertical_selection_state", {})
    if vs.get("error"):
        lines.append("[Vertical selection] error: " + str(vs["error"]))
    elif vs:
        lines.append("[Vertical selection] primary=" + str(vs.get("recommended_primary_vertical_id") or "—") + "  secondary=" + str(vs.get("recommended_secondary_vertical_id") or "—"))
        lines.append("  active=" + str(vs.get("active_vertical_id") or "—") + "  surfaces_hidden_by_scope=" + str(vs.get("surfaces_hidden_by_scope_count", 0)))
        lines.append("  next: " + str(vs.get("next_scope_review", "—"))[:60])
    lines.append("")

    # M40A–M40D Production cut
    pc = state.get("production_cut_state", {})
    if pc.get("error"):
        lines.append("[Production cut] error: " + str(pc["error"]))
    elif pc.get("active_cut_id"):
        lines.append("[Production cut] cut=" + str(pc.get("active_cut_id") or "—") + "  vertical=" + str(pc.get("vertical_id") or "—"))
        lines.append("  included=" + str(pc.get("included_surface_count", 0)) + "  excluded=" + str(pc.get("excluded_surface_count", 0)) + "  quarantined=" + str(pc.get("quarantined_surface_count", 0)))
        if pc.get("top_scope_risk"):
            lines.append("  scope_risk: " + str(pc["top_scope_risk"])[:60])
        lines.append("  next: " + str(pc.get("next_freeze_review", "—")))
    else:
        lines.append("[Production cut] (none)  next: workflow-dataset production-cut lock --id <vertical_id>")
    lines.append("")

    # M41A–M41D Learning lab (+ M41D.1 profile/templates)
    ll = state.get("learning_lab_state", {})
    if ll.get("error"):
        lines.append("[Learning lab] error: " + str(ll["error"]))
    elif ll:
        lines.append("[Learning lab] active=" + str(ll.get("active_experiment_id") or "—") + "  top_pending=" + str(ll.get("top_active_experiment") or "—"))
        lines.append("  patterns_in_use=" + str(ll.get("pattern_mappings_in_use_count", 0)) + "  quarantined=" + str(ll.get("quarantined_experiments_count", 0)))
        if ll.get("current_profile_id"):
            lines.append("  profile=" + str(ll.get("current_profile_id")) + "  safe_templates(local)=" + str(ll.get("safe_templates_local_count", 0)) + "  safe_templates(prod_adj)=" + str(ll.get("safe_templates_production_adjacent_count", 0)))
        lines.append("  next: " + str(ll.get("next_improvement_review", "—")))
    lines.append("")

    # M23W Environment health
    eh = state.get("environment_health", {})
    if eh.get("error"):
        lines.append("[Environment] error: " + str(eh["error"]))
    elif eh:
        lines.append("[Environment] required_ok=" + str(eh.get("required_ok")) + "  optional_ok=" + str(eh.get("optional_ok")) + "  incubator_present=" + str(eh.get("incubator_present")) + "  python=" + str(eh.get("python_version", "")))
    lines.append("")

    # M23Y Starter kits
    sk = state.get("starter_kits", {})
    if sk.get("error"):
        lines.append("[Starter kits] error: " + str(sk["error"]))
    elif sk:
        lines.append("[Starter kits] kits=" + str(sk.get("kits_count", 0)) + "  recommended=" + str(sk.get("recommended_kit_id") or "—") + "  score=" + str(sk.get("score", 0)))
    lines.append("")

    # M24A External capabilities
    ec = state.get("external_capabilities", {})
    if ec.get("error"):
        lines.append("[External capabilities] error: " + str(ec["error"]))
    elif ec:
        lines.append("[External capabilities] recommended=" + str(ec.get("recommended_count", 0)) + "  blocked=" + str(ec.get("blocked_count", 0)) + "  plans_pending=" + str(len(ec.get("plans_pending_review", []))))
    lines.append("")

    # M24D Activation executor
    ae = state.get("activation_executor", {})
    if ae.get("error"):
        lines.append("[Activation executor] error: " + str(ae["error"]))
    elif ae:
        lines.append("[Activation executor] pending=" + str(ae.get("pending_count", 0)) + "  blocked=" + str(ae.get("blocked_count", 0)) + "  failed=" + str(ae.get("failed_count", 0)) + "  enabled=" + str(len(ae.get("enabled_external_capabilities", []))))
        if ae.get("recommended_next_capability_action"):
            lines.append("  next: workflow-dataset " + str(ae.get("recommended_next_capability_action", "")))
    lines.append("")

    # M24B Value packs
    vp = state.get("value_packs", {})
    if vp.get("error"):
        lines.append("[Value packs] error: " + str(vp["error"]))
    elif vp:
        lines.append("[Value packs] packs=" + str(vp.get("packs_count", 0)) + "  recommended=" + str(vp.get("recommended_pack_id") or "—") + "  missing_prereqs=" + str(vp.get("missing_prerequisites_count", 0)))
    lines.append("")

    # M24E Provisioning
    prov = state.get("provisioning", {})
    if prov.get("error"):
        lines.append("[Provisioning] error: " + str(prov["error"]))
    elif prov:
        lines.append("[Provisioning] provisioned=" + str(prov.get("provisioned_packs", [])) + "  recipe_runs=" + str(prov.get("recipe_runs_count", 0)) + "  failed=" + str(prov.get("failed_count", 0)))
        if prov.get("recommended_next_first_value_flow"):
            lines.append("  next_first_value: " + str(prov["recommended_next_first_value_flow"])[:80])
        if prov.get("missing_prerequisites"):
            lines.append("  missing_prereqs: " + ", ".join(prov["missing_prerequisites"][:5]))
    lines.append("")

    # M24C Acceptance
    ac = state.get("acceptance", {})
    if ac.get("error"):
        lines.append("[Acceptance] error: " + str(ac["error"]))
    elif ac:
        lines.append("[Acceptance] scenarios=" + str(ac.get("scenarios_count", 0)) + "  latest_run=" + str(ac.get("latest_run_scenario_id") or "—") + "  outcome=" + str(ac.get("latest_run_outcome") or "—") + "  ready_for_trial=" + str(ac.get("latest_run_ready_for_trial")))
    lines.append("")

    # M25I Pack authoring
    pa = state.get("pack_authoring", {})
    if pa.get("error"):
        lines.append("[Pack authoring] error: " + str(pa["error"]))
    elif pa:
        lines.append("[Pack authoring] draft=" + str(len(pa.get("draft_packs", []))) + "  uncertified=" + str(len(pa.get("uncertified_packs", []))) + "  blocked=" + str(len(pa.get("blocked_certification", []))) + "  certifiable=" + str(len(pa.get("certifiable_packs", []))))
        if pa.get("highest_value_certifiable"):
            lines.append("  highest_value_certifiable: " + ", ".join(pa["highest_value_certifiable"][:5]))
    lines.append("")

    # M24F Rollout
    ro = state.get("rollout", {})
    if ro.get("error"):
        lines.append("[Rollout] error: " + str(ro["error"]))
    elif ro:
        lines.append("[Rollout] status=" + str(ro.get("rollout_status", "—")) + "  target=" + str(ro.get("target_scenario_id") or "—") + "  demo_readiness=" + str(ro.get("demo_readiness", "—")))
        if ro.get("blocked_rollout_items"):
            lines.append("  blocked: " + "; ".join(str(x) for x in ro["blocked_rollout_items"][:5]))
        lines.append("  support_bundle: " + (str(ro.get("support_bundle_freshness", "—")) or "none"))
        lines.append("  next: " + str(ro.get("next_rollout_action", "")))
    lines.append("")

    # M24J–M24M Session
    asess = state.get("active_session")
    if asess is None:
        lines.append("[Session] no active session")
    elif isinstance(asess, dict) and asess.get("error"):
        lines.append("[Session] error: " + str(asess["error"]))
    elif isinstance(asess, dict):
        lines.append("[Session] session_id=" + str(asess.get("session_id", "—")) + "  pack=" + str(asess.get("pack_id", "—")))
        lines.append("  queued=" + str(asess.get("queued_count", 0)) + "  blocked=" + str(asess.get("blocked_count", 0)) + "  ready=" + str(asess.get("ready_count", 0)) + "  artifacts=" + str(asess.get("artifacts_count", 0)))
        if asess.get("recommended_next_session_action"):
            lines.append("  next: workflow-dataset session " + str(asess["recommended_next_session_action"]))
    lines.append("")

    # M24N–M24Q Outcomes
    oc = state.get("outcomes", {})
    if oc.get("error"):
        lines.append("[Outcomes] error: " + str(oc["error"]))
    elif oc:
        lines.append("[Outcomes] sessions=" + str(oc.get("latest_session_outcomes_count", 0)) + "  history=" + str(oc.get("outcome_history_count", 0)) + "  first_value_flow_weak=" + str(oc.get("first_value_flow_weak", False)))
        if oc.get("recurring_blockers"):
            lines.append("  recurring_blockers: " + ", ".join(oc["recurring_blockers"][:5]))
        if oc.get("high_value_jobs_macros"):
            lines.append("  high_value: " + ", ".join(oc["high_value_jobs_macros"][:5]))
        if oc.get("next_recommended_improvement"):
            lines.append("  next_improvement: " + str(oc["next_recommended_improvement"])[:80])
    lines.append("")

    # M24R–M24U Distribution
    dist = state.get("distribution", {})
    if dist.get("error"):
        lines.append("[Distribution] error: " + str(dist["error"]))
    elif dist:
        lines.append("[Distribution] deploy_ready=" + str(dist.get("deploy_ready", False)) + "  bundles=" + str(dist.get("install_bundles_count", 0)))
        if dist.get("blocks"):
            lines.append("  blocks: " + ", ".join(str(b) for b in dist["blocks"][:3]))
        if dist.get("next_action"):
            lines.append("  next: workflow-dataset " + str(dist["next_action"]))
    lines.append("")

    # M25A–M25D Pack registry (M25D.1 channel policy)
    pr = state.get("pack_registry", {})
    if pr.get("error"):
        lines.append("[Pack registry] error: " + str(pr["error"]))
    elif pr:
        lines.append("[Pack registry] installed=" + str(pr.get("installed_count", 0)) + "  registry_entries=" + str(pr.get("registry_entries_count", 0)) + "  updates_available=" + str(pr.get("update_available_count", 0)))
        if pr.get("verification_failures"):
            lines.append("  verification_failures: " + ", ".join(pr["verification_failures"][:5]))
        cp = pr.get("channel_policy", {})
        if cp.get("block") or cp.get("warn"):
            lines.append("  channel_policy: block=" + str(cp.get("block", [])) + "  warn=" + str(cp.get("warn", [])) + ("  role=" + str(cp.get("active_role", "")) if cp.get("active_role") else ""))
        if pr.get("next_action"):
            lines.append("  next: workflow-dataset packs " + str(pr["next_action"]))
    lines.append("")

    # M25E–M25H Pack behavior
    pb = state.get("pack_behavior", {})
    if pb.get("error"):
        lines.append("[Pack behavior] error: " + str(pb["error"]))
    elif pb:
        lines.append("[Pack behavior] winning=" + str(pb.get("winning_pack_id") or "—") + "  active=" + str(pb.get("active_pack_ids", [])[:3]) + "  prompt_sources=" + str(pb.get("prompt_asset_sources", [])[:3]))
        if pb.get("task_defaults"):
            td = pb["task_defaults"]
            lines.append("  task_defaults: adapter=" + str(td.get("preferred_adapter") or "—") + "  model_class=" + str(td.get("preferred_model_class") or "—"))
        if pb.get("why_current_behavior"):
            lines.append("  why: " + str(pb["why_current_behavior"])[:70])
        if pb.get("retrieval_profile"):
            lines.append("  retrieval_profile: " + str(pb.get("retrieval_profile"))[:60] + " from " + str(pb.get("retrieval_profile_source_pack") or "—"))
        if pb.get("why_retrieval_profile"):
            lines.append("  why_retrieval: " + str(pb["why_retrieval_profile"])[:60])
        if pb.get("output_profile"):
            lines.append("  output_profile: " + str(pb.get("output_profile"))[:60] + " from " + str(pb.get("output_profile_source_pack") or "—"))
        if pb.get("why_output_profile"):
            lines.append("  why_output: " + str(pb["why_output_profile"])[:60])
        if pb.get("excluded_pack_ids"):
            lines.append("  excluded: " + ", ".join(pb["excluded_pack_ids"][:3]))
        if pb.get("conflict_summary"):
            lines.append("  conflict_summary: " + str(pb["conflict_summary"])[:80])
        if pb.get("conflicts"):
            for c in pb["conflicts"][:3]:
                lines.append("  conflict: " + str(c)[:70])
    lines.append("")

    # M26A–M26D Goal / plan
    gp = state.get("goal_plan", {})
    if gp.get("error"):
        lines.append("[Goal / plan] error: " + str(gp["error"]))
    elif gp:
        lines.append("[Goal / plan] goal=" + (str(gp.get("active_goal", ""))[:50] + "…" if gp.get("active_goal") else "—") + "  plan_id=" + str(gp.get("latest_plan_id", "—")) + "  steps=" + str(gp.get("plan_step_count", 0)) + "  blocked=" + str(gp.get("blocked_step_count", 0)))
        if gp.get("next_checkpoint_index") is not None:
            lines.append("  next_checkpoint: step " + str(gp["next_checkpoint_index"] + 1))
        if gp.get("expected_artifacts"):
            lines.append("  expected_artifacts: " + ", ".join(gp["expected_artifacts"][:3]))
        if gp.get("next_action"):
            lines.append("  next: workflow-dataset planner " + str(gp["next_action"]))
    lines.append("")

    # M27A–M27D Project / case
    pc = state.get("project_case", {})
    if pc.get("error"):
        lines.append("[Project / case] error: " + str(pc["error"]))
    elif pc.get("active_project_id"):
        lines.append("[Project / case] active=" + str(pc.get("active_project_id")) + "  title=" + str(pc.get("active_project_title", "")[:40]))
        gs = pc.get("goal_stack_summary", {})
        if gs:
            lines.append("  goals: " + str(gs.get("goals_count", 0)) + "  active=" + str(gs.get("active", 0)) + "  blocked=" + str(gs.get("blocked", 0)) + "  deferred=" + str(gs.get("deferred", 0)) + "  complete=" + str(gs.get("complete", 0)))
        if pc.get("project_blockers"):
            lines.append("  blockers: " + ", ".join([b.get("goal_id", "") for b in pc["project_blockers"][:5]]))
        nxt = pc.get("recommended_next_project_action")
        if nxt:
            lines.append("  next: " + str(nxt.get("action_type", "")) + " — " + str(nxt.get("label", ""))[:40])
    elif pc:
        if pc.get("next_action"):
            lines.append("[Project / case] (no active project)  next: " + str(pc["next_action"]))
    lines.append("")

    # M27I–M27L Progress / Replan
    pr = state.get("progress_replan", {})
    if pr.get("error"):
        lines.append("[Progress / Replan] error: " + str(pr["error"]))
    elif pr:
        lines.append("[Progress / Replan] replan_needed=" + str(len(pr.get("replan_needed_projects", []))) + "  stalled=" + str(len(pr.get("stalled_projects", []))) + "  advancing=" + str(len(pr.get("advancing_projects", []))) + "  blockers=" + str(pr.get("recurring_blockers_count", 0)) + "  impact=" + str(pr.get("positive_impact_count", 0)))
        if pr.get("next_intervention_candidate"):
            lines.append("  next_intervention: " + str(pr["next_intervention_candidate"]))
    lines.append("")

    # M26E–M26H Executor
    ex = state.get("executor", {})
    if ex.get("error"):
        lines.append("[Executor] error: " + str(ex["error"]))
    elif ex:
        lines.append("[Executor] run=" + str(ex.get("active_run_id") or "—") + "  plan=" + str(ex.get("plan_ref") or "—") + "  status=" + str(ex.get("status") or "—") + "  step=" + str(ex.get("current_step_index", 0)))
        if ex.get("next_checkpoint") is not None:
            lines.append("  next_checkpoint: before step " + str(ex["next_checkpoint"]))
        if ex.get("blocked_action"):
            lines.append("  blocked: " + str(ex["blocked_action"]))
        lines.append("  artifacts=" + str(ex.get("produced_artifacts_count", 0)) + "  executed=" + str(ex.get("executed_count", 0)) + "  blocked=" + str(ex.get("blocked_count", 0)))
        if ex.get("next_action"):
            lines.append("  next: workflow-dataset " + str(ex["next_action"]))
    lines.append("")

    # M27E–M27H Supervised agent loop
    sl = state.get("supervised_loop", {})
    if sl.get("error"):
        lines.append("[Supervised agent loop] error: " + str(sl["error"]))
    elif sl:
        lines.append("[Supervised agent loop] cycle=" + str(sl.get("cycle_id") or "—") + "  project=" + str(sl.get("project_slug") or "—") + "  status=" + str(sl.get("status") or "idle"))
        if sl.get("blocked_reason"):
            lines.append("  blocked: " + str(sl["blocked_reason"]))
        lines.append("  queue: pending=" + str(sl.get("pending_queue_count", 0)) + "  approved=" + str(sl.get("approved_count", 0)) + "  rejected=" + str(sl.get("rejected_count", 0)) + "  deferred=" + str(sl.get("deferred_count", 0)))
        lines.append("  last_handoff=" + str(sl.get("last_handoff_status") or "—") + "  last_run_id=" + str(sl.get("last_run_id") or "—"))
        if sl.get("next_proposed_action_label"):
            lines.append("  next_proposed: " + str(sl["next_proposed_action_label"][:80]) + ("..." if len(sl.get("next_proposed_action_label", "")) > 80 else ""))
            lines.append("  agent-loop approve --id " + str(sl.get("next_proposed_action_id", "")))
    lines.append("")

    # M28 Portfolio router (Pane 1)
    pr = state.get("portfolio_router", {})
    if pr.get("error"):
        lines.append("[Portfolio] error: " + str(pr["error"]))
    elif pr:
        lines.append("[Portfolio] active=" + str(pr.get("health_total_active", 0)) + "  " + "  ".join(pr.get("health_labels", [])))
        if pr.get("next_recommended_project"):
            lines.append("  next_recommended: " + str(pr["next_recommended_project"]))
        if pr.get("top_intervention_candidate"):
            lines.append("  top_intervention: " + str(pr["top_intervention_candidate"]))
        if pr.get("most_blocked_project"):
            lines.append("  most_blocked: " + str(pr["most_blocked_project"]))
        if pr.get("most_valuable_ready_project"):
            lines.append("  most_valuable_ready: " + str(pr["most_valuable_ready_project"]))
        stack = pr.get("priority_stack", [])[:5]
        if stack:
            lines.append("  priority_stack: " + ", ".join(f"#{s.get('rank_index')} {s.get('project_id')}" for s in stack))
    lines.append("")

    # M28E–M28H Worker lanes (Pane 3)
    wl = state.get("worker_lanes", {})
    if wl.get("error"):
        lines.append("[Worker lanes] error: " + str(wl["error"]))
    elif wl:
        lines.append("[Worker lanes] active=" + str(len(wl.get("active_lanes", []))) + "  blocked=" + str(len(wl.get("blocked_lanes", []))) + "  awaiting_review=" + str(len(wl.get("results_awaiting_review", []))) + "  total=" + str(wl.get("total_lanes", 0)))
        if wl.get("next_handoff_needed"):
            lines.append("  next_handoff: " + str(wl["next_handoff_needed"]) + "  workflow-dataset lanes results --id " + str(wl["next_handoff_needed"]))
    lines.append("")

    # M28I–M28L Human policy (Pane 2)
    hp = state.get("human_policy", {})
    if hp.get("error"):
        lines.append("[Human policy] error: " + str(hp["error"]))
    elif hp:
        lines.append("[Human policy] active_restrictions=" + str(hp.get("active_restrictions_count", 0)) + "  active_overrides=" + str(hp.get("active_overrides_count", 0)))
        if hp.get("override_ids"):
            lines.append("  override_ids: " + ", ".join(hp["override_ids"][:5]))
        lines.append("  policy board  |  policy evaluate --action <action_class> --project <id>")
    lines.append("")

    # M29I–M29L Review studio
    rs = state.get("review_studio", {})
    if rs.get("error"):
        lines.append("[Review studio] error: " + str(rs["error"]))
    elif rs:
        lines.append("[Review studio] timeline=" + str(rs.get("recent_timeline_count", 0)) + "  inbox=" + str(rs.get("inbox_count", 0)) + "  urgent=" + str(rs.get("urgent_count", 0)))
        if rs.get("oldest_unresolved_id"):
            lines.append("  oldest: " + str(rs["oldest_unresolved_id"])[:40])
        lines.append("  timeline latest  |  inbox list  |  inbox review --id <item_id>")
    lines.append("")

    # M29E–M29H Conversational (Ask)
    lines.append("[Ask] workflow-dataset ask \"What should I do next?\"  |  ask \"Why is X blocked?\"  (no auto-execute)")
    lines.append("")

    # M30A–M30D Install / upgrade
    iu = state.get("install_upgrade", {})
    if iu.get("error"):
        lines.append("[Install / upgrade] error: " + str(iu["error"]))
    elif iu:
        lines.append("[Install / upgrade] version=" + str(iu.get("current_version", "—")) + "  source=" + str(iu.get("version_source", "—")))
        lines.append("  target=" + str(iu.get("target_version", "—")) + "  upgrade_available=" + str(iu.get("upgrade_available", False)))
        lines.append("  rollback_available=" + str(iu.get("rollback_available", False)) + "  checkpoints=" + str(iu.get("rollback_checkpoints_count", 0)))
        if iu.get("blocked_reasons"):
            lines.append("  blocked: " + "; ".join(iu["blocked_reasons"][:2]))
        lines.append("  release current-version  |  release upgrade-plan  |  release upgrade-apply  |  release rollback")
    lines.append("")

    # M30I–M30L Release readiness
    rr = state.get("release_readiness", {})
    if rr.get("error"):
        lines.append("[Release readiness] error: " + str(rr["error"]))
    elif rr:
        lines.append("[Release readiness] status=" + str(rr.get("status", "")) + "  blockers=" + str(rr.get("blocker_count", 0)) + "  warnings=" + str(rr.get("warning_count", 0)) + "  supportability=" + str(rr.get("supportability_confidence", "")) + "  guidance=" + str(rr.get("guidance", "")))
        if rr.get("highest_severity_blocker"):
            lines.append("  blocker: " + str(rr["highest_severity_blocker"])[:60])
        if rr.get("handoff_pack_freshness"):
            lines.append("  handoff_pack: " + str(rr["handoff_pack_freshness"]) + "  |  release handoff-pack")
    lines.append("")

    # M40I–M40L Production launch; M40L.1 review cycles, sustained-use, post-deployment guidance
    pl = state.get("production_launch", {})
    if pl.get("error"):
        lines.append("[Production launch] error: " + str(pl["error"]))
    elif pl:
        lines.append("[Production launch] decision=" + str(pl.get("recommended_decision", "—")) + "  failed_gates=" + str(pl.get("failed_gates_count", 0)) + "  guidance=" + str(pl.get("post_deployment_guidance", "—")) + "  next: " + str(pl.get("next_launch_review_action", ""))[:60])
        if pl.get("highest_severity_blocker"):
            lines.append("  highest_blocker: " + str(pl["highest_severity_blocker"])[:80])
        if pl.get("post_deployment_reason"):
            lines.append("  post_deploy_reason: " + str(pl["post_deployment_reason"])[:70])
        if pl.get("latest_review_cycle_at"):
            lines.append("  latest_review: " + str(pl["latest_review_cycle_at"])[:24] + "  checkpoint_kind=" + str(pl.get("latest_sustained_use_checkpoint_kind", "—")))
        if pl.get("ongoing_summary_one_liner"):
            lines.append("  ongoing: " + str(pl["ongoing_summary_one_liner"])[:80])
    lines.append("")

    # M41E–M41H Council
    co = state.get("council", {})
    if co.get("error"):
        lines.append("[Council] error: " + str(co["error"]))
    elif co:
        lines.append("[Council] reviews=" + str(co.get("active_reviews_count", 0)) + "  high_risk=" + str(co.get("highest_risk_pending_subject_id", "—") or "—") + "  promoted=" + str(co.get("latest_promoted_subject_id", "—") or "—") + "  quarantined=" + str(co.get("latest_quarantined_subject_id", "—") or "—"))
    lines.append("")

    # M30E–M30H Reliability
    rel = state.get("reliability", {})
    if rel.get("error"):
        lines.append("[Reliability] error: " + str(rel["error"]))
    elif rel:
        lines.append("[Reliability] golden_path_health=" + str(rel.get("golden_path_health", "—")) + "  release_confidence=" + str(rel.get("release_confidence_summary", "—")))
        if rel.get("recent_regressions"):
            lines.append("  recent_regressions: " + ", ".join(rel["recent_regressions"][:3]))
        if rel.get("top_recovery_case"):
            lines.append("  top_recovery: workflow-dataset recovery guide --case " + str(rel["top_recovery_case"]))
        lines.append("  reliability list  |  reliability run --id <path_id>  |  reliability report --latest")
    lines.append("")

    # M31I–M31L Personal adaptation
    pa = state.get("personal_adaptation", {})
    if pa.get("error"):
        lines.append("[Personal adaptation] error: " + str(pa["error"]))
    elif pa:
        lines.append("[Personal adaptation] preference_candidates=" + str(pa.get("preference_candidates_count", 0)) + "  style_candidates=" + str(pa.get("style_candidates_count", 0)) + "  accepted=" + str(pa.get("accepted_count", 0)) + "  low_confidence=" + str(pa.get("low_confidence_count", 0)))
        if pa.get("strongest_patterns"):
            lines.append("  strongest: " + ", ".join(pa["strongest_patterns"][:3]))
        lines.append("  personal preferences  |  personal style-candidates  |  personal apply-preference --id <id>  |  personal explain-preference --id <id>")
    lines.append("")

    # Next action
    lines.append("--- Recommended next action ---")
    lines.append("  action: " + next_rec.get("action", "hold"))
    lines.append("  rationale: " + next_rec.get("rationale", ""))
    if next_rec.get("detail"):
        lines.append("  detail: " + str(next_rec["detail"]))
    lines.append("")
    lines.append("(Operator-controlled. No automatic changes.)")
    return "\n".join(lines)
