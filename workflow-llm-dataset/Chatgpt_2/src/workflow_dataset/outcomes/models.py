"""
M24N–M24Q: Outcome capture models — session outcome, task outcome, artifact outcome,
blocked cause, operator-confirmed usefulness, incomplete work, follow-up recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Blocked cause taxonomy for pattern detection
BLOCKED_CAUSES = (
    "approval_missing",
    "job_not_found",
    "routine_not_found",
    "macro_not_found",
    "path_scope_denied",
    "timeout",
    "user_abandoned",
    "policy_denied",
    "runtime_unavailable",
    "other",
)

OUTCOME_KINDS = ("success", "partial", "failed", "blocked", "skipped", "abandoned")


@dataclass
class BlockedCause:
    """Structured blocked cause for an outcome."""
    cause_code: str  # one of BLOCKED_CAUSES
    detail: str = ""
    source_ref: str = ""  # job_id, routine_id, macro_id, or ""


@dataclass
class UsefulnessConfirmation:
    """Operator- or user-confirmed usefulness for a run/artifact."""
    source_type: str = ""  # job_run, routine_run, macro_run, artifact
    source_ref: str = ""
    usefulness_score: int = 0  # 0-5, 0 = not set
    operator_confirmed: bool = False
    note: str = ""


@dataclass
class IncompleteWork:
    """Record of work that was incomplete or abandoned in a session."""
    description: str = ""
    reason: str = ""  # abandoned, blocked, deferred
    source_ref: str = ""
    suggested_follow_up: str = ""


@dataclass
class FollowUpRecommendation:
    """Recommendation for next run or pack refinement."""
    kind: str = ""  # next_run, pack_refinement, correction_suggested, trust_review
    title: str = ""
    detail: str = ""
    ref: str = ""  # job_id, pack_id, correction_id, etc.
    priority: str = "medium"  # low, medium, high


@dataclass
class TaskOutcome:
    """Outcome of a single task (job run, routine run, macro run) within a session."""
    task_id: str = ""
    session_id: str = ""
    source_type: str = ""  # job_run, routine_run, macro_run
    source_ref: str = ""  # job_pack_id, routine_id, macro_id
    outcome_kind: str = ""  # success, partial, failed, blocked, skipped, abandoned
    blocked_cause: BlockedCause | None = None
    usefulness: UsefulnessConfirmation | None = None
    timestamp: str = ""
    params_used: dict[str, Any] = field(default_factory=dict)
    notes: str = ""


@dataclass
class ArtifactOutcome:
    """Outcome related to an artifact produced or consumed in a session."""
    artifact_id: str = ""
    session_id: str = ""
    artifact_type: str = ""  # output_file, staging_output, report, etc.
    path_or_ref: str = ""
    outcome_kind: str = ""  # created, reused, failed, skipped
    usefulness: UsefulnessConfirmation | None = None
    timestamp: str = ""


@dataclass
class SessionOutcome:
    """Aggregate outcome for one session: summary, task outcomes, artifacts, blocked, useful, incomplete, follow-ups."""
    session_id: str = ""
    timestamp_start: str = ""
    timestamp_end: str = ""
    pack_id: str = ""  # value_pack_id or ""
    disposition: str = ""  # continue, fix, pause, complete
    task_outcomes: list[TaskOutcome] = field(default_factory=list)
    artifact_outcomes: list[ArtifactOutcome] = field(default_factory=list)
    blocked_causes: list[BlockedCause] = field(default_factory=list)
    usefulness_confirmations: list[UsefulnessConfirmation] = field(default_factory=list)
    incomplete_work: list[IncompleteWork] = field(default_factory=list)
    follow_up_recommendations: list[FollowUpRecommendation] = field(default_factory=list)
    summary_text: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "pack_id": self.pack_id,
            "disposition": self.disposition,
            "task_outcomes": [_task_to_dict(t) for t in self.task_outcomes],
            "artifact_outcomes": [_artifact_to_dict(a) for a in self.artifact_outcomes],
            "blocked_causes": [{"cause_code": b.cause_code, "detail": b.detail, "source_ref": b.source_ref} for b in self.blocked_causes],
            "usefulness_confirmations": [_useful_to_dict(u) for u in self.usefulness_confirmations],
            "incomplete_work": [{"description": i.description, "reason": i.reason, "source_ref": i.source_ref, "suggested_follow_up": i.suggested_follow_up} for i in self.incomplete_work],
            "follow_up_recommendations": [{"kind": f.kind, "title": f.title, "detail": f.detail, "ref": f.ref, "priority": f.priority} for f in self.follow_up_recommendations],
            "summary_text": self.summary_text,
            **self.extra,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SessionOutcome":
        extra = {k: v for k, v in d.items() if k not in {
            "session_id", "timestamp_start", "timestamp_end", "pack_id", "disposition",
            "task_outcomes", "artifact_outcomes", "blocked_causes", "usefulness_confirmations",
            "incomplete_work", "follow_up_recommendations", "summary_text",
        }}
        return cls(
            session_id=d.get("session_id", ""),
            timestamp_start=d.get("timestamp_start", ""),
            timestamp_end=d.get("timestamp_end", ""),
            pack_id=d.get("pack_id", ""),
            disposition=d.get("disposition", ""),
            task_outcomes=[_dict_to_task(t) for t in d.get("task_outcomes", [])],
            artifact_outcomes=[_dict_to_artifact(a) for a in d.get("artifact_outcomes", [])],
            blocked_causes=[BlockedCause(cause_code=b.get("cause_code", ""), detail=b.get("detail", ""), source_ref=b.get("source_ref", "")) for b in d.get("blocked_causes", [])],
            usefulness_confirmations=[_dict_to_useful(u) for u in d.get("usefulness_confirmations", [])],
            incomplete_work=[IncompleteWork(description=i.get("description", ""), reason=i.get("reason", ""), source_ref=i.get("source_ref", ""), suggested_follow_up=i.get("suggested_follow_up", "")) for i in d.get("incomplete_work", [])],
            follow_up_recommendations=[FollowUpRecommendation(kind=f.get("kind", ""), title=f.get("title", ""), detail=f.get("detail", ""), ref=f.get("ref", ""), priority=f.get("priority", "medium")) for f in d.get("follow_up_recommendations", [])],
            summary_text=d.get("summary_text", ""),
            extra=extra,
        )


def _task_to_dict(t: TaskOutcome) -> dict[str, Any]:
    return {
        "task_id": t.task_id,
        "session_id": t.session_id,
        "source_type": t.source_type,
        "source_ref": t.source_ref,
        "outcome_kind": t.outcome_kind,
        "blocked_cause": {"cause_code": t.blocked_cause.cause_code, "detail": t.blocked_cause.detail, "source_ref": t.blocked_cause.source_ref} if t.blocked_cause else None,
        "usefulness": _useful_to_dict(t.usefulness) if t.usefulness else None,
        "timestamp": t.timestamp,
        "params_used": t.params_used,
        "notes": t.notes,
    }


def _dict_to_task(d: dict[str, Any]) -> TaskOutcome:
    bc = d.get("blocked_cause")
    return TaskOutcome(
        task_id=d.get("task_id", ""),
        session_id=d.get("session_id", ""),
        source_type=d.get("source_type", ""),
        source_ref=d.get("source_ref", ""),
        outcome_kind=d.get("outcome_kind", ""),
        blocked_cause=BlockedCause(cause_code=bc["cause_code"], detail=bc.get("detail", ""), source_ref=bc.get("source_ref", "")) if bc else None,
        usefulness=_dict_to_useful(d["usefulness"]) if d.get("usefulness") else None,
        timestamp=d.get("timestamp", ""),
        params_used=d.get("params_used", {}),
        notes=d.get("notes", ""),
    )


def _artifact_to_dict(a: ArtifactOutcome) -> dict[str, Any]:
    return {
        "artifact_id": a.artifact_id,
        "session_id": a.session_id,
        "artifact_type": a.artifact_type,
        "path_or_ref": a.path_or_ref,
        "outcome_kind": a.outcome_kind,
        "usefulness": _useful_to_dict(a.usefulness) if a.usefulness else None,
        "timestamp": a.timestamp,
    }


def _dict_to_artifact(d: dict[str, Any]) -> ArtifactOutcome:
    return ArtifactOutcome(
        artifact_id=d.get("artifact_id", ""),
        session_id=d.get("session_id", ""),
        artifact_type=d.get("artifact_type", ""),
        path_or_ref=d.get("path_or_ref", ""),
        outcome_kind=d.get("outcome_kind", ""),
        usefulness=_dict_to_useful(d["usefulness"]) if d.get("usefulness") else None,
        timestamp=d.get("timestamp", ""),
    )


def _useful_to_dict(u: UsefulnessConfirmation) -> dict[str, Any]:
    return {
        "source_type": u.source_type,
        "source_ref": u.source_ref,
        "usefulness_score": u.usefulness_score,
        "operator_confirmed": u.operator_confirmed,
        "note": u.note,
    }


def _dict_to_useful(d: dict[str, Any]) -> UsefulnessConfirmation:
    return UsefulnessConfirmation(
        source_type=d.get("source_type", ""),
        source_ref=d.get("source_ref", ""),
        usefulness_score=int(d.get("usefulness_score", 0) or 0),
        operator_confirmed=bool(d.get("operator_confirmed", False)),
        note=d.get("note", ""),
    )
