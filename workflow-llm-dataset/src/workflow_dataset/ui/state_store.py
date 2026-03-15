"""
Local UI state for the operator console.

Keeps selected project, session, workspace, last viewed items,
pending apply plan, and chat context. In-memory; optional persistence later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.apply.apply_models import ApplyPlan


@dataclass
class ConsoleState:
    """In-memory state for the current console session."""

    config_path: str = "configs/settings.yaml"
    selected_session_id: str = ""
    selected_project_id: str = ""
    selected_workspace_path: str = ""
    selected_suggestion_id: str = ""
    selected_draft_type: str = ""
    last_suggestions_ids: list[str] = field(default_factory=list)
    last_drafts_types: list[str] = field(default_factory=list)
    pending_apply_plan: ApplyPlan | None = None
    pending_apply_workspace_path: str = ""
    pending_apply_target_path: str = ""
    pending_adoption_candidate: dict[str, Any] | None = None
    chat_messages: list[dict[str, str]] = field(default_factory=list)
    _raw_settings: Any = field(default=None, repr=False)

    def set_session(self, session_id: str) -> None:
        self.selected_session_id = session_id or ""

    def set_project(self, project_id: str) -> None:
        self.selected_project_id = project_id or ""

    def set_workspace(self, path: str | Path) -> None:
        self.selected_workspace_path = str(path) if path else ""

    def set_pending_apply(
        self,
        plan: ApplyPlan | None,
        workspace_path: str = "",
        target_path: str = "",
    ) -> None:
        self.pending_apply_plan = plan
        self.pending_apply_workspace_path = workspace_path or ""
        self.pending_apply_target_path = target_path or ""

    def clear_pending_apply(self) -> None:
        self.pending_apply_plan = None
        self.pending_apply_workspace_path = ""
        self.pending_apply_target_path = ""

    def set_pending_adoption_candidate(self, candidate: dict[str, Any] | None) -> None:
        self.pending_adoption_candidate = candidate

    def clear_pending_adoption_candidate(self) -> None:
        self.pending_adoption_candidate = None

    def add_chat_turn(self, role: str, content: str) -> None:
        self.chat_messages.append({"role": role, "content": content})
        # Keep last N to avoid unbounded growth
        if len(self.chat_messages) > 20:
            self.chat_messages = self.chat_messages[-20:]
