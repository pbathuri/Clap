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

    # Runtime mesh (M23T)
    rm = state.get("runtime_mesh", {})
    if rm.get("error"):
        lines.append("[Runtime mesh] error: " + str(rm["error"]))
    elif rm:
        lines.append("[Runtime mesh] backends=" + str(rm.get("available_backends", [])) + "  missing=" + str(rm.get("missing_runtimes", [])))
        lines.append("  desktop_copilot: backend=" + str(rm.get("recommended_backend_desktop_copilot")) + "  model_class=" + str(rm.get("recommended_model_class_desktop_copilot", "")))
        lines.append("  codebase_task: backend=" + str(rm.get("recommended_backend_codebase_task")) + "  model_class=" + str(rm.get("recommended_model_class_codebase_task", "")))
        lines.append("  integrations=" + str(rm.get("integrations_count", 0)) + "  local_only=" + str(rm.get("integrations_local_only", True)) + "  enabled=" + str(rm.get("integrations_enabled_count", 0)))
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

    # M23V Package readiness
    pr = state.get("package_readiness", {})
    if pr.get("error"):
        lines.append("[Package readiness] error: " + str(pr["error"]))
    elif pr:
        lines.append("[Package readiness] machine_ready=" + str(pr.get("machine_ready")) + "  ready_for_first_install=" + str(pr.get("ready_for_first_install")))
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
