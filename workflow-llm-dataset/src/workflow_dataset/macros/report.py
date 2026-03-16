"""
M23V/M23P: Format macro preview (with step types), blocked steps, run state.
"""

from __future__ import annotations

from workflow_dataset.copilot.plan import PlanPreview
from workflow_dataset.macros.runner import macro_preview, get_blocked_steps, get_macro_steps
from workflow_dataset.macros.step_classifier import explain_step_categories
from workflow_dataset.macros.schema import Macro


def format_macro_preview(plan: PlanPreview | None, macro_id: str = "", mode: str = "simulate", repo_root=None) -> str:
    """Produce human-readable macro preview with M23P step classification."""
    if not plan:
        return f"Macro '{macro_id}': no preview (not found or invalid)."
    m = mode or plan.mode
    steps = get_macro_steps(macro_id, mode=m, repo_root=repo_root)
    lines = [
        f"=== Macro preview: {macro_id} ===",
        "",
        f"Plan ID: {plan.plan_id}",
        f"Mode: {plan.mode}",
        f"Jobs: {', '.join(plan.job_pack_ids)}",
        "",
        explain_step_categories(),
        "",
    ]
    if plan.blocked:
        lines.append("[Blocked]")
        for j in plan.blocked:
            lines.append(f"  {j}: {plan.blocked_reasons.get(j, '')}")
        lines.append("")
    if steps:
        lines.append("[Steps (classified)]")
        for i, s in enumerate(steps[:20]):
            lines.append(f"  {i+1}. {s.job_pack_id} — {s.step_type} (simulate_ok={s.simulate_eligible}, real_ok={s.real_mode_eligible})")
        lines.append("")
    elif plan.step_previews:
        lines.append("[Step previews]")
        for i, s in enumerate(plan.step_previews[:15]):
            lines.append(f"  {i+1}. {s.get('job_pack_id', '')} — {s.get('mode', '')}")
        lines.append("")
    lines.append("(No execution. Use: workflow-dataset macro run --id " + (macro_id or "MACRO_ID") + " --mode " + plan.mode + " [--stop-at-checkpoints])")
    return "\n".join(lines)


def format_blocked_steps_report(macro_id: str, run_id: str | None = None, repo_root=None) -> str:
    """Format blocked steps for a macro run."""
    blocked = get_blocked_steps(macro_id, run_id=run_id, repo_root=repo_root)
    lines = [f"=== Blocked steps: {macro_id} ===", ""]
    if run_id:
        lines.append(f"Run: {run_id}")
        lines.append("")
    if not blocked:
        lines.append("No blocked steps.")
        return "\n".join(lines)
    for b in blocked:
        lines.append(f"  {b.get('job_pack_id', '')}: {b.get('reason', '')}")
    return "\n".join(lines)
