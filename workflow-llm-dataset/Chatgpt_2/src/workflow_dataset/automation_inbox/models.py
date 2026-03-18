"""
M34I–M34L: Automation inbox and recurring outcome digest models.

Automation inbox item, recurring digest, blocked automation review item,
background result summary, failed/suppressed explanation, human follow-up recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Automation inbox item kinds
ITEM_AUTOMATION_RESULT = "automation_result"
ITEM_RECURRING_DIGEST = "recurring_digest"
ITEM_BLOCKED_AUTOMATION = "blocked_automation"
ITEM_BACKGROUND_RESULT_SUMMARY = "background_result_summary"
ITEM_FAILED_SUPPRESSED = "failed_suppressed_automation"
ITEM_FOLLOW_UP_RECOMMENDATION = "human_follow_up_recommendation"

AUTOMATION_INBOX_ITEM_KINDS = (
    ITEM_AUTOMATION_RESULT,
    ITEM_RECURRING_DIGEST,
    ITEM_BLOCKED_AUTOMATION,
    ITEM_BACKGROUND_RESULT_SUMMARY,
    ITEM_FAILED_SUPPRESSED,
    ITEM_FOLLOW_UP_RECOMMENDATION,
)

# Decision status for inbox items
STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
STATUS_ARCHIVED = "archived"
STATUS_DISMISSED = "dismissed"
STATUS_ESCALATED = "escalated"

AUTOMATION_INBOX_STATUSES = (STATUS_PENDING, STATUS_ACCEPTED, STATUS_ARCHIVED, STATUS_DISMISSED, STATUS_ESCALATED)


@dataclass
class AutomationInboxItem:
    """One automation-related item in the automation inbox."""
    item_id: str = ""
    kind: str = ""
    status: str = STATUS_PENDING
    summary: str = ""
    created_at: str = ""
    priority: str = "medium"  # low | medium | high | urgent
    run_id: str = ""
    automation_id: str = ""
    plan_ref: str = ""
    project_id: str = ""
    outcome_summary: str = ""
    failure_code: str = ""  # blocked | policy_suppressed | transient | degraded
    entity_refs: dict[str, str] = field(default_factory=dict)
    source_ref: str = ""
    operator_notes: str = ""
    decided_at: str = ""
    decision_note: str = ""
    digest_id: str = ""  # if item was generated from a digest

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "status": self.status,
            "summary": self.summary,
            "created_at": self.created_at,
            "priority": self.priority,
            "run_id": self.run_id,
            "automation_id": self.automation_id,
            "plan_ref": self.plan_ref,
            "project_id": self.project_id,
            "outcome_summary": self.outcome_summary,
            "failure_code": self.failure_code,
            "entity_refs": dict(self.entity_refs),
            "source_ref": self.source_ref,
            "operator_notes": self.operator_notes,
            "decided_at": self.decided_at,
            "decision_note": self.decision_note,
            "digest_id": self.digest_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AutomationInboxItem":
        return cls(
            item_id=d.get("item_id", ""),
            kind=d.get("kind", ""),
            status=d.get("status", STATUS_PENDING),
            summary=d.get("summary", ""),
            created_at=d.get("created_at", ""),
            priority=d.get("priority", "medium"),
            run_id=d.get("run_id", ""),
            automation_id=d.get("automation_id", ""),
            plan_ref=d.get("plan_ref", ""),
            project_id=d.get("project_id", ""),
            outcome_summary=d.get("outcome_summary", ""),
            failure_code=d.get("failure_code", ""),
            entity_refs=dict(d.get("entity_refs", {})),
            source_ref=d.get("source_ref", ""),
            operator_notes=d.get("operator_notes", ""),
            decided_at=d.get("decided_at", ""),
            decision_note=d.get("decision_note", ""),
            digest_id=d.get("digest_id", ""),
        )


@dataclass
class RecurringDigest:
    """One recurring outcome digest (morning, project, blocked, approval-followup)."""
    digest_id: str = ""
    digest_type: str = ""  # morning_automation | project_automation | blocked_automation | approval_followup
    generated_at: str = ""
    title: str = ""
    completed_runs: list[str] = field(default_factory=list)  # run_id or summary lines
    blocked_or_failed: list[str] = field(default_factory=list)
    approval_follow_ups: list[str] = field(default_factory=list)
    most_important_follow_up: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "digest_id": self.digest_id,
            "digest_type": self.digest_type,
            "generated_at": self.generated_at,
            "title": self.title,
            "completed_runs": list(self.completed_runs),
            "blocked_or_failed": list(self.blocked_or_failed),
            "approval_follow_ups": list(self.approval_follow_ups),
            "most_important_follow_up": self.most_important_follow_up,
            "details": dict(self.details),
            "errors": list(self.errors),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RecurringDigest":
        return cls(
            digest_id=d.get("digest_id", ""),
            digest_type=d.get("digest_type", ""),
            generated_at=d.get("generated_at", ""),
            title=d.get("title", ""),
            completed_runs=list(d.get("completed_runs", [])),
            blocked_or_failed=list(d.get("blocked_or_failed", [])),
            approval_follow_ups=list(d.get("approval_follow_ups", [])),
            most_important_follow_up=d.get("most_important_follow_up", ""),
            details=dict(d.get("details", {})),
            errors=list(d.get("errors", [])),
        )


@dataclass
class BlockedAutomationReviewItem:
    """Blocked automation needing human review (run_id, reason, recovery hint)."""
    run_id: str = ""
    automation_id: str = ""
    plan_ref: str = ""
    blocked_reason: str = ""
    failure_code: str = ""
    handoff_to_review: bool = False
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "automation_id": self.automation_id,
            "plan_ref": self.plan_ref,
            "blocked_reason": self.blocked_reason,
            "failure_code": self.failure_code,
            "handoff_to_review": self.handoff_to_review,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BlockedAutomationReviewItem":
        return cls(
            run_id=d.get("run_id", ""),
            automation_id=d.get("automation_id", ""),
            plan_ref=d.get("plan_ref", ""),
            blocked_reason=d.get("blocked_reason", ""),
            failure_code=d.get("failure_code", ""),
            handoff_to_review=bool(d.get("handoff_to_review", False)),
            created_at=d.get("created_at", ""),
        )


@dataclass
class BackgroundResultSummary:
    """Summary of one or more background run outcomes for digest/inbox."""
    run_ids: list[str] = field(default_factory=list)
    automation_id: str = ""
    plan_ref: str = ""
    completed_count: int = 0
    blocked_count: int = 0
    failed_count: int = 0
    suppressed_count: int = 0
    outcome_summaries: list[str] = field(default_factory=list)
    latest_timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_ids": list(self.run_ids),
            "automation_id": self.automation_id,
            "plan_ref": self.plan_ref,
            "completed_count": self.completed_count,
            "blocked_count": self.blocked_count,
            "failed_count": self.failed_count,
            "suppressed_count": self.suppressed_count,
            "outcome_summaries": list(self.outcome_summaries),
            "latest_timestamp": self.latest_timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BackgroundResultSummary":
        return cls(
            run_ids=list(d.get("run_ids", [])),
            automation_id=d.get("automation_id", ""),
            plan_ref=d.get("plan_ref", ""),
            completed_count=int(d.get("completed_count", 0)),
            blocked_count=int(d.get("blocked_count", 0)),
            failed_count=int(d.get("failed_count", 0)),
            suppressed_count=int(d.get("suppressed_count", 0)),
            outcome_summaries=list(d.get("outcome_summaries", [])),
            latest_timestamp=d.get("latest_timestamp", ""),
        )


@dataclass
class FailedSuppressedExplanation:
    """Explanation for a failed or suppressed automation (no hidden execution)."""
    run_id: str = ""
    automation_id: str = ""
    status: str = ""  # failed | suppressed
    reason: str = ""
    failure_code: str = ""
    policy_notes: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "automation_id": self.automation_id,
            "status": self.status,
            "reason": self.reason,
            "failure_code": self.failure_code,
            "policy_notes": list(self.policy_notes),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "FailedSuppressedExplanation":
        return cls(
            run_id=d.get("run_id", ""),
            automation_id=d.get("automation_id", ""),
            status=d.get("status", ""),
            reason=d.get("reason", ""),
            failure_code=d.get("failure_code", ""),
            policy_notes=list(d.get("policy_notes", [])),
            created_at=d.get("created_at", ""),
        )


@dataclass
class HumanFollowUpRecommendation:
    """Recommended human follow-up for automation (inspect, retry, escalate, approve)."""
    recommendation_id: str = ""
    run_id: str = ""
    automation_id: str = ""
    action: str = ""  # inspect | retry | escalate_to_planner | escalate_to_workspace | approve
    reason: str = ""
    link_commands: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "run_id": self.run_id,
            "automation_id": self.automation_id,
            "action": self.action,
            "reason": self.reason,
            "link_commands": list(self.link_commands),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "HumanFollowUpRecommendation":
        return cls(
            recommendation_id=d.get("recommendation_id", ""),
            run_id=d.get("run_id", ""),
            automation_id=d.get("automation_id", ""),
            action=d.get("action", ""),
            reason=d.get("reason", ""),
            link_commands=list(d.get("link_commands", [])),
            created_at=d.get("created_at", ""),
        )


# ----- M34L.1 Morning briefs + resume-work continuity cards -----

HANDOFF_WORKSPACE = "workspace"
HANDOFF_PROJECT = "project"
HANDOFF_ACTION = "action"


@dataclass
class HandoffTarget:
    """Direct handoff into workspace, project, or action (command)."""
    label: str = ""
    target_type: str = ""  # workspace | project | action
    view: str = ""
    command: str = ""
    ref: str = ""  # project_id, workspace_id, or action ref

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "target_type": self.target_type,
            "view": self.view,
            "command": self.command,
            "ref": self.ref,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "HandoffTarget":
        return cls(
            label=d.get("label", ""),
            target_type=d.get("target_type", ""),
            view=d.get("view", ""),
            command=d.get("command", ""),
            ref=d.get("ref", ""),
        )


@dataclass
class MorningBriefCard:
    """M34L.1: Morning brief card — what happened, top next action, handoff."""
    brief_id: str = ""
    generated_at: str = ""
    title: str = "Morning brief"
    what_happened_while_away: list[str] = field(default_factory=list)
    top_next_action: str = ""
    handoff: HandoffTarget | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "brief_id": self.brief_id,
            "generated_at": self.generated_at,
            "title": self.title,
            "what_happened_while_away": list(self.what_happened_while_away),
            "top_next_action": self.top_next_action,
            "handoff": self.handoff.to_dict() if self.handoff else {},
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MorningBriefCard":
        h = d.get("handoff")
        handoff = HandoffTarget.from_dict(h) if isinstance(h, dict) and h else None
        return cls(
            brief_id=d.get("brief_id", ""),
            generated_at=d.get("generated_at", ""),
            title=d.get("title", "Morning brief"),
            what_happened_while_away=list(d.get("what_happened_while_away", [])),
            top_next_action=d.get("top_next_action", ""),
            handoff=handoff,
            details=dict(d.get("details", {})),
        )


@dataclass
class ResumeWorkContinuityCard:
    """M34L.1: Resume-work continuity card — context, what happened, suggested next, handoff."""
    card_id: str = ""
    generated_at: str = ""
    title: str = "Resume work"
    resume_context: str = ""  # e.g. last project or workspace
    what_happened_while_away: list[str] = field(default_factory=list)
    suggested_next: str = ""
    handoff: HandoffTarget | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "generated_at": self.generated_at,
            "title": self.title,
            "resume_context": self.resume_context,
            "what_happened_while_away": list(self.what_happened_while_away),
            "suggested_next": self.suggested_next,
            "handoff": self.handoff.to_dict() if self.handoff else {},
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ResumeWorkContinuityCard":
        h = d.get("handoff")
        handoff = HandoffTarget.from_dict(h) if isinstance(h, dict) and h else None
        return cls(
            card_id=d.get("card_id", ""),
            generated_at=d.get("generated_at", ""),
            title=d.get("title", "Resume work"),
            resume_context=d.get("resume_context", ""),
            what_happened_while_away=list(d.get("what_happened_while_away", [])),
            suggested_next=d.get("suggested_next", ""),
            handoff=handoff,
            details=dict(d.get("details", {})),
        )
