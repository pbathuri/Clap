"""
M45I–M45L Phase B: Human takeover / handback flows — pause, stop, takeover, redirect, approve continuation, handback.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.supervisory_control.models import (
    SupervisedLoopView,
    OperatorIntervention,
    PauseState,
    RedirectState,
    TakeoverState,
    HandbackState,
    OperatorRationale,
    LOOP_VIEW_ACTIVE,
    LOOP_VIEW_PAUSED,
    LOOP_VIEW_TAKEN_OVER,
    LOOP_VIEW_AWAITING_CONTINUATION,
    LOOP_VIEW_STOPPED,
    INTERVENTION_PAUSE,
    INTERVENTION_STOP,
    INTERVENTION_TAKEOVER,
    INTERVENTION_REDIRECT,
    INTERVENTION_APPROVE_CONTINUATION,
    INTERVENTION_HANDBACK,
)
from workflow_dataset.supervisory_control.store import (
    load_loop_views,
    save_loop_views,
    load_pause_state,
    save_pause_state,
    load_redirect_state,
    save_redirect_state,
    load_takeover_state,
    save_takeover_state,
    load_last_handback,
    save_handback_state,
    append_intervention,
    append_rationale,
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


def _get_or_create_loop(loop_id: str, repo_root=None) -> SupervisedLoopView | None:
    loops = load_loop_views(repo_root)
    for v in loops:
        if v.loop_id == loop_id:
            return v
    return None


def _update_loop_status(loop_id: str, status: str, repo_root=None) -> None:
    loops = load_loop_views(repo_root)
    for v in loops:
        if v.loop_id == loop_id:
            v.status = status
            v.updated_at_utc = utc_now_iso()
            save_loop_views(loops, repo_root)
            return
    # If no loop view exists, create one
    loops.append(SupervisedLoopView(loop_id=loop_id, label=loop_id, status=status, updated_at_utc=utc_now_iso(), created_at_utc=utc_now_iso()))
    save_loop_views(loops, repo_root)


def pause_loop(loop_id: str, reason: str = "", repo_root=None, rationale_text: str = "") -> PauseState:
    now = utc_now_iso()
    state = PauseState(loop_id=loop_id, paused_at_utc=now, reason=reason or "Operator paused.")
    save_pause_state(state, repo_root)
    _update_loop_status(loop_id, LOOP_VIEW_PAUSED, repo_root)
    rid = ""
    if rationale_text:
        rid = stable_id("rat", loop_id, now, prefix="rat_")
        append_rationale(OperatorRationale(rationale_id=rid, text=rationale_text, created_at_utc=now, attached_to_loop_id=loop_id), repo_root)
    append_intervention(OperatorIntervention(
        intervention_id=stable_id("int", loop_id, INTERVENTION_PAUSE, now, prefix="int_"),
        loop_id=loop_id,
        kind=INTERVENTION_PAUSE,
        created_at_utc=now,
        rationale_id=rid,
        payload={"reason": reason or "Operator paused."},
    ), repo_root)
    return state


def resume_loop(loop_id: str, repo_root=None) -> bool:
    state = load_pause_state(loop_id, repo_root)
    if not state or state.resumed_at_utc:
        return False
    state.resumed_at_utc = utc_now_iso()
    save_pause_state(state, repo_root)
    _update_loop_status(loop_id, LOOP_VIEW_ACTIVE, repo_root)
    return True


def stop_loop(loop_id: str, reason: str = "", repo_root=None) -> None:
    now = utc_now_iso()
    save_pause_state(None, repo_root, loop_id=loop_id)  # clear pause if any
    save_takeover_state(None, repo_root, loop_id=loop_id)  # clear takeover if any
    _update_loop_status(loop_id, LOOP_VIEW_STOPPED, repo_root)
    append_intervention(OperatorIntervention(
        intervention_id=stable_id("int", loop_id, INTERVENTION_STOP, now, prefix="int_"),
        loop_id=loop_id,
        kind=INTERVENTION_STOP,
        created_at_utc=now,
        payload={"reason": reason or "Operator stopped loop."},
    ), repo_root)


def take_over_loop(loop_id: str, operator_note: str = "", repo_root=None, rationale_text: str = "") -> TakeoverState:
    now = utc_now_iso()
    state = TakeoverState(loop_id=loop_id, taken_over_at_utc=now, operator_note=operator_note)
    save_takeover_state(state, repo_root)
    save_pause_state(None, repo_root, loop_id=loop_id)
    _update_loop_status(loop_id, LOOP_VIEW_TAKEN_OVER, repo_root)
    rid = ""
    if rationale_text:
        rid = stable_id("rat", loop_id, now, prefix="rat_")
        append_rationale(OperatorRationale(rationale_id=rid, text=rationale_text, created_at_utc=now, attached_to_loop_id=loop_id), repo_root)
    append_intervention(OperatorIntervention(
        intervention_id=stable_id("int", loop_id, INTERVENTION_TAKEOVER, now, prefix="int_"),
        loop_id=loop_id,
        kind=INTERVENTION_TAKEOVER,
        created_at_utc=now,
        rationale_id=rid,
        payload={"operator_note": operator_note},
    ), repo_root)
    return state


def redirect_loop(loop_id: str, next_step_hint: str, repo_root=None) -> RedirectState:
    now = utc_now_iso()
    state = RedirectState(loop_id=loop_id, redirect_at_utc=now, next_step_hint=next_step_hint, applied=False)
    save_redirect_state(state, repo_root)
    append_intervention(OperatorIntervention(
        intervention_id=stable_id("int", loop_id, INTERVENTION_REDIRECT, now, prefix="int_"),
        loop_id=loop_id,
        kind=INTERVENTION_REDIRECT,
        created_at_utc=now,
        payload={"next_step_hint": next_step_hint},
    ), repo_root)
    return state


def approve_continuation(loop_id: str, repo_root=None, rationale_text: str = "") -> bool:
    pause = load_pause_state(loop_id, repo_root)
    if not pause or pause.resumed_at_utc:
        return False
    now = utc_now_iso()
    rid = ""
    if rationale_text:
        rid = stable_id("rat", loop_id, now, prefix="rat_")
        append_rationale(OperatorRationale(rationale_id=rid, text=rationale_text, created_at_utc=now, attached_to_loop_id=loop_id), repo_root)
    append_intervention(OperatorIntervention(
        intervention_id=stable_id("int", loop_id, INTERVENTION_APPROVE_CONTINUATION, now, prefix="int_"),
        loop_id=loop_id,
        kind=INTERVENTION_APPROVE_CONTINUATION,
        created_at_utc=now,
        rationale_id=rid,
        payload={},
    ), repo_root)
    _update_loop_status(loop_id, LOOP_VIEW_AWAITING_CONTINUATION, repo_root)
    return True


def handback_loop(loop_id: str, handback_note: str = "", safe_to_resume: bool = True, repo_root=None) -> HandbackState | None:
    takeover = load_takeover_state(loop_id, repo_root)
    if not takeover or takeover.returned_at_utc:
        return None
    now = utc_now_iso()
    state = HandbackState(loop_id=loop_id, handback_at_utc=now, handback_note=handback_note, safe_to_resume=safe_to_resume)
    save_handback_state(state, repo_root)
    takeover.returned_at_utc = now
    save_takeover_state(takeover, repo_root)
    _update_loop_status(loop_id, LOOP_VIEW_ACTIVE, repo_root)
    append_intervention(OperatorIntervention(
        intervention_id=stable_id("int", loop_id, INTERVENTION_HANDBACK, now, prefix="int_"),
        loop_id=loop_id,
        kind=INTERVENTION_HANDBACK,
        created_at_utc=now,
        payload={"handback_note": handback_note, "safe_to_resume": safe_to_resume},
    ), repo_root)
    return state
