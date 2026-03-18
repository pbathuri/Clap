"""
M35H.1: Emergency pause, safe pause, revocation flows; pause/revocation report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]

from workflow_dataset.utils.dates import utc_now_iso

from workflow_dataset.operator_mode.models import (
    PauseState,
    PauseKind,
    RevocationRecord,
    PauseRevocationReport,
    WorkImpactExplanation,
)
from workflow_dataset.operator_mode.store import (
    load_pause_state,
    save_pause_state,
    load_suspension_revocation_state,
    save_suspension_revocation_state,
    load_revocation_history,
    append_revocation_record,
    get_responsibility,
    get_bundle,
)
from workflow_dataset.operator_mode.explain import explain_work_impact


def set_emergency_pause(
    reason: str = "",
    repo_root: Path | str | None = None,
) -> PauseState:
    """Set emergency pause: all operator responsibilities stop until cleared."""
    now = utc_now_iso()
    state = PauseState(
        kind=PauseKind.EMERGENCY,
        reason=reason or "Emergency pause — all operator work stopped.",
        started_utc=now,
        safe_continue_responsibility_ids=[],
        updated_utc=now,
    )
    save_pause_state(state, repo_root=repo_root)
    return state


def set_safe_pause(
    reason: str = "",
    safe_continue_responsibility_ids: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> PauseState:
    """Set safe pause: only listed responsibilities may continue; others stop."""
    now = utc_now_iso()
    state = PauseState(
        kind=PauseKind.SAFE,
        reason=reason or "Safe pause — only explicitly allowed work continues.",
        started_utc=now,
        safe_continue_responsibility_ids=list(safe_continue_responsibility_ids or []),
        updated_utc=now,
    )
    save_pause_state(state, repo_root=repo_root)
    return state


def clear_pause(repo_root: Path | str | None = None) -> PauseState:
    """Clear pause; operator mode resumes according to suspension/revocation state."""
    now = utc_now_iso()
    state = PauseState(kind=PauseKind.NONE, updated_utc=now)
    save_pause_state(state, repo_root=repo_root)
    return state


def revoke_responsibility(
    responsibility_id: str,
    reason: str = "",
    repo_root: Path | str | None = None,
) -> RevocationRecord:
    """Revoke a single responsibility; add to revocation state and history."""
    root = Path(repo_root).resolve() if repo_root else None
    now = utc_now_iso()
    rev_id = stable_id("rev", responsibility_id, now, prefix="rev_")[:20]
    record = RevocationRecord(
        revocation_id=rev_id,
        responsibility_id=responsibility_id,
        reason=reason or "Revoked by operator",
        revoked_at_utc=now,
        revoked_responsibility_ids=[responsibility_id],
    )
    append_revocation_record(record, repo_root=root)
    state = load_suspension_revocation_state(repo_root=root)
    if responsibility_id not in state.revoked_ids:
        state.revoked_ids = list(state.revoked_ids) + [responsibility_id]
        state.revoked_reasons[responsibility_id] = record.reason
        state.updated_utc = now
        save_suspension_revocation_state(state, repo_root=root)
    return record


def revoke_bundle(
    bundle_id: str,
    reason: str = "",
    repo_root: Path | str | None = None,
) -> RevocationRecord | None:
    """Revoke all responsibilities in a bundle; add one revocation record and update state."""
    root = Path(repo_root).resolve() if repo_root else None
    bundle = get_bundle(bundle_id, repo_root=root)
    if not bundle or not bundle.responsibility_ids:
        return None
    now = utc_now_iso()
    rev_id = stable_id("rev", bundle_id, now, prefix="rev_")[:20]
    record = RevocationRecord(
        revocation_id=rev_id,
        bundle_id=bundle_id,
        reason=reason or f"Bundle {bundle_id} revoked by operator",
        revoked_at_utc=now,
        revoked_responsibility_ids=list(bundle.responsibility_ids),
    )
    append_revocation_record(record, repo_root=root)
    state = load_suspension_revocation_state(repo_root=root)
    for rid in record.revoked_responsibility_ids:
        if rid not in state.revoked_ids:
            state.revoked_ids = list(state.revoked_ids) + [rid]
            state.revoked_reasons[rid] = record.reason
    state.updated_utc = now
    save_suspension_revocation_state(state, repo_root=root)
    return record


def build_pause_revocation_report(repo_root: Path | str | None = None) -> PauseRevocationReport:
    """Build a report: current pause state, recent revocation records, and work-impact explanation."""
    root = Path(repo_root).resolve() if repo_root else None
    now = utc_now_iso()
    pause = load_pause_state(repo_root=root)
    history = load_revocation_history(repo_root=root)
    impact = explain_work_impact(repo_root=root)
    impact.generated_at_utc = now
    return PauseRevocationReport(
        pause_state=pause,
        revocation_records=history[-50:],
        impact=impact,
        report_generated_at_utc=now,
    )
