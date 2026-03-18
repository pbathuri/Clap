"""
Pydantic models for user-approved apply-to-project loop (M8).

Used by copy planner, executor, rollback store, and apply manifest store.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ApplyRequest(BaseModel):
    """A request to apply sandbox outputs to a target path."""

    apply_id: str = Field(..., description="Stable unique ID")
    session_id: str = Field(default="")
    workspace_id: str = Field(default="", description="Workspace or request_id from materialization")
    workspace_path: str = Field(default="", description="Absolute path to sandbox workspace")
    target_root: str = Field(default="", description="Absolute path to target directory")
    selected_paths: list[str] = Field(default_factory=list, description="Relative paths in workspace to apply; empty = all from manifest")
    apply_mode: str = Field(default="copy", description="copy only for v1")
    user_confirmed: bool = Field(default=False)
    created_utc: str = Field(default="")


class ApplyPlan(BaseModel):
    """Plan of copy operations before execution."""

    plan_id: str = Field(...)
    apply_id: str = Field(default="")
    source_paths: list[str] = Field(default_factory=list, description="Relative paths in workspace")
    target_paths: list[str] = Field(default_factory=list, description="Absolute or relative target paths")
    operations: list[dict[str, Any]] = Field(default_factory=list, description="List of {op: create|overwrite, source, target, backup_path?}")
    conflicts: list[dict[str, Any]] = Field(default_factory=list, description="Paths that would be overwritten")
    overwrite_candidates: list[str] = Field(default_factory=list)
    skipped_paths: list[str] = Field(default_factory=list)
    estimated_file_count: int = Field(default=0)
    created_utc: str = Field(default="")


class ApplyResult(BaseModel):
    """Result of an apply execution."""

    result_id: str = Field(...)
    apply_id: str = Field(default="")
    applied_paths: list[str] = Field(default_factory=list)
    skipped_paths: list[str] = Field(default_factory=list)
    overwritten_paths: list[str] = Field(default_factory=list)
    backup_paths: list[str] = Field(default_factory=list)
    rollback_token: str = Field(default="")
    errors: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")


class RollbackRecord(BaseModel):
    """Record for rollback: backups and affected paths."""

    rollback_token: str = Field(...)
    apply_id: str = Field(default="")
    backups: list[dict[str, str]] = Field(default_factory=list, description="[{original, backup}, ...]")
    affected_paths: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")
