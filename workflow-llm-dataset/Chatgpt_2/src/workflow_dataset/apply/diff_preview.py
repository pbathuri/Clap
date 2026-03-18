"""
Render diff/preview summary of apply plan: what would be created, overwritten, skipped.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.apply.apply_models import ApplyPlan


def render_diff_preview(plan: ApplyPlan) -> str:
    """Produce a text preview of the apply plan for user inspection."""
    lines = [
        "# Apply plan preview",
        "",
        f"**Plan ID:** {plan.plan_id}",
        f"**Estimated file count:** {plan.estimated_file_count}",
        "",
        "## Would be created",
        "",
    ]
    created = [o for o in plan.operations if o.get("op") == "create"]
    for o in created[:50]:
        lines.append(f"- `{o.get('source', '')}` -> `{o.get('target', '')}`")
    if len(created) > 50:
        lines.append(f"... and {len(created) - 50} more")
    lines.append("")
    if plan.overwrite_candidates:
        lines.append("## Would be overwritten (backup created if enabled)")
        lines.append("")
        for p in plan.overwrite_candidates[:30]:
            lines.append(f"- `{p}`")
        if len(plan.overwrite_candidates) > 30:
            lines.append(f"... and {len(plan.overwrite_candidates) - 30} more")
        lines.append("")
    if plan.conflicts:
        lines.append("## Conflicts (need --allow-overwrite or resolve manually)")
        lines.append("")
        for c in plan.conflicts[:20]:
            lines.append(f"- {c.get('source', '')} -> {c.get('target', '')} ({c.get('reason', '')})")
        lines.append("")
    if plan.skipped_paths:
        lines.append("## Skipped")
        lines.append("")
        for p in plan.skipped_paths[:20]:
            lines.append(f"- `{p}`")
        lines.append("")
    lines.append("---")
    lines.append("Run with `--confirm` to apply. Rollback token will be printed after apply.")
    return "\n".join(lines)
