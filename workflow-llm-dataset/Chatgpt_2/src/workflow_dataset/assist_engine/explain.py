"""
M32E–M32H: Explain a suggestion by id — reason, context, evidence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.assist_engine.store import load_suggestion


def explain_suggestion(
    suggestion_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Return full explanation for a suggestion: reason, triggering context, evidence,
    confidence, usefulness, required action. Empty dict if not found.
    """
    s = load_suggestion(suggestion_id, repo_root=repo_root)
    if not s:
        return {}
    out = {
        "suggestion_id": s.suggestion_id,
        "suggestion_type": s.suggestion_type,
        "title": s.title,
        "description": s.description,
        "reason": {
            "title": s.reason.title if s.reason else "",
            "description": s.reason.description if s.reason else "",
            "evidence": list(s.reason.evidence) if s.reason else [],
        },
        "triggering_context": {
            "source": s.triggering_context.source if s.triggering_context else "",
            "summary": s.triggering_context.summary if s.triggering_context else "",
            "signals": list(s.triggering_context.signals) if s.triggering_context else [],
            "project_id": s.triggering_context.project_id if s.triggering_context else "",
            "session_id": s.triggering_context.session_id if s.triggering_context else "",
        },
        "confidence": s.confidence,
        "usefulness_score": s.usefulness_score,
        "interruptiveness_score": s.interruptiveness_score,
        "affected_project_id": s.affected_project_id,
        "affected_session_id": s.affected_session_id,
        "required_operator_action": s.required_operator_action,
        "status": s.status,
        "supporting_signals": list(s.supporting_signals) if isinstance(s.supporting_signals, list) else [],
    }
    # M32H.1: Clear explanation when suggestion was held back
    if getattr(s, "held_back_reason", None) or s.status == "held_back":
        reason = getattr(s, "held_back_reason", "") or ""
        out["held_back"] = True
        out["held_back_explanation"] = (
            reason
            or "This suggestion was held back by policy (quiet hours, focus-safe, or interruptibility rules)."
        )
    else:
        out["held_back"] = False
        out["held_back_explanation"] = ""
    return out
