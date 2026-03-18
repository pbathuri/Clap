"""
M32I–M32L: Action card model — card, preview, handoff target, trust requirement, card state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CardState(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    EXECUTED = "executed"
    BLOCKED = "blocked"


class HandoffTarget(str, Enum):
    """Where the card hands off when executed."""
    OPEN_VIEW = "open_view"           # Open a target view (e.g. review studio, workspace)
    PREFILL_COMMAND = "prefill_command"  # Prefill a command or planner goal
    QUEUE_SIMULATED = "queue_simulated"   # Queue a safe simulated run (supervised_loop)
    APPROVAL_STUDIO = "approval_studio"   # Move to approval queue / review surface
    CREATE_DRAFT = "create_draft"     # Create draft artifact in sandbox (materialize)
    COMPILE_PLAN = "compile_plan"     # Compile a plan for a task (planner)
    EXECUTOR_RUN = "executor_run"     # Queue executor run (still via approval if gated)


class TrustRequirement(str, Enum):
    NONE = "none"
    SIMULATE_ONLY = "simulate_only"
    APPROVAL_REQUIRED = "approval_required"
    TRUSTED_PATH = "trusted_path"


@dataclass
class ActionCard:
    """One guided action card: source suggestion, preview, handoff target, state."""
    card_id: str = ""
    title: str = ""
    description: str = ""
    source_type: str = ""       # personal_suggestion | graph_routine | style_suggestion | copilot
    source_ref: str = ""        # suggestion_id, routine_id, etc.
    handoff_target: HandoffTarget = HandoffTarget.PREFILL_COMMAND
    handoff_params: dict[str, Any] = field(default_factory=dict)  # command, plan_ref, view_id, suggestion_id, goal, etc.
    trust_requirement: TrustRequirement = TrustRequirement.NONE
    reversible: bool = True     # Operator can undo/dismiss
    expected_artifact: str = "" # Optional: path or label of expected output
    state: CardState = CardState.PENDING
    created_utc: str = ""
    updated_utc: str = ""
    executed_at: str = ""
    outcome_summary: str = ""
    blocked_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "title": self.title,
            "description": self.description,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "handoff_target": self.handoff_target.value,
            "handoff_params": dict(self.handoff_params),
            "trust_requirement": self.trust_requirement.value,
            "reversible": self.reversible,
            "expected_artifact": self.expected_artifact,
            "state": self.state.value,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
            "executed_at": self.executed_at,
            "outcome_summary": self.outcome_summary,
            "blocked_reason": self.blocked_reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ActionCard:
        return cls(
            card_id=d.get("card_id", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            source_type=d.get("source_type", ""),
            source_ref=d.get("source_ref", ""),
            handoff_target=HandoffTarget(d.get("handoff_target", HandoffTarget.PREFILL_COMMAND.value)),
            handoff_params=dict(d.get("handoff_params", {})),
            trust_requirement=TrustRequirement(d.get("trust_requirement", TrustRequirement.NONE.value)),
            reversible=bool(d.get("reversible", True)),
            expected_artifact=d.get("expected_artifact", ""),
            state=CardState(d.get("state", CardState.PENDING.value)),
            created_utc=d.get("created_utc", ""),
            updated_utc=d.get("updated_utc", ""),
            executed_at=d.get("executed_at", ""),
            outcome_summary=d.get("outcome_summary", ""),
            blocked_reason=d.get("blocked_reason", ""),
        )


@dataclass
class ActionPreview:
    """Preview of what executing the card would do."""
    card_id: str = ""
    summary: str = ""
    what_would_happen: str = ""
    trust_note: str = ""
    command_hint: str = ""      # Suggested CLI command if applicable
    approval_required: bool = False
    simulate_first: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "summary": self.summary,
            "what_would_happen": self.what_would_happen,
            "trust_note": self.trust_note,
            "command_hint": self.command_hint,
            "approval_required": self.approval_required,
            "simulate_first": self.simulate_first,
        }


# ----- M32L.1 Micro-assistance bundles + fast review paths -----

class UserMoment(str, Enum):
    """Common user moments for grouped card flows."""
    RESUME_WORK = "resume_work"
    BLOCKED_REVIEW = "blocked_review"
    END_OF_DAY_WRAP = "end_of_day_wrap"
    DOCUMENT_HANDOFF = "document_handoff"


@dataclass
class MicroAssistanceBundle:
    """Reusable micro-assistance bundle: named group of action cards for a user moment."""
    bundle_id: str = ""
    name: str = ""
    description: str = ""
    moment_kind: str = ""   # UserMoment value
    card_ids: list[str] = field(default_factory=list)
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "name": self.name,
            "description": self.description,
            "moment_kind": self.moment_kind,
            "card_ids": list(self.card_ids),
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MicroAssistanceBundle:
        return cls(
            bundle_id=d.get("bundle_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            moment_kind=d.get("moment_kind", ""),
            card_ids=list(d.get("card_ids", [])),
            created_utc=d.get("created_utc", ""),
            updated_utc=d.get("updated_utc", ""),
        )


@dataclass
class FastReviewPath:
    """Fast review path: filter + sort + action for common accepted cards."""
    path_id: str = ""
    name: str = ""
    description: str = ""
    moment_kind: str = ""   # UserMoment value
    filter_state: str = ""  # pending | accepted | executed | blocked | "" (any)
    filter_handoff_target: str = ""  # optional, e.g. queue_simulated
    filter_source_type: str = ""  # optional, e.g. copilot
    sort_by: str = "updated_utc"  # created_utc | updated_utc | title
    sort_order: str = "desc"  # asc | desc
    action: str = "list_only"  # list_only | preview_first | execute_in_order | open_studio
    limit: int = 10
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "name": self.name,
            "description": self.description,
            "moment_kind": self.moment_kind,
            "filter_state": self.filter_state,
            "filter_handoff_target": self.filter_handoff_target,
            "filter_source_type": self.filter_source_type,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "action": self.action,
            "limit": self.limit,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FastReviewPath:
        return cls(
            path_id=d.get("path_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            moment_kind=d.get("moment_kind", ""),
            filter_state=d.get("filter_state", ""),
            filter_handoff_target=d.get("filter_handoff_target", ""),
            filter_source_type=d.get("filter_source_type", ""),
            sort_by=d.get("sort_by", "updated_utc"),
            sort_order=d.get("sort_order", "desc"),
            action=d.get("action", "list_only"),
            limit=int(d.get("limit", 10)),
            created_utc=d.get("created_utc", ""),
            updated_utc=d.get("updated_utc", ""),
        )


@dataclass
class GroupedCardFlow:
    """Grouped card flow: links a user moment to a bundle and/or fast review path."""
    flow_id: str = ""
    moment_kind: str = ""
    label: str = ""
    bundle_id: str = ""
    review_path_id: str = ""
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "moment_kind": self.moment_kind,
            "label": self.label,
            "bundle_id": self.bundle_id,
            "review_path_id": self.review_path_id,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GroupedCardFlow:
        return cls(
            flow_id=d.get("flow_id", ""),
            moment_kind=d.get("moment_kind", ""),
            label=d.get("label", ""),
            bundle_id=d.get("bundle_id", ""),
            review_path_id=d.get("review_path_id", ""),
            created_utc=d.get("created_utc", ""),
            updated_utc=d.get("updated_utc", ""),
        )
