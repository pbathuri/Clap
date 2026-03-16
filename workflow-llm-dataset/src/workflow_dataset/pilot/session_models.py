"""
M21: Pilot session and feedback models. Local-only; inspectable persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PilotSessionRecord:
    """One pilot session: context, commands, issues, disposition."""

    session_id: str = ""
    timestamp_start: str = ""
    timestamp_end: str = ""
    operator: str = ""
    pilot_scope: str = "ops"
    task_type: str = ""
    config_path: str = ""
    release_config_path: str = ""
    adapter_mode: str = "adapter"
    degraded_mode: bool = False
    commands_run: list[str] = field(default_factory=list)
    artifacts_produced: list[str] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    operator_notes: str = ""
    user_feedback_summary: str = ""
    disposition: str = ""  # continue | fix | pause
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "operator": self.operator,
            "pilot_scope": self.pilot_scope,
            "task_type": self.task_type,
            "config_path": self.config_path,
            "release_config_path": self.release_config_path,
            "adapter_mode": self.adapter_mode,
            "degraded_mode": self.degraded_mode,
            "commands_run": self.commands_run,
            "artifacts_produced": self.artifacts_produced,
            "blocking_issues": self.blocking_issues,
            "warnings": self.warnings,
            "operator_notes": self.operator_notes,
            "user_feedback_summary": self.user_feedback_summary,
            "disposition": self.disposition,
            **self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PilotSessionRecord":
        extra = {k: v for k, v in data.items() if k not in {
            "session_id", "timestamp_start", "timestamp_end", "operator", "pilot_scope", "task_type",
            "config_path", "release_config_path", "adapter_mode", "degraded_mode", "commands_run",
            "artifacts_produced", "blocking_issues", "warnings", "operator_notes", "user_feedback_summary", "disposition",
        }}
        return cls(
            session_id=data.get("session_id", ""),
            timestamp_start=data.get("timestamp_start", ""),
            timestamp_end=data.get("timestamp_end", ""),
            operator=data.get("operator", ""),
            pilot_scope=data.get("pilot_scope", "ops"),
            task_type=data.get("task_type", ""),
            config_path=data.get("config_path", ""),
            release_config_path=data.get("release_config_path", ""),
            adapter_mode=data.get("adapter_mode", "adapter"),
            degraded_mode=data.get("degraded_mode", False),
            commands_run=data.get("commands_run", []),
            artifacts_produced=data.get("artifacts_produced", []),
            blocking_issues=data.get("blocking_issues", []),
            warnings=data.get("warnings", []),
            operator_notes=data.get("operator_notes", ""),
            user_feedback_summary=data.get("user_feedback_summary", ""),
            disposition=data.get("disposition", ""),
            extra=extra,
        )


@dataclass
class PilotFeedbackRecord:
    """Structured feedback for one pilot session."""

    session_id: str = ""
    timestamp: str = ""
    usefulness_score: int = 0  # 1-5
    trust_score: int = 0  # 1-5
    clarity_score: int = 0  # 1-5
    adoption_likelihood: int = 0  # 1-5 "would use again"
    blocker_encountered: bool = False
    top_failure_reason: str = ""
    operator_friction_notes: str = ""
    user_quote: str = ""
    freeform_notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "usefulness_score": self.usefulness_score,
            "trust_score": self.trust_score,
            "clarity_score": self.clarity_score,
            "adoption_likelihood": self.adoption_likelihood,
            "blocker_encountered": self.blocker_encountered,
            "top_failure_reason": self.top_failure_reason,
            "operator_friction_notes": self.operator_friction_notes,
            "user_quote": self.user_quote,
            "freeform_notes": self.freeform_notes,
            **self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PilotFeedbackRecord":
        extra = {k: v for k, v in data.items() if k not in {
            "session_id", "timestamp", "usefulness_score", "trust_score", "clarity_score",
            "adoption_likelihood", "blocker_encountered", "top_failure_reason", "operator_friction_notes",
            "user_quote", "freeform_notes",
        }}
        return cls(
            session_id=data.get("session_id", ""),
            timestamp=data.get("timestamp", ""),
            usefulness_score=int(data.get("usefulness_score", 0) or 0),
            trust_score=int(data.get("trust_score", 0) or 0),
            clarity_score=int(data.get("clarity_score", 0) or 0),
            adoption_likelihood=int(data.get("adoption_likelihood", 0) or 0),
            blocker_encountered=bool(data.get("blocker_encountered", False)),
            top_failure_reason=data.get("top_failure_reason", ""),
            operator_friction_notes=data.get("operator_friction_notes", ""),
            user_quote=data.get("user_quote", ""),
            freeform_notes=data.get("freeform_notes", ""),
            extra=extra,
        )
