"""
Agent action audit log: proposed, approved, executed, failed.

Device-local only; see docs/schemas/AGENT_ACTION_LOG.md.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from pathlib import Path
import json


class ActionLogRecord(BaseModel):
    """Single audit log entry."""

    log_id: str
    timestamp_utc: str = Field(..., description="ISO 8601")
    mode: str = Field(..., description="observe | simulate | assist | automate")
    action_type: str = Field(..., description="e.g. file_write, api_call, suggestion_only")
    intent: str = Field(default="", description="Human-readable intent")
    target: str | dict[str, Any] = Field(default="")
    outcome: str = Field(
        ...,
        description="proposed | approved | rejected | executed | failed | skipped",
    )
    rollback_feasible: bool | None = None
    rollback_method: str | None = None
    rollback_token: str | None = None
    rollback_limitations: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    approval_id: str | None = None
    user_override: str | None = None


def append_log(
    log_store: Any,
    record: ActionLogRecord,
) -> None:
    """Append one record to the audit log (JSONL)."""
    path = _resolve_log_path(log_store)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(record.model_dump_json())
        f.write("\n")


def query_log(
    log_store: Any,
    since_utc: str | None = None,
    mode: str | None = None,
    outcome: str | None = None,
    limit: int = 1000,
) -> list[ActionLogRecord]:
    """Query audit log (JSONL)."""
    path = _resolve_log_path(log_store)
    if not path.exists():
        return []
    out: list[ActionLogRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            data = json.loads(line)
            rec = ActionLogRecord.model_validate(data)
            if since_utc and rec.timestamp_utc < since_utc:
                continue
            if mode and rec.mode != mode:
                continue
            if outcome and rec.outcome != outcome:
                continue
            out.append(rec)
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def _resolve_log_path(log_store: Any) -> Path:
    if isinstance(log_store, Path):
        base = log_store
    elif isinstance(log_store, str):
        base = Path(log_store)
    else:
        try:
            from workflow_dataset.path_utils import get_repo_root
            base = Path(get_repo_root())
        except Exception:
            base = Path.cwd()
    if base.is_dir():
        return base / "data/local/agent/action_log.jsonl"
    return base
