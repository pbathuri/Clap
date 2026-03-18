"""
M27L.1: Intervention playbooks — trigger pattern, operator intervention, agent next step, escalation/defer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PLAYBOOK_IDS = (
    "stalled_founder_ops",
    "blocked_analyst_case",
    "developer_stuck_approval_capability",
    "document_heavy_stuck_extraction_review",
)


@dataclass
class InterventionPlaybook:
    """Single intervention playbook for stalled/blocked recovery."""
    playbook_id: str
    title: str
    trigger_pattern: str
    operator_intervention: str
    agent_next_step: str
    escalation_defer_guidance: str
    trigger_keywords: list[str] = field(default_factory=list)  # for matching
    trigger_cause_codes: list[str] = field(default_factory=list)  # outcome blocked cause_code

    def to_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "title": self.title,
            "trigger_pattern": self.trigger_pattern,
            "operator_intervention": self.operator_intervention,
            "agent_next_step": self.agent_next_step,
            "escalation_defer_guidance": self.escalation_defer_guidance,
            "trigger_keywords": list(self.trigger_keywords),
            "trigger_cause_codes": list(self.trigger_cause_codes),
        }


def get_default_playbooks() -> list[InterventionPlaybook]:
    """Return built-in intervention playbooks."""
    return [
        InterventionPlaybook(
            playbook_id="stalled_founder_ops",
            title="Stalled founder ops project",
            trigger_pattern="Stalled founder-ops project: 2+ sessions with disposition fix/pause, pack founder_ops or role founder, blocked_count > 0.",
            operator_intervention="Review approval registry; unblock path/scope if safe. Run value-packs first-run for founder_ops_plus if not provisioned. Check mission-control trust cockpit. Run: workflow-dataset progress board, then replan recommend.",
            agent_next_step="Replan with current goal; suggest simulate-only next step; do not auto-execute real actions until operator confirms approvals.",
            escalation_defer_guidance="If approvals cannot be extended: defer to human; document blocker in outcomes and set disposition=fix. Use corrections add for any parameter/style fix.",
            trigger_keywords=["founder", "founder_ops", "ops"],
            trigger_cause_codes=["approval_missing", "path_scope_denied", "policy_denied"],
        ),
        InterventionPlaybook(
            playbook_id="blocked_analyst_case",
            title="Blocked analyst case",
            trigger_pattern="Blocked analyst case: sessions with pack analyst or role analyst, recurring blocked_causes (job_not_found, routine_not_found, or approval_missing).",
            operator_intervention="Verify job_packs and routines exist for analyst pack. Run jobs seed if needed. Run value-packs recommend; provision analyst_research_plus if appropriate. Check outcomes patterns for recurring_blockers.",
            agent_next_step="Suggest replan with available jobs/routines only; avoid recommending unprovisioned workflows. Offer simulate run for next best step.",
            escalation_defer_guidance="If job/routine missing: defer to operator to add pack or mark scope out-of-scope. Log in outcomes with suggested_follow_up.",
            trigger_keywords=["analyst", "analyst_research", "research"],
            trigger_cause_codes=["job_not_found", "routine_not_found", "approval_missing"],
        ),
        InterventionPlaybook(
            playbook_id="developer_stuck_approval_capability",
            title="Developer workflow stuck on approval/capability",
            trigger_pattern="Developer workflow stuck: plan or executor blocked on approval or capability; step_class human_required or blocked; cause approval_missing or path_scope_denied.",
            operator_intervention="Review capability_discovery approval registry. Add path or action scope for sandbox if safe. Run trust cockpit; run acceptance report. Do not disable safety; extend scope explicitly.",
            agent_next_step="Pause on blocked step; surface approval_required and blocked_reason. Recommend operator run: approvals review, then executor resume after approval.",
            escalation_defer_guidance="If capability cannot be granted: defer step; suggest alternative path (e.g. simulate-only branch) or document as human_required and move to next checkpoint.",
            trigger_keywords=["developer", "approval", "capability", "path_scope", "sandbox"],
            trigger_cause_codes=["approval_missing", "path_scope_denied", "runtime_unavailable"],
        ),
        InterventionPlaybook(
            playbook_id="document_heavy_stuck_extraction_review",
            title="Document-heavy workflow stuck on extraction/review",
            trigger_pattern="Document-heavy workflow stuck: sessions with many artifacts or intake; blocked or partial outcomes; disposition fix/pause; suggests extraction or review bottleneck.",
            operator_intervention="Check intake_labels and unreviewed count in context. Run dashboard workspace for artifact list. Consider batch review or narrowing scope. Run outcomes patterns to see which source_ref is blocking.",
            agent_next_step="Suggest smaller batch or single-doc flow; recommend next best document for review. Do not auto-extract at scale without operator confirmation.",
            escalation_defer_guidance="If extraction/review backlog is large: defer to operator to triage or accept partial run. Log incomplete_work in session outcome with suggested_follow_up.",
            trigger_keywords=["document", "extraction", "review", "intake", "artifact"],
            trigger_cause_codes=["timeout", "user_abandoned", "other"],
        ),
    ]


def list_playbooks() -> list[InterventionPlaybook]:
    """Return all default playbooks."""
    return get_default_playbooks()
