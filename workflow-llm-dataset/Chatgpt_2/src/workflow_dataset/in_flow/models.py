"""
M33I–M33L: In-flow review and composition models.

Draft artifact, handoff package, review checkpoint, staged summary/checklist/decision,
affected workflow step, review status, revision history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Draft artifact types (in-flow composition)
DRAFT_TYPE_UPDATE = "draft_update"
DRAFT_TYPE_MEETING_FOLLOW_UP = "meeting_follow_up"
DRAFT_TYPE_STATUS_SUMMARY = "status_summary"
DRAFT_TYPE_REVIEW_CHECKLIST = "review_checklist"
DRAFT_TYPE_APPROVAL_REQUEST_SUMMARY = "approval_request_summary"
DRAFT_TYPE_NEXT_STEP_HANDOFF_BRIEF = "next_step_handoff_brief"
DRAFT_TYPE_BLOCKED_ESCALATION_NOTE = "blocked_item_escalation_note"
DRAFT_TYPE_OTHER = "other"

DRAFT_TYPES = (
    DRAFT_TYPE_UPDATE,
    DRAFT_TYPE_MEETING_FOLLOW_UP,
    DRAFT_TYPE_STATUS_SUMMARY,
    DRAFT_TYPE_REVIEW_CHECKLIST,
    DRAFT_TYPE_APPROVAL_REQUEST_SUMMARY,
    DRAFT_TYPE_NEXT_STEP_HANDOFF_BRIEF,
    DRAFT_TYPE_BLOCKED_ESCALATION_NOTE,
    DRAFT_TYPE_OTHER,
)

# Review status for drafts and checkpoints
REVIEW_STATUS_DRAFT = "draft"
REVIEW_STATUS_WAITING_REVIEW = "waiting_review"
REVIEW_STATUS_REVISED = "revised"
REVIEW_STATUS_PROMOTED = "promoted"
REVIEW_STATUS_HANDED_OFF = "handed_off"
REVIEW_STATUS_DEFERRED = "deferred"

REVIEW_STATUSES = (
    REVIEW_STATUS_DRAFT,
    REVIEW_STATUS_WAITING_REVIEW,
    REVIEW_STATUS_REVISED,
    REVIEW_STATUS_PROMOTED,
    REVIEW_STATUS_HANDED_OFF,
    REVIEW_STATUS_DEFERRED,
)

# M33L.1: Readiness states for handoffs and drafts (ready to send / approve / continue)
READINESS_NONE = ""
READINESS_READY_TO_SEND = "ready_to_send"
READINESS_READY_TO_APPROVE = "ready_to_approve"
READINESS_READY_TO_CONTINUE = "ready_to_continue"

READINESS_STATES = (READINESS_NONE, READINESS_READY_TO_SEND, READINESS_READY_TO_APPROVE, READINESS_READY_TO_CONTINUE)


@dataclass
class AffectedWorkflowStep:
    """Reference to a workflow step this draft/checkpoint is tied to."""
    step_index: int = -1
    plan_id: str = ""
    plan_ref: str = ""
    step_label: str = ""
    run_id: str = ""
    episode_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "plan_id": self.plan_id,
            "plan_ref": self.plan_ref,
            "step_label": self.step_label,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AffectedWorkflowStep:
        return cls(
            step_index=int(d.get("step_index", -1)),
            plan_id=str(d.get("plan_id", "")),
            plan_ref=str(d.get("plan_ref", "")),
            step_label=str(d.get("step_label", "")),
            run_id=str(d.get("run_id", "")),
            episode_id=str(d.get("episode_id", "")),
        )


@dataclass
class RevisionEntry:
    """One revision in draft history."""
    revision_id: str = ""
    timestamp_utc: str = ""
    summary: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "timestamp_utc": self.timestamp_utc,
            "summary": self.summary,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RevisionEntry:
        return cls(
            revision_id=str(d.get("revision_id", "")),
            timestamp_utc=str(d.get("timestamp_utc", "")),
            summary=str(d.get("summary", "")),
            note=str(d.get("note", "")),
        )


@dataclass
class DraftArtifact:
    """In-flow draft artifact: created at a workflow moment, tied to episode/step/session."""
    draft_id: str = ""
    draft_type: str = ""
    title: str = ""
    content: str = ""  # Markdown or structured text
    project_id: str = ""
    session_id: str = ""
    affected_step: AffectedWorkflowStep | None = None
    episode_ref: str = ""
    artifact_refs: list[str] = field(default_factory=list)
    review_status: str = REVIEW_STATUS_DRAFT
    created_utc: str = ""
    updated_utc: str = ""
    revision_history: list[RevisionEntry] = field(default_factory=list)
    operator_notes: str = ""
    promoted_artifact_path: str = ""
    handed_off_to: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "draft_type": self.draft_type,
            "title": self.title,
            "content": self.content,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "affected_step": self.affected_step.to_dict() if self.affected_step else {},
            "episode_ref": self.episode_ref,
            "artifact_refs": list(self.artifact_refs),
            "review_status": self.review_status,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
            "revision_history": [r.to_dict() for r in self.revision_history],
            "operator_notes": self.operator_notes,
            "promoted_artifact_path": self.promoted_artifact_path,
            "handed_off_to": self.handed_off_to,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DraftArtifact:
        step = d.get("affected_step")
        if isinstance(step, dict) and step:
            step = AffectedWorkflowStep.from_dict(step)
        else:
            step = None
        revs = [RevisionEntry.from_dict(r) for r in d.get("revision_history", []) if isinstance(r, dict)]
        return cls(
            draft_id=str(d.get("draft_id", "")),
            draft_type=str(d.get("draft_type", "")),
            title=str(d.get("title", "")),
            content=str(d.get("content", "")),
            project_id=str(d.get("project_id", "")),
            session_id=str(d.get("session_id", "")),
            affected_step=step,
            episode_ref=str(d.get("episode_ref", "")),
            artifact_refs=list(d.get("artifact_refs", [])),
            review_status=str(d.get("review_status", REVIEW_STATUS_DRAFT)),
            created_utc=str(d.get("created_utc", "")),
            updated_utc=str(d.get("updated_utc", "")),
            revision_history=revs,
            operator_notes=str(d.get("operator_notes", "")),
            promoted_artifact_path=str(d.get("promoted_artifact_path", "")),
            handed_off_to=str(d.get("handed_off_to", "")),
        )


@dataclass
class StagedSummary:
    """Staged summary tied to workflow context."""
    summary_id: str = ""
    content: str = ""
    project_id: str = ""
    session_id: str = ""
    step_ref: str = ""
    episode_ref: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "content": self.content,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "step_ref": self.step_ref,
            "episode_ref": self.episode_ref,
            "created_utc": self.created_utc,
        }


@dataclass
class StagedChecklist:
    """Staged checklist (items + done state)."""
    checklist_id: str = ""
    title: str = ""
    items: list[str] = field(default_factory=list)
    done: list[bool] = field(default_factory=list)
    project_id: str = ""
    session_id: str = ""
    step_ref: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "checklist_id": self.checklist_id,
            "title": self.title,
            "items": list(self.items),
            "done": list(self.done),
            "project_id": self.project_id,
            "session_id": self.session_id,
            "step_ref": self.step_ref,
            "created_utc": self.created_utc,
        }


@dataclass
class StagedDecisionRequest:
    """Staged decision request for operator."""
    decision_id: str = ""
    question: str = ""
    options: list[str] = field(default_factory=list)
    context: str = ""
    project_id: str = ""
    step_ref: str = ""
    created_utc: str = ""
    decided: bool = False
    decision_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "question": self.question,
            "options": list(self.options),
            "context": self.context,
            "project_id": self.project_id,
            "step_ref": self.step_ref,
            "created_utc": self.created_utc,
            "decided": self.decided,
            "decision_note": self.decision_note,
        }


@dataclass
class ReviewCheckpoint:
    """Review checkpoint linked to a step or episode."""
    checkpoint_id: str = ""
    label: str = ""
    step_index: int = -1
    plan_id: str = ""
    episode_ref: str = ""
    draft_id: str = ""
    status: str = "pending"  # pending | reviewed | skipped
    created_utc: str = ""
    reviewed_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "label": self.label,
            "step_index": self.step_index,
            "plan_id": self.plan_id,
            "episode_ref": self.episode_ref,
            "draft_id": self.draft_id,
            "status": self.status,
            "created_utc": self.created_utc,
            "reviewed_utc": self.reviewed_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ReviewCheckpoint:
        return cls(
            checkpoint_id=str(d.get("checkpoint_id", "")),
            label=str(d.get("label", "")),
            step_index=int(d.get("step_index", -1)),
            plan_id=str(d.get("plan_id", "")),
            episode_ref=str(d.get("episode_ref", "")),
            draft_id=str(d.get("draft_id", "")),
            status=str(d.get("status", "pending")),
            created_utc=str(d.get("created_utc", "")),
            reviewed_utc=str(d.get("reviewed_utc", "")),
        )


@dataclass
class HandoffPackage:
    """Handoff package: from workflow/session, contents, target. M33L.1: readiness, nav_links."""
    handoff_id: str = ""
    from_workflow: str = ""  # run_id, episode_id, or "latest"
    from_session_id: str = ""
    from_project_id: str = ""
    title: str = ""
    summary: str = ""
    next_steps: list[str] = field(default_factory=list)
    draft_ids: list[str] = field(default_factory=list)
    target: str = ""  # approval_studio | planner | executor | workspace | artifact
    target_ref: str = ""
    created_utc: str = ""
    delivered_utc: str = ""
    # M33L.1: ready_to_send | ready_to_approve | ready_to_continue
    readiness: str = ""
    # Links into approvals, planner, executor, workspace (view, command, ref)
    nav_links: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "from_workflow": self.from_workflow,
            "from_session_id": self.from_session_id,
            "from_project_id": self.from_project_id,
            "title": self.title,
            "summary": self.summary,
            "next_steps": list(self.next_steps),
            "draft_ids": list(self.draft_ids),
            "target": self.target,
            "target_ref": self.target_ref,
            "created_utc": self.created_utc,
            "delivered_utc": self.delivered_utc,
            "readiness": self.readiness,
            "nav_links": list(self.nav_links),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> HandoffPackage:
        nav = d.get("nav_links")
        if not isinstance(nav, list):
            nav = []
        return cls(
            handoff_id=str(d.get("handoff_id", "")),
            from_workflow=str(d.get("from_workflow", "")),
            from_session_id=str(d.get("from_session_id", "")),
            from_project_id=str(d.get("from_project_id", "")),
            title=str(d.get("title", "")),
            summary=str(d.get("summary", "")),
            next_steps=list(d.get("next_steps", [])),
            draft_ids=list(d.get("draft_ids", [])),
            target=str(d.get("target", "")),
            target_ref=str(d.get("target_ref", "")),
            created_utc=str(d.get("created_utc", "")),
            delivered_utc=str(d.get("delivered_utc", "")),
            readiness=str(d.get("readiness", "")),
            nav_links=[x if isinstance(x, dict) else {} for x in nav],
        )


@dataclass
class ReviewBundle:
    """M33L.1: Reusable review bundle — checklist items, summary template, decision points, draft types."""
    bundle_id: str = ""
    name: str = ""
    description: str = ""
    checklist_items: list[str] = field(default_factory=list)
    summary_template: str = ""
    decision_questions: list[str] = field(default_factory=list)
    draft_types: list[str] = field(default_factory=list)  # which draft types to create

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "name": self.name,
            "description": self.description,
            "checklist_items": list(self.checklist_items),
            "summary_template": self.summary_template,
            "decision_questions": list(self.decision_questions),
            "draft_types": list(self.draft_types),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ReviewBundle:
        return cls(
            bundle_id=str(d.get("bundle_id", "")),
            name=str(d.get("name", "")),
            description=str(d.get("description", "")),
            checklist_items=list(d.get("checklist_items", [])),
            summary_template=str(d.get("summary_template", "")),
            decision_questions=list(d.get("decision_questions", [])),
            draft_types=list(d.get("draft_types", [])),
        )


@dataclass
class HandoffKit:
    """M33L.1: Handoff kit for common workflow types — title template, default target, nav links."""
    kit_id: str = ""
    name: str = ""
    workflow_type: str = ""  # end_of_session | blocked_escalation | approval_request | next_phase | other
    title_template: str = ""
    default_target: str = ""
    default_next_steps: list[str] = field(default_factory=list)
    nav_links: list[dict[str, str]] = field(default_factory=list)  # [{view, command, label, ref}]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kit_id": self.kit_id,
            "name": self.name,
            "workflow_type": self.workflow_type,
            "title_template": self.title_template,
            "default_target": self.default_target,
            "default_next_steps": list(self.default_next_steps),
            "nav_links": list(self.nav_links),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> HandoffKit:
        nav = d.get("nav_links")
        if not isinstance(nav, list):
            nav = []
        return cls(
            kit_id=str(d.get("kit_id", "")),
            name=str(d.get("name", "")),
            workflow_type=str(d.get("workflow_type", "")),
            title_template=str(d.get("title_template", "")),
            default_target=str(d.get("default_target", "artifact")),
            default_next_steps=list(d.get("default_next_steps", [])),
            nav_links=[x if isinstance(x, dict) else {} for x in nav],
        )
