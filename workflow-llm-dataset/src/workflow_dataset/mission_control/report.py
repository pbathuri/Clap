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

    # Next action
    lines.append("--- Recommended next action ---")
    lines.append("  action: " + next_rec.get("action", "hold"))
    lines.append("  rationale: " + next_rec.get("rationale", ""))
    if next_rec.get("detail"):
        lines.append("  detail: " + str(next_rec["detail"]))
    lines.append("")
    lines.append("(Operator-controlled. No automatic changes.)")
    return "\n".join(lines)
