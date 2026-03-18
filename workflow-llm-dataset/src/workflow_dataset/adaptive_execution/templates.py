"""
M45D.1: Loop templates for common bounded workflows — weekly summary, approval sweep, resume, single job.
"""

from __future__ import annotations

from workflow_dataset.adaptive_execution.models import LoopTemplate
from workflow_dataset.adaptive_execution.profiles import (
    PROFILE_CONSERVATIVE,
    PROFILE_BALANCED,
    PROFILE_REVIEW_HEAVY,
)

TEMPLATE_WEEKLY_SUMMARY = "weekly_summary"
TEMPLATE_APPROVAL_SWEEP = "approval_sweep"
TEMPLATE_RESUME_CONTINUITY = "resume_continuity"
TEMPLATE_SINGLE_JOB_RUN = "single_job_run"

_TEMPLATES: list[LoopTemplate] = [
    LoopTemplate(
        template_id=TEMPLATE_WEEKLY_SUMMARY,
        label="Weekly summary",
        description="Bounded loop for generating or publishing a weekly summary.",
        goal_hint="Weekly summary",
        default_profile_id=PROFILE_BALANCED,
        required_approval_scopes=["checkpoint_before_real"],
        max_steps_default=10,
        why_safe="This template is safe because it uses a bounded step count and requires a checkpoint before any real (non-simulate) execution; the default profile adds plan checkpoints.",
        why_blocked="Blocked if approval registry or checkpoint policy is missing, or if the plan compiles to steps that require higher trust than the current tier.",
    ),
    LoopTemplate(
        template_id=TEMPLATE_APPROVAL_SWEEP,
        label="Approval sweep",
        description="Loop over pending approvals; one step per approval or batch.",
        goal_hint="Approval sweep",
        default_profile_id=PROFILE_REVIEW_HEAVY,
        required_approval_scopes=["approval_registry", "checkpoint_before_real"],
        max_steps_default=20,
        why_safe="Review-heavy profile ensures every step is reviewed; approval sweep only presents items from the approval registry and does not execute without explicit approval.",
        why_blocked="Blocked when approval registry is not configured or when trust policy does not allow review-heavy execution.",
    ),
    LoopTemplate(
        template_id=TEMPLATE_RESUME_CONTINUITY,
        label="Resume / continuity",
        description="Resume from last stop or continue a continuity workflow.",
        goal_hint="Resume continuity",
        default_profile_id=PROFILE_BALANCED,
        required_approval_scopes=[],
        max_steps_default=15,
        why_safe="Bounded steps and plan-derived checkpoints; resume only continues already-scoped work from memory or session state.",
        why_blocked="Blocked when no resume context is available or when the continuity engine reports an unresolved blocker that requires human decision.",
    ),
    LoopTemplate(
        template_id=TEMPLATE_SINGLE_JOB_RUN,
        label="Single job run",
        description="Run one job or macro as a single-step bounded loop.",
        goal_hint="Run single job",
        default_profile_id=PROFILE_CONSERVATIVE,
        required_approval_scopes=["checkpoint_before_real"],
        max_steps_default=1,
        why_safe="Single step with conservative profile: review before first (and only) step, simulate-first; safe for trying one job or macro.",
        why_blocked="Blocked if the job or macro is not in the allowed set for the current trust tier or requires approval that is not yet granted.",
    ),
]


def list_templates() -> list[LoopTemplate]:
    """Return all loop templates."""
    return list(_TEMPLATES)


def get_template(template_id: str) -> LoopTemplate | None:
    """Return template by id."""
    for t in _TEMPLATES:
        if t.template_id == template_id:
            return t
    return None


def explain_template_safety(
    template_id: str,
    is_blocked: bool = False,
    blocked_reason: str = "",
) -> dict[str, str]:
    """
    Operator-facing explanation: why this template is safe or why it is blocked.
    Returns { "why_safe", "why_blocked", "summary" }.
    """
    t = get_template(template_id)
    if not t:
        return {
            "why_safe": "",
            "why_blocked": f"Unknown template {template_id}.",
            "summary": f"Unknown template {template_id}.",
        }
    why_safe = t.why_safe or "This template has no specific safety explanation."
    why_blocked = blocked_reason or t.why_blocked or "See trust and approval configuration."
    if is_blocked:
        summary = f"Template '{t.label}' is blocked: {why_blocked}"
    else:
        summary = f"Template '{t.label}' is safe to use when conditions are met: {why_safe[:120]}..."
    return {
        "why_safe": why_safe,
        "why_blocked": why_blocked,
        "summary": summary,
    }
