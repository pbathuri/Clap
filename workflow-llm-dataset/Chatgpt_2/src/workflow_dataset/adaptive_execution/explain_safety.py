"""
M45D.1: Operator-facing explanation of why a loop template is safe or blocked.
"""

from __future__ import annotations

from workflow_dataset.adaptive_execution.models import BoundedExecutionLoop
from workflow_dataset.adaptive_execution.profiles import get_profile, get_profile_why_safe, get_profile_when_blocked
from workflow_dataset.adaptive_execution.templates import get_template, explain_template_safety


def explain_loop_safety(
    loop: BoundedExecutionLoop,
    is_blocked: bool = False,
    blocked_reason: str = "",
) -> dict[str, str]:
    """
    Build operator-facing explanation: why this loop is safe or why it is blocked.
    Uses profile and template when set on the loop.
    Returns { "summary", "profile_why_safe", "profile_when_blocked", "template_why_safe", "template_why_blocked" }.
    """
    out: dict[str, str] = {
        "summary": "",
        "profile_why_safe": "",
        "profile_when_blocked": "",
        "template_why_safe": "",
        "template_why_blocked": "",
    }
    if loop.profile_id:
        out["profile_why_safe"] = get_profile_why_safe(loop.profile_id)
        out["profile_when_blocked"] = get_profile_when_blocked(loop.profile_id)
    if loop.template_id:
        t_explain = explain_template_safety(loop.template_id, is_blocked=is_blocked, blocked_reason=blocked_reason)
        out["template_why_safe"] = t_explain.get("why_safe", "")
        out["template_why_blocked"] = t_explain.get("why_blocked", "")
        out["summary"] = t_explain.get("summary", "")
    if not out["summary"] and loop.profile_id:
        if is_blocked:
            out["summary"] = f"Loop uses profile '{loop.profile_id}'. Blocked: {out['profile_when_blocked']}"
        else:
            out["summary"] = f"Loop uses profile '{loop.profile_id}': {out['profile_why_safe'][:100]}..."
    if not out["summary"]:
        out["summary"] = "No profile or template set; see plan checkpoints and max_steps for bounds."
    return out


def format_safety_explanation(expl: dict[str, str]) -> str:
    """Format explain_loop_safety result as multi-line text for CLI."""
    lines = [expl.get("summary", "")]
    if expl.get("profile_why_safe"):
        lines.append("Profile (why safe): " + expl["profile_why_safe"][:200] + ("..." if len(expl["profile_why_safe"]) > 200 else ""))
    if expl.get("profile_when_blocked"):
        lines.append("Profile (when blocked): " + expl["profile_when_blocked"][:200])
    if expl.get("template_why_safe"):
        lines.append("Template (why safe): " + expl["template_why_safe"][:200] + ("..." if len(expl["template_why_safe"]) > 200 else ""))
    if expl.get("template_why_blocked"):
        lines.append("Template (when blocked): " + expl["template_why_blocked"][:200])
    return "\n".join(lines)
