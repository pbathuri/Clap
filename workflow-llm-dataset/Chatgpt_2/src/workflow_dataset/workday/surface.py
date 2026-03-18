"""
M36A–M36D: Daily operating surface — current workday state, active project, queue, approvals, trust, next transition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.workday.models import WorkdayState, WorkdayStateRecord, BlockedStateInfo
from workflow_dataset.workday.store import load_workday_state, current_day_id, get_active_workday_preset_id
from workflow_dataset.workday.state_machine import (
    can_transition,
    VALID_TRANSITIONS,
    blocked_reasons,
    gather_context,
)
from workflow_dataset.workday.presets import get_workday_preset


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


@dataclass
class DailyOperatingSurface:
    """Single top-level daily operating surface."""
    current_workday_state: str = ""
    state_entered_at_iso: str = ""
    day_started_at_iso: str = ""
    day_id: str = ""
    active_project_id: str = ""
    active_project_title: str = ""
    active_focus: str = ""
    top_queue_item: str = ""
    pending_approvals_count: int = 0
    pending_approvals_summary: str = ""
    automation_background_summary: str = ""
    trust_posture: str = ""
    next_recommended_transition: str = ""
    next_recommended_reason: str = ""
    blocked_transitions: list[BlockedStateInfo] = field(default_factory=list)
    allowed_next_states: list[str] = field(default_factory=list)
    updated_at_iso: str = ""
    # M36D.1 role preset
    preset_id: str = ""
    role_operating_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_workday_state": self.current_workday_state,
            "state_entered_at_iso": self.state_entered_at_iso,
            "day_started_at_iso": self.day_started_at_iso,
            "day_id": self.day_id,
            "active_project_id": self.active_project_id,
            "active_project_title": self.active_project_title,
            "active_focus": self.active_focus,
            "top_queue_item": self.top_queue_item,
            "pending_approvals_count": self.pending_approvals_count,
            "pending_approvals_summary": self.pending_approvals_summary,
            "automation_background_summary": self.automation_background_summary,
            "trust_posture": self.trust_posture,
            "next_recommended_transition": self.next_recommended_transition,
            "next_recommended_reason": self.next_recommended_reason,
            "blocked_transitions": [
                {"from": b.from_state, "to": b.to_state, "reason": b.reason} for b in self.blocked_transitions
            ],
            "allowed_next_states": list(self.allowed_next_states),
            "updated_at_iso": self.updated_at_iso,
            "preset_id": self.preset_id,
            "role_operating_hint": self.role_operating_hint,
        }


def build_daily_operating_surface(repo_root: Path | str | None = None) -> DailyOperatingSurface:
    """Build the single top-level daily operating surface from workday state, workspace, mission_control, trust."""
    root = _root(repo_root)
    record = load_workday_state(root)
    surf = DailyOperatingSurface(
        current_workday_state=record.state,
        state_entered_at_iso=record.entered_at_iso,
        day_started_at_iso=record.day_started_at_iso,
        day_id=record.day_id or current_day_id(),
        updated_at_iso=utc_now_iso(),
    )
    surf.allowed_next_states = VALID_TRANSITIONS.get(record.state, [])
    context = gather_context(root)

    # Blocked transitions (e.g. to operator_mode when paused)
    for to_state in surf.allowed_next_states:
        ok, blocked = can_transition(record.state, to_state, context)
        surf.blocked_transitions.extend(blocked)

    # M36D.1 Active workday preset (role)
    preset = None
    active_preset_id = get_active_workday_preset_id(root)
    if active_preset_id:
        preset = get_workday_preset(active_preset_id)
        if preset:
            surf.preset_id = preset.preset_id
            surf.role_operating_hint = preset.role_operating_hint or ""

    # One bounded mission-control read for this surface (full aggregate can hang).
    try:
        from workflow_dataset.workspace.state import _mission_control_state_with_timeout

        mc_state = _mission_control_state_with_timeout(root)
    except Exception:
        mc_state = None

    # Active project, focus, queue from workspace
    try:
        from workflow_dataset.workspace.state import build_active_work_context

        ctx = build_active_work_context(root, mission_control_prefetch=mc_state)
        surf.active_project_id = ctx.active_project_id or ""
        surf.active_project_title = ctx.active_project_title or ""
        surf.active_focus = (ctx.active_goal_text or "")[:120]
        surf.pending_approvals_count = ctx.queued_approvals_count
        surf.pending_approvals_summary = (
            f"{ctx.queued_approvals_count} pending approval(s)" if ctx.queued_approvals_count > 0
            else "No pending approvals"
        )
        if ctx.queued_approval_ids:
            surf.top_queue_item = ctx.queued_approval_ids[0]
    except Exception:
        pass

    # Automation / background summary from mission_control (reuse bounded state)
    try:
        state = mc_state or {}
        br = state.get("background_runner_state", {})
        ai = state.get("automation_inbox", {})
        parts = []
        if mc_state and not br.get("error"):
            parts.append(f"Background: queue={br.get('queue_length', 0)} active={len(br.get('active_run_ids', []))}")
        if mc_state and not ai.get("error"):
            parts.append(f"Inbox unseen={ai.get('unseen_automation_results_count', 0)}")
        surf.automation_background_summary = (
            "; ".join(parts) or ("—" if mc_state else "— (run workflow-dataset mission-control for automation summary)")
        )
    except Exception:
        surf.automation_background_summary = "—"

    # Trust posture
    try:
        from workflow_dataset.trust.validation_report import get_active_preset_id

        preset_id = get_active_preset_id(root)
        if preset_id:
            surf.trust_posture = f"Preset: {preset_id}"
        else:
            acs = (mc_state or {}).get("authority_contracts_state", {})
            if mc_state and not acs.get("error"):
                surf.trust_posture = f"Tier: {acs.get('active_tier_posture', '—')}"
            else:
                surf.trust_posture = "—"
    except Exception:
        surf.trust_posture = "—"

    # Next recommended transition (preset can override default after startup; operator_mode preferred for some roles)
    if record.state == WorkdayState.NOT_STARTED.value or record.state == WorkdayState.RESUME_PENDING.value:
        surf.next_recommended_transition = WorkdayState.STARTUP.value
        surf.next_recommended_reason = "Start the day: workflow-dataset day start"
    elif record.state == WorkdayState.STARTUP.value:
        if preset and preset.default_transition_after_startup and preset.default_transition_after_startup in surf.allowed_next_states:
            surf.next_recommended_transition = preset.default_transition_after_startup
            surf.next_recommended_reason = f"({preset.label}) workflow-dataset day mode --set {preset.default_transition_after_startup}"
        else:
            surf.next_recommended_transition = WorkdayState.FOCUS_WORK.value
            surf.next_recommended_reason = "Shift to focus work: workflow-dataset day mode --set focus_work"
    elif record.state in (WorkdayState.FOCUS_WORK.value, WorkdayState.OPERATOR_MODE.value):
        if surf.pending_approvals_count > 0 and (not preset or preset.queue_review_emphasis != "low"):
            surf.next_recommended_transition = WorkdayState.REVIEW_AND_APPROVALS.value
            surf.next_recommended_reason = "Pending approvals; shift to review: workflow-dataset day mode --set review_and_approvals"
        elif record.state == WorkdayState.FOCUS_WORK.value and preset and preset.operator_mode_usage == "preferred" and WorkdayState.OPERATOR_MODE.value in surf.allowed_next_states:
            surf.next_recommended_transition = WorkdayState.OPERATOR_MODE.value
            surf.next_recommended_reason = f"({preset.label}) workflow-dataset day mode --set operator_mode"
        else:
            surf.next_recommended_transition = WorkdayState.WRAP_UP.value
            surf.next_recommended_reason = "Wrap up when ready: workflow-dataset day wrap-up"
    elif record.state == WorkdayState.REVIEW_AND_APPROVALS.value:
        surf.next_recommended_transition = WorkdayState.FOCUS_WORK.value
        surf.next_recommended_reason = "Return to focus: workflow-dataset day mode --set focus_work"
    elif record.state == WorkdayState.WRAP_UP.value:
        surf.next_recommended_transition = WorkdayState.SHUTDOWN.value
        surf.next_recommended_reason = "End day: workflow-dataset day shutdown"
    else:
        surf.next_recommended_transition = ""
        surf.next_recommended_reason = ""

    return surf


def format_daily_operating_surface(surf: DailyOperatingSurface) -> str:
    """Human-readable daily operating surface."""
    lines: list[str] = []
    lines.append("=== Daily operating surface ===")
    lines.append(f"  State: {surf.current_workday_state}  (entered: {surf.state_entered_at_iso or '—'})")
    lines.append(f"  Day: {surf.day_id}  started: {surf.day_started_at_iso or '—'}")
    if surf.preset_id:
        lines.append(f"  Preset: {surf.preset_id}")
        if surf.role_operating_hint:
            lines.append(f"  Hint: {surf.role_operating_hint}")
    lines.append("")
    lines.append("[Context]")
    lines.append(f"  Project: {surf.active_project_id or '—'}  {surf.active_project_title or ''}")
    lines.append(f"  Focus: {(surf.active_focus[:60] + '…') if len(surf.active_focus or '') > 60 else (surf.active_focus or '—')}")
    lines.append(f"  Top queue: {surf.top_queue_item or '—'}")
    lines.append(f"  Approvals: {surf.pending_approvals_summary}")
    lines.append(f"  Automation: {surf.automation_background_summary}")
    lines.append(f"  Trust: {surf.trust_posture}")
    lines.append("")
    lines.append("[Transitions]")
    lines.append(f"  Allowed next: {', '.join(surf.allowed_next_states) or '—'}")
    if surf.next_recommended_transition:
        lines.append(f"  Recommended: {surf.next_recommended_transition}")
        lines.append(f"  Reason: {surf.next_recommended_reason}")
    if surf.blocked_transitions:
        lines.append("  Blocked:")
        for b in surf.blocked_transitions[:5]:
            lines.append(f"    -> {b.to_state}: {b.reason[:70]}")
    lines.append("")
    return "\n".join(lines)
