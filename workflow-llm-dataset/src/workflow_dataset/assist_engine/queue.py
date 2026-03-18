"""
M32E–M32H: Reviewable suggestion queue — sort, suppress repetitive, snooze/dismiss/accept.
M32H.1: Apply quiet hours, focus-safe, interruptibility policy; hold back with clear reason.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.assist_engine.models import AssistSuggestion
from workflow_dataset.assist_engine.store import (
    list_suggestions,
    list_dismissed_patterns,
    save_suggestion,
    update_status,
)
from workflow_dataset.assist_engine.generation import generate_assist_suggestions
from workflow_dataset.assist_engine.policy import apply_policy
from workflow_dataset.utils.dates import utc_now_iso


def _suppress_repetitive(
    suggestions: list[AssistSuggestion],
    repo_root: Path | str | None = None,
    window_hours: int = 24,
) -> list[AssistSuggestion]:
    """Drop suggestions that match a recently dismissed pattern (same type + reason title)."""
    dismissed = list_dismissed_patterns(repo_root=repo_root, limit=100)
    try:
        cutoff = datetime.now(timezone.utc)
        from datetime import timedelta
        cutoff = cutoff - timedelta(hours=window_hours)
        cutoff_iso = cutoff.isoformat()
        recent = [d for d in dismissed if (d.get("dismissed_utc") or "") >= cutoff_iso]
    except Exception:
        recent = dismissed[:20]
    keys = {(d.get("suggestion_type", ""), (d.get("reason_title") or "")[:60]) for d in recent}
    out = []
    for s in suggestions:
        reason_title = (s.reason.title if s.reason else "")[:60]
        if (s.suggestion_type, reason_title) in keys:
            continue
        out.append(s)
    return out


def _is_snoozed(s: AssistSuggestion) -> bool:
    if s.status != "snoozed":
        return False
    until = s.snoozed_until_utc or ""
    if not until:
        return True  # Snoozed indefinitely until next context change
    try:
        dt = datetime.fromisoformat(until.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp() > datetime.now(timezone.utc).timestamp()
    except Exception:
        return False


def _get_policy_context(repo_root: Path | str | None) -> tuple[str, str, str, bool]:
    """Resolve work_mode, project_id, trust_level, focus_safe_active for policy. M32H.1."""
    work_mode = ""
    project_id = ""
    trust_level = ""
    focus_safe_active = False
    try:
        from workflow_dataset.live_context.state import get_live_context_state
        root = Path(repo_root).resolve() if repo_root else Path.cwd()
        state = get_live_context_state(root / "data/local")
        if state:
            w = getattr(state, "work_mode", None)
            work_mode = (w.value if w is not None and hasattr(w, "value") else str(w or "")).lower()
            proj = getattr(state, "inferred_project", None)
            if proj is not None:
                project_id = getattr(proj, "project_id", "") or getattr(proj, "label", "") or ""
    except Exception:
        pass
    return work_mode, project_id, trust_level, focus_safe_active


def run_now(
    repo_root: Path | str | None = None,
    max_new: int = 15,
    merge_with_existing_pending: bool = True,
    work_mode: str = "",
    project_id: str = "",
    trust_level: str = "",
    focus_safe_active: bool = False,
) -> list[AssistSuggestion]:
    """
    Generate new suggestions, apply policy (quiet hours, focus-safe, interruptibility),
    suppress repetitive, merge with existing pending, return visible queue (pending, not snoozed).
    Held-back suggestions are saved with status=held_back and held_back_reason for explain.
    """
    # Resolve policy context if not provided
    if not work_mode and not project_id:
        work_mode, project_id, trust_level, focus_safe_active = _get_policy_context(repo_root)

    # Existing pending (and not snoozed past)
    existing = list_suggestions(repo_root=repo_root, status_filter="pending", limit=50)
    existing = [e for e in existing if not _is_snoozed(e)]

    # New candidates
    new = generate_assist_suggestions(repo_root=repo_root, max_total=max_new)
    new = _suppress_repetitive(new, repo_root=repo_root)

    seen_ids = {e.suggestion_id for e in existing}
    for s in new:
        if s.suggestion_id in seen_ids:
            continue
        allow, hold_back_reason = apply_policy(
            s,
            repo_root=repo_root,
            work_mode=work_mode,
            project_id=project_id,
            trust_level=trust_level,
            focus_safe_active=focus_safe_active,
        )
        if not allow:
            s.status = "held_back"
            s.held_back_reason = hold_back_reason
            s.updated_utc = utc_now_iso()
            save_suggestion(s, repo_root=repo_root)
            continue
        existing.append(s)
        seen_ids.add(s.suggestion_id)
        save_suggestion(s, repo_root=repo_root)

    # Sort: usefulness (desc), then confidence (desc), then interruptiveness (asc)
    existing.sort(
        key=lambda x: (
            -x.usefulness_score,
            -x.confidence,
            x.interruptiveness_score,
        ),
    )
    return existing[:50]


def get_queue(
    repo_root: Path | str | None = None,
    status_filter: str | None = "pending",
    limit: int = 30,
    include_snoozed: bool = False,
) -> list[AssistSuggestion]:
    """Return queue sorted by usefulness/confidence; optionally filter by status."""
    items = list_suggestions(repo_root=repo_root, status_filter=status_filter, limit=limit * 2)
    if status_filter == "pending" and not include_snoozed:
        items = [i for i in items if not _is_snoozed(i)]
    items.sort(key=lambda x: (-x.usefulness_score, -x.confidence, x.interruptiveness_score))
    return items[:limit]


def accept_suggestion(suggestion_id: str, repo_root: Path | str | None = None) -> bool:
    """Mark suggestion as accepted (record only; no auto-execute)."""
    return update_status(suggestion_id, "accepted", repo_root=repo_root)


def dismiss_suggestion(suggestion_id: str, repo_root: Path | str | None = None) -> bool:
    """Mark suggestion as dismissed."""
    return update_status(suggestion_id, "dismissed", repo_root=repo_root)


def snooze_suggestion(
    suggestion_id: str,
    snoozed_until_utc: str,
    repo_root: Path | str | None = None,
) -> bool:
    """Snooze suggestion until given UTC time (ISO)."""
    return update_status(
        suggestion_id,
        "snoozed",
        repo_root=repo_root,
        snoozed_until_utc=snoozed_until_utc,
    )
