"""
M24J–M24M: Live workspace session model — pack-linked, operator/end-user session with tasks, artifacts, state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SESSION_STATES = ("open", "closed", "archived")


@dataclass
class Session:
    """
    A live workspace session tied to a provisioned value pack.
    Tracks active work context, tasks, jobs/routines/macros, artifacts, notes, and recommended next actions.
    """
    session_id: str
    value_pack_id: str = ""
    starter_kit_id: str = ""
    profile_ref: str = ""  # e.g. field, job_family from onboarding
    # Active work
    active_tasks: list[str] = field(default_factory=list)  # human-readable or task ids
    active_job_ids: list[str] = field(default_factory=list)
    active_routine_ids: list[str] = field(default_factory=list)
    active_macro_ids: list[str] = field(default_factory=list)
    current_artifacts: list[str] = field(default_factory=list)  # paths or labels
    notes: list[str] = field(default_factory=list)
    state: str = "open"  # open | closed | archived
    created_at: str = ""
    updated_at: str = ""
    closed_at: str = ""
    # Optional context snapshots (read-only for display)
    trust_context: dict[str, Any] = field(default_factory=dict)
    capability_context: dict[str, Any] = field(default_factory=dict)
    recommended_next_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "value_pack_id": self.value_pack_id,
            "starter_kit_id": self.starter_kit_id,
            "profile_ref": self.profile_ref,
            "active_tasks": list(self.active_tasks),
            "active_job_ids": list(self.active_job_ids),
            "active_routine_ids": list(self.active_routine_ids),
            "active_macro_ids": list(self.active_macro_ids),
            "current_artifacts": list(self.current_artifacts),
            "notes": list(self.notes),
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
            "trust_context": dict(self.trust_context),
            "capability_context": dict(self.capability_context),
            "recommended_next_actions": list(self.recommended_next_actions),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Session:
        return cls(
            session_id=d.get("session_id", ""),
            value_pack_id=d.get("value_pack_id", ""),
            starter_kit_id=d.get("starter_kit_id", ""),
            profile_ref=d.get("profile_ref", ""),
            active_tasks=list(d.get("active_tasks", [])),
            active_job_ids=list(d.get("active_job_ids", [])),
            active_routine_ids=list(d.get("active_routine_ids", [])),
            active_macro_ids=list(d.get("active_macro_ids", [])),
            current_artifacts=list(d.get("current_artifacts", [])),
            notes=list(d.get("notes", [])),
            state=d.get("state", "open"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            closed_at=d.get("closed_at", ""),
            trust_context=dict(d.get("trust_context", {})),
            capability_context=dict(d.get("capability_context", {})),
            recommended_next_actions=list(d.get("recommended_next_actions", [])),
        )
