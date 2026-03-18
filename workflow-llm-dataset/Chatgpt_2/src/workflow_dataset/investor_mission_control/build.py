"""
M52E–M52H: Assemble investor mission-control home from real demo + onboarding state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone

    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.investor_mission_control.models import (
    ActivityTimelineItem,
    ActivityTimelineState,
    FirstValueSurface,
    Hero30Surface,
    MemoryBootstrapSurface,
    MissionControlInvestorHome,
    MissionControlSidePanelState,
    NextStepCard,
    ReadinessStateSnapshot,
    ReadyToAssistSurface,
    RolePreviewCard,
    RoleStateSurface,
    RoleSwitchPreviewState,
    TrustPostureSurface,
)
from workflow_dataset.investor_mission_control.narrative_m52h1 import (
    build_memory_story,
    build_role_switch_previews,
    hero_eyebrow,
    hero_headline,
    hero_subline,
    investor_flow_lines,
    next_step_after_first_value,
    tight_first_value_subcopy,
    trust_chip,
)
from workflow_dataset.investor_mission_control.surfaces import (
    bounded_memory_note,
    humanize_first_value_command,
    memory_headline,
    readiness_headline,
    trust_investor_copy,
    vertical_pack_display_name,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _readiness_snapshot(root: Path) -> ReadinessStateSnapshot:
    try:
        from workflow_dataset.demo_usb.bundle_root import resolve_demo_bundle_root
        from workflow_dataset.demo_usb import build_readiness_report

        br = resolve_demo_bundle_root(None, allow_cwd=True)
        rep = build_readiness_report(br, explicit_bundle=None)
        cap = rep.capability_level.value
        hl, ok = readiness_headline(cap)
        return ReadinessStateSnapshot(capability=cap, headline=hl, device_ok_for_demo=ok)
    except Exception:
        return ReadinessStateSnapshot(
            capability="unknown",
            headline="Connect demo USB or run from product folder to verify readiness.",
            device_ok_for_demo=False,
        )


def _timeline(
    root: Path,
    session: Any,
    completion: Any,
    readiness: ReadinessStateSnapshot,
) -> ActivityTimelineState:
    items: list[ActivityTimelineItem] = []
    env_done = readiness.capability in ("full", "degraded")
    items.append(
        ActivityTimelineItem(
            step_id="env",
            label="Environment checked",
            status="done" if env_done else "pending",
        )
    )
    role_done = bool(session and session.role_preset_id)
    items.append(
        ActivityTimelineItem(
            step_id="role",
            label="Role & preset applied",
            status="done" if role_done else ("current" if env_done else "pending"),
        )
    )
    mem_done = bool(session and session.memory_bootstrap_completed)
    st = "done" if mem_done else ("current" if role_done else "pending")
    items.append(
        ActivityTimelineItem(
            step_id="memory",
            label="Bounded memory bootstrap",
            status=st,
        )
    )
    assist = bool(completion and getattr(completion, "ready_for_assist", False))
    items.append(
        ActivityTimelineItem(
            step_id="assist",
            label="Ready to assist",
            status="done" if assist else ("current" if mem_done else "pending"),
        )
    )
    return ActivityTimelineState(items=items)


def _side_panel(root: Path) -> MissionControlSidePanelState:
    summary = ""
    try:
        from workflow_dataset.review_studio.inbox import build_inbox

        items = build_inbox(repo_root=root, status="pending", limit=30)
        n = len(items)
        if n == 0:
            summary = "Review inbox: clear for now."
        elif n == 1:
            summary = "1 item in your review inbox when you want it."
        else:
            summary = f"{n} items in review inbox — optional, not blocking the demo."
    except Exception:
        summary = ""
    note = ""
    if not summary:
        note = "Inbox unavailable in this context — demo path still works."
    return MissionControlSidePanelState(inbox_summary=summary or note, intervention_note="")


def build_mission_control_investor_home(repo_root: Path | str | None = None) -> MissionControlInvestorHome:
    root = _root(repo_root)
    now = utc_now_iso()

    from workflow_dataset.demo_onboarding import (
        build_ready_to_assist_state,
        build_completion_state,
    )
    from workflow_dataset.demo_onboarding.presets import get_role_preset, get_default_role_preset
    from workflow_dataset.demo_onboarding.store import load_session, load_bootstrap_summary

    readiness = _readiness_snapshot(root)
    session = load_session(root)
    summary = load_bootstrap_summary(root)
    completion = build_completion_state(root)
    rta = build_ready_to_assist_state(root)

    preset = get_role_preset(session.role_preset_id) if session and session.role_preset_id else None
    eff = preset or get_default_role_preset()

    role = RoleStateSurface(
        active_role_label=rta.chosen_role_label or eff.label,
        vertical_pack_display=vertical_pack_display_name(rta.vertical_pack_id or eff.vertical_pack_id),
        preset_id=(session.role_preset_id if session else "") or eff.preset_id,
        role_one_liner=(
            (preset.description[:160] + "…")
            if preset and len(preset.description) > 160
            else (preset.description if preset else (eff.description[:160] + ("…" if len(eff.description) > 160 else "")))
        ),
    )

    files = int(summary.get("files_scanned") or 0)
    units = int(summary.get("memory_units_created") or 0)
    bullets: list[str] = []
    for x in (rta.inferred_project_context or [])[:2]:
        if x:
            bullets.append(f"Context signal: {x}")
    for t in (rta.recurring_themes or [])[:2]:
        if t:
            bullets.append(f"Theme: {t}")
    for p in (rta.likely_priorities or [])[:2]:
        if p:
            bullets.append(f"Priority hint: {p[:100]}")
    bullets = bullets[:4]
    narr_intro, insight_lines = build_memory_story(
        files,
        units,
        list(rta.inferred_project_context or []),
        list(rta.recurring_themes or []),
        list(rta.likely_priorities or []),
        completion.memory_bootstrapped or files > 0,
    )

    memory = MemoryBootstrapSurface(
        headline=memory_headline(completion.ready_for_assist, files, units),
        files_scanned=files,
        memory_units=units,
        what_learned_bullets=bullets if bullets else (["Complete memory bootstrap to see themes and priorities."] if not completion.memory_bootstrapped else ["Sample context loaded; refine with your own files later."]),
        bounded_note=bounded_memory_note(),
        narrative_intro=narr_intro,
        insight_lines=insight_lines,
    )

    if rta.ready:
        rs = ReadyToAssistSurface(
            ready=True,
            status_headline="Ready to assist",
            confirmation_plain="Role and sample context are loaded. Ask for the next task or open the first-value surface below.",
        )
    else:
        rs = ReadyToAssistSurface(
            ready=False,
            status_headline="Setup in progress",
            confirmation_plain=rta.confirmation_message or "Complete demo onboarding steps to unlock assist.",
        )

    cmd = rta.recommended_first_value_action or eff.recommended_first_value_command
    h, why, nxt = humanize_first_value_command(cmd)
    nsl, nsc = next_step_after_first_value(cmd)
    first = FirstValueSurface(
        headline=h,
        why_this_matters=why,
        command=cmd,
        what_happens_next=nxt,
        subcopy_tight=tight_first_value_subcopy(why),
        next_step_label=nsl,
        next_step_command=nsc,
    )

    tp = eff.trust_posture
    th, tb = trust_investor_copy(
        tp.simulate_first if tp else True,
        (tp.label if tp else "Demo mode"),
    )
    trust = TrustPostureSurface(headline=th, body=tb, simulate_first=tp.simulate_first if tp else True)

    sim = tp.simulate_first if tp else True
    hero = Hero30Surface(
        eyebrow=hero_eyebrow(completion.ready_for_assist, readiness.device_ok_for_demo),
        headline=hero_headline(completion.ready_for_assist),
        subline=hero_subline(readiness.capability, role.active_role_label),
        trust_chip=trust_chip(sim),
    )
    preview_raw = build_role_switch_previews(role.preset_id)
    role_previews = RoleSwitchPreviewState(
        cards=[
            RolePreviewCard(
                preset_id=x["preset_id"],
                label=x["label"],
                hook=x["hook"],
                switch_command=x["switch_command"],
                is_active=x["is_active"],
            )
            for x in preview_raw
        ]
    )
    next_card = NextStepCard(label=first.next_step_label, command=first.next_step_command)

    home = MissionControlInvestorHome(
        generated_at_utc=now,
        readiness=readiness,
        role=role,
        memory=memory,
        ready_surface=rs,
        first_value=first,
        trust=trust,
        timeline=_timeline(root, session, completion, readiness),
        side_panel=_side_panel(root),
        hero_30=hero,
        role_switch_previews=role_previews,
        next_step_card=next_card,
        narrative_flow_steps=investor_flow_lines(completion.ready_for_assist),
    )
    return home
