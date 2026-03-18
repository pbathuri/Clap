"""
M26D: Plan explanation — why this plan, sources, packs/skills/macros reused, blocked, human approval, expected outputs.
"""

from __future__ import annotations

from workflow_dataset.planner.schema import Plan


def explain_plan(plan: Plan) -> str:
    """
    Produce a human-readable explanation: why chosen, what influenced it, what is blocked,
    where human approval is required, what outputs are expected.
    """
    lines: list[str] = []
    lines.append("## Plan explanation")
    lines.append("")
    if plan.goal_text:
        lines.append(f"**Goal:** {plan.goal_text}")
        lines.append("")
    lines.append(f"**Plan ID:** {plan.plan_id}")
    lines.append("")
    if plan.sources_used:
        lines.append("### Sources used")
        for s in plan.sources_used:
            lines.append(f"- {s}")
        lines.append("")
    lines.append("### Steps")
    for s in plan.steps:
        line = f"- {s.step_index + 1}. {s.label}  [{s.step_class}]"
        if s.provenance:
            line += f"  (from {s.provenance.kind}:{s.provenance.ref})"
        if s.blocked_reason:
            line += f"  — **Blocked:** {s.blocked_reason}"
        if s.approval_required or s.checkpoint_before:
            line += "  — **Human approval required**"
        lines.append(line)
    if plan.checkpoints:
        lines.append("")
        lines.append("### Checkpoints (human approval required before proceeding)")
        for c in plan.checkpoints:
            lines.append(f"- After step {c.step_index + 1}: {c.label or 'approval'}")
    if plan.blocked_conditions:
        lines.append("")
        lines.append("### Blocked")
        for b in plan.blocked_conditions:
            lines.append(f"- {b.reason}" + (f" (step {b.step_index + 1})" if b.step_index is not None else ""))
    if plan.expected_artifacts:
        lines.append("")
        lines.append("### Expected outputs")
        for a in plan.expected_artifacts:
            lines.append(f"- {a.label}" + (f" (step {a.step_index + 1})" if a.step_index is not None else ""))
    return "\n".join(lines)
