"""
M35H.1: Explain what work will stop, continue, or require human takeover.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.operator_mode.models import (
    PauseState,
    PauseKind,
    WorkImpactExplanation,
    DelegatedResponsibility,
)
from workflow_dataset.operator_mode.store import (
    load_pause_state,
    load_suspension_revocation_state,
    get_responsibility,
    list_responsibility_ids,
    get_bundle,
)
from workflow_dataset.utils.dates import utc_now_iso


def explain_work_impact(
    repo_root: Path | str | None = None,
    responsibility_ids: list[str] | None = None,
    bundle_ids: list[str] | None = None,
) -> WorkImpactExplanation:
    """
    Build a clear explanation: what will stop, what will continue, what requires human takeover.
    If responsibility_ids/bundle_ids are None, consider all known responsibilities.
    """
    root = Path(repo_root).resolve() if repo_root else None
    now = utc_now_iso()
    pause = load_pause_state(repo_root=root)
    susp_rev = load_suspension_revocation_state(repo_root=root)
    revoked_set = set(susp_rev.revoked_ids)
    suspended_set = set(susp_rev.suspended_ids)

    # Resolve scope: specific ids + bundle members, or all
    if responsibility_ids is None and bundle_ids is None:
        responsibility_ids = list_responsibility_ids(repo_root=root)
    resolved_ids: set[str] = set(responsibility_ids or [])
    for bid in bundle_ids or []:
        b = get_bundle(bid, repo_root=root)
        if b:
            resolved_ids.update(b.responsibility_ids)

    what_stops: list[str] = []
    what_continues: list[str] = []
    what_requires_human: list[str] = []

    for rid in sorted(resolved_ids):
        r = get_responsibility(rid, repo_root=root)
        label = r.label or rid if r else rid
        if rid in revoked_set:
            what_stops.append(label)
            what_requires_human.append(f"{label} (revoked — re-delegate to resume)")
        elif pause.kind == PauseKind.EMERGENCY:
            what_stops.append(label)
        elif pause.kind == PauseKind.SAFE:
            if rid in pause.safe_continue_responsibility_ids:
                what_continues.append(label)
            else:
                what_stops.append(label)
        elif rid in suspended_set:
            what_stops.append(label)
            what_requires_human.append(f"{label} (suspended — resume to continue)")
        else:
            what_continues.append(label)

    summary_parts = []
    if pause.kind != PauseKind.NONE:
        summary_parts.append(f"Pause active: {pause.kind.value} — {pause.reason or 'no reason given'}")
    if revoked_set:
        summary_parts.append(f"{len(revoked_set)} responsibility(ies) revoked")
    if what_stops:
        summary_parts.append(f"{len(what_stops)} will stop")
    if what_continues:
        summary_parts.append(f"{len(what_continues)} will continue")
    if what_requires_human:
        summary_parts.append(f"{len(what_requires_human)} require human takeover or review")

    summary = "; ".join(summary_parts) if summary_parts else "No impact (no pause, no revocations)."

    return WorkImpactExplanation(
        what_stops=what_stops,
        what_continues=what_continues,
        what_requires_human=what_requires_human,
        pause_active=pause.kind != PauseKind.NONE,
        pause_kind=pause.kind.value,
        revoked_count=len(revoked_set),
        summary=summary,
        generated_at_utc=now,
    )
