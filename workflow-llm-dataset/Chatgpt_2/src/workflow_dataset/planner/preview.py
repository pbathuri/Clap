"""
M26D: Plan preview and graph formatting for CLI.
"""

from __future__ import annotations

from workflow_dataset.planner.schema import Plan


def format_plan_preview(plan: Plan) -> str:
    """Plain-text preview: goal, step count, blocked, checkpoints, expected outputs."""
    lines = [
        "=== Plan preview ===",
        "",
        f"Plan ID: {plan.plan_id}",
        f"Goal: {plan.goal_text or '(none)'}",
        f"Steps: {len(plan.steps)}",
        f"Blocked: {len(plan.blocked_conditions)}",
        f"Checkpoints: {len(plan.checkpoints)}",
        "",
        "Sources used: " + ", ".join(plan.sources_used or ["—"]),
        "",
    ]
    for s in plan.steps:
        line = f"  {s.step_index + 1}. {s.label}  [{s.step_class}]"
        if s.blocked_reason:
            line += f"  BLOCKED: {s.blocked_reason}"
        if s.approval_required or s.checkpoint_before:
            line += "  [human approval]"
        lines.append(line)
    if plan.expected_artifacts:
        lines.append("")
        lines.append("Expected outputs:")
        for a in plan.expected_artifacts:
            lines.append(f"  - {a.label}")
    return "\n".join(lines)


def format_plan_graph(plan: Plan) -> str:
    """Dependency graph as text: nodes = steps, edges = dependencies."""
    lines = [
        "=== Plan dependency graph ===",
        "",
        f"Plan ID: {plan.plan_id}",
        "",
    ]
    for s in plan.steps:
        lines.append(f"  node_{s.step_index}  [label=\"{s.label[:40]}...\"  class={s.step_class}]")
    for e in plan.edges:
        lines.append(f"  node_{e.source_index} -> node_{e.target_index}  [{e.edge_type}]")
    if plan.checkpoints:
        lines.append("")
        lines.append("Checkpoints:")
        for c in plan.checkpoints:
            lines.append(f"  checkpoint after node_{c.step_index}: {c.label or 'approval'}")
    return "\n".join(lines)
