"""
M45I–M45L Phase C: Control panel / review flows — inspect loop, confidence/gates, attach rationale.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.supervisory_control.models import (
    SupervisedLoopView,
    LOOP_VIEW_ACTIVE,
    LOOP_VIEW_PAUSED,
    LOOP_VIEW_TAKEN_OVER,
    LOOP_VIEW_AWAITING_CONTINUATION,
    LOOP_VIEW_STOPPED,
)
from workflow_dataset.supervisory_control.store import (
    load_loop_views,
    save_loop_views,
    load_pause_state,
    load_redirect_state,
    load_takeover_state,
    load_last_handback,
    load_interventions,
    load_rationales,
    load_audit_notes,
    append_rationale,
    append_audit_note,
    OperatorRationale,
    LoopControlAuditNote,
)

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def sync_loop_views_from_supervised(repo_root: Path | str | None = None) -> list[SupervisedLoopView]:
    """Build or update loop views from supervised_loop current cycle; persist and return."""
    root = _root(repo_root)
    loops = load_loop_views(repo_root)
    try:
        from workflow_dataset.supervised_loop.summary import build_cycle_summary
        from workflow_dataset.supervised_loop.store import load_cycle
        summary = build_cycle_summary(repo_root=root)
        cycle = load_cycle(repo_root=root)
        cycle_id = summary.cycle_id or (cycle.cycle_id if cycle else "") or "default"
        loop_id = cycle_id or "default"
        existing = next((v for v in loops if v.loop_id == loop_id), None)
        now = utc_now_iso()
        if existing:
            existing.project_slug = summary.project_slug or ""
            existing.goal_text = (summary.goal_text or "")[:500]
            existing.cycle_id = cycle_id
            existing.pending_count = summary.pending_queue_count or 0
            existing.last_activity_utc = now
            existing.updated_at_utc = now
            # Preserve status from supervisory state (pause/takeover) unless we have explicit override
            pause = load_pause_state(loop_id, repo_root)
            takeover = load_takeover_state(loop_id, repo_root)
            if takeover and not takeover.returned_at_utc:
                existing.status = LOOP_VIEW_TAKEN_OVER
            elif pause and not pause.resumed_at_utc:
                existing.status = LOOP_VIEW_PAUSED
            elif existing.status not in (LOOP_VIEW_PAUSED, LOOP_VIEW_TAKEN_OVER, LOOP_VIEW_STOPPED, LOOP_VIEW_AWAITING_CONTINUATION):
                existing.status = summary.status or LOOP_VIEW_ACTIVE
        else:
            pause = load_pause_state(loop_id, repo_root)
            takeover = load_takeover_state(loop_id, repo_root)
            status = LOOP_VIEW_ACTIVE
            if takeover and not takeover.returned_at_utc:
                status = LOOP_VIEW_TAKEN_OVER
            elif pause and not pause.resumed_at_utc:
                status = LOOP_VIEW_PAUSED
            else:
                status = summary.status or LOOP_VIEW_ACTIVE
            loops.append(SupervisedLoopView(
                loop_id=loop_id,
                label=summary.project_slug or loop_id,
                status=status,
                project_slug=summary.project_slug or "",
                goal_text=(summary.goal_text or "")[:500],
                cycle_id=cycle_id,
                pending_count=summary.pending_queue_count or 0,
                last_activity_utc=now,
                created_at_utc=now,
                updated_at_utc=now,
            ))
        save_loop_views(loops, repo_root)
    except Exception:
        pass
    return loops


def list_loops(repo_root: Path | str | None = None) -> list[SupervisedLoopView]:
    """List loop views; sync from supervised_loop first if empty."""
    loops = load_loop_views(repo_root)
    if not loops:
        loops = sync_loop_views_from_supervised(repo_root)
    return loops


def get_loop(loop_id: str, repo_root: Path | str | None = None) -> SupervisedLoopView | None:
    """Return one loop view by id; sync first so current cycle is present."""
    loops = sync_loop_views_from_supervised(repo_root)
    for v in loops:
        if v.loop_id == loop_id:
            return v
    return None


def inspect_loop(loop_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Inspect current loop: view, pause/takeover/redirect/handback state, recent interventions, queue summary."""
    root = _root(repo_root)
    view = get_loop(loop_id, repo_root)
    out: dict[str, Any] = {
        "loop_id": loop_id,
        "view": view.to_dict() if view else None,
        "pause_state": None,
        "redirect_state": None,
        "takeover_state": None,
        "last_handback": None,
        "recent_interventions": [],
        "pending_count": 0,
        "next_proposed_action_id": "",
        "next_proposed_action_label": "",
    }
    if view:
        out["pending_count"] = view.pending_count
    pause = load_pause_state(loop_id, repo_root)
    if pause:
        out["pause_state"] = pause.to_dict()
    redirect = load_redirect_state(loop_id, repo_root)
    if redirect:
        out["redirect_state"] = redirect.to_dict()
    takeover = load_takeover_state(loop_id, repo_root)
    if takeover:
        out["takeover_state"] = takeover.to_dict()
    handback = load_last_handback(loop_id, repo_root)
    if handback:
        out["last_handback"] = handback.to_dict()
    interventions = [i for i in load_interventions(repo_root) if i.loop_id == loop_id]
    out["recent_interventions"] = [i.to_dict() for i in interventions[-10:]]
    try:
        from workflow_dataset.supervised_loop.summary import build_cycle_summary
        s = build_cycle_summary(repo_root=root)
        if s.cycle_id == loop_id or not view:
            out["pending_count"] = s.pending_queue_count
            out["next_proposed_action_id"] = s.next_proposed_action_id or ""
            out["next_proposed_action_label"] = s.next_proposed_action_label or ""
    except Exception:
        pass
    return out


def inspect_confidence_gates(loop_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Inspect confidence and gate status for the loop (from supervised_loop queue and policy)."""
    root = _root(repo_root)
    out: dict[str, Any] = {"loop_id": loop_id, "pending_approval_count": 0, "blocked_reason": "", "gate_status": "unknown"}
    try:
        from workflow_dataset.supervised_loop.summary import build_cycle_summary
        from workflow_dataset.supervised_loop.store import load_queue, load_cycle
        s = build_cycle_summary(repo_root=root)
        queue = load_queue(repo_root=root)
        cycle = load_cycle(repo_root=root)
        pending = [q for q in queue if q.status == "pending"]
        out["pending_approval_count"] = len(pending)
        out["blocked_reason"] = s.blocked_reason or ""
        out["cycle_status"] = s.status or ""
        if cycle and cycle.blocked_reason:
            out["blocked_reason"] = cycle.blocked_reason.reason or out["blocked_reason"]
        out["gate_status"] = "blocked" if out["blocked_reason"] else ("awaiting_approval" if pending else "ready")
    except Exception as e:
        out["gate_status"] = "error"
        out["error"] = str(e)
    return out


def attach_rationale(loop_id: str, text: str, intervention_id: str = "", repo_root: Path | str | None = None) -> OperatorRationale:
    """Attach an operator rationale to a loop or intervention."""
    now = utc_now_iso()
    rid = stable_id("rat", loop_id, now, prefix="rat_")
    r = OperatorRationale(
        rationale_id=rid,
        text=text,
        created_at_utc=now,
        attached_to_intervention_id=intervention_id,
        attached_to_loop_id=loop_id,
    )
    append_rationale(r, repo_root)
    return r


def attach_audit_note(loop_id: str, note_text: str, kind: str = "audit", intervention_id: str = "", repo_root: Path | str | None = None) -> LoopControlAuditNote:
    """Attach an audit note to a loop or intervention."""
    now = utc_now_iso()
    note_id = stable_id("note", loop_id, now, prefix="note_")
    note = LoopControlAuditNote(
        note_id=note_id,
        loop_id=loop_id,
        intervention_id=intervention_id,
        created_at_utc=now,
        note_text=note_text,
        kind=kind,
    )
    append_audit_note(note, repo_root)
    return note


def mission_control_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mission-control visibility: active/paused/awaiting/taken_over counts, most urgent intervention candidate."""
    loops = list_loops(repo_root)
    active = [l for l in loops if l.status == LOOP_VIEW_ACTIVE]
    paused = [l for l in loops if l.status == LOOP_VIEW_PAUSED]
    awaiting = [l for l in loops if l.status == LOOP_VIEW_AWAITING_CONTINUATION]
    taken_over = [l for l in loops if l.status == LOOP_VIEW_TAKEN_OVER]
    stopped = [l for l in loops if l.status == LOOP_VIEW_STOPPED]
    # Most urgent: paused with pending, or awaiting_continuation, or first taken_over
    urgent_loop_id = ""
    urgent_reason = ""
    if paused and any(l.pending_count > 0 for l in paused):
        cand = next((l for l in paused if l.pending_count > 0), None)
        if cand:
            urgent_loop_id = cand.loop_id
            urgent_reason = "paused_with_pending"
    elif awaiting:
        urgent_loop_id = awaiting[0].loop_id
        urgent_reason = "awaiting_continuation"
    elif taken_over:
        urgent_loop_id = taken_over[0].loop_id
        urgent_reason = "under_takeover"
    return {
        "active_loops_count": len(active),
        "paused_loops_count": len(paused),
        "awaiting_continuation_count": len(awaiting),
        "taken_over_count": len(taken_over),
        "stopped_count": len(stopped),
        "most_urgent_loop_id": urgent_loop_id,
        "most_urgent_reason": urgent_reason,
    }
