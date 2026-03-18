"""
M52H + M52H.1: Investor mission-control home — first-30-seconds hero, then depth.
"""

from __future__ import annotations

from workflow_dataset.investor_mission_control.models import MissionControlInvestorHome


def format_investor_mission_control_home(home: MissionControlInvestorHome) -> str:
    """M52H.1 default: hero → dual CTAs → role previews → memory story → trust → path."""
    lines: list[str] = []
    h = home.hero_30
    lines.append("══════════════════════════════════════════════════════════════")
    lines.append(f"  FIRST LOOK  ·  {h.eyebrow}")
    lines.append("══════════════════════════════════════════════════════════════")
    lines.append("")
    lines.append(f"  {h.headline}")
    lines.append(f"  {h.subline}")
    lines.append(f"  · {h.trust_chip}")
    lines.append("")
    fv = home.first_value
    lines.append("┌── YOUR NEXT MOVE ───────────────────────────────────────────┐")
    lines.append(f"│  {fv.headline}")
    lines.append(f"│  {fv.subcopy_tight or fv.why_this_matters[:100]}")
    lines.append("│")
    lines.append(f"│  $ {fv.command}")
    lines.append("└──────────────────────────────────────────────────────────────┘")
    lines.append("")
    ns = home.next_step_card
    lines.append("┌── THEN ──────────────────────────────────────────────────────┐")
    lines.append(f"│  {ns.label}")
    lines.append(f"│  $ {ns.command}")
    lines.append("└──────────────────────────────────────────────────────────────┘")
    lines.append("")
    lines.append("── Other roles (switch anytime) ──")
    for c in home.role_switch_previews.cards:
        mark = "●" if c.is_active else "○"
        lines.append(f"  {mark} {c.label}")
        lines.append(f"      {c.hook}")
        lines.append(f"      → {c.switch_command}")
    lines.append("")
    lines.append("── What it learned (bounded, on-device) ──")
    lines.append(f"  {home.memory.narrative_intro}")
    for ins in home.memory.insight_lines[:4]:
        lines.append(f"    · {ins}")
    bn = home.memory.bounded_note
    lines.append(f"  ({bn[:100]}…)" if len(bn) > 100 else f"  ({bn})")
    lines.append("")
    lines.append(f"── Active role ──  {home.role.active_role_label}  ·  {home.role.vertical_pack_display}")
    if home.role.role_one_liner:
        lines.append(f"  {home.role.role_one_liner[:180]}")
    lines.append("")
    ra = home.ready_surface
    tag = "✓" if ra.ready else "○"
    lines.append(f"── {tag} {ra.status_headline} ──")
    lines.append(f"  {ra.confirmation_plain[:220]}{'…' if len(ra.confirmation_plain) > 220 else ''}")
    lines.append("")
    lines.append("── Trust ──")
    lines.append(f"  {home.trust.headline} — {home.trust.body[:120]}{'…' if len(home.trust.body) > 120 else ''}")
    lines.append("")
    r = home.readiness
    lines.append(f"── Device ──  {r.headline}")
    lines.append("")
    lines.append("── Your path ──")
    for it in home.timeline.items:
        sym = "✓" if it.status == "done" else ("→" if it.status == "current" else "·")
        lines.append(f"  {sym} {it.label}")
    lines.append("")
    lines.append("── Investor flow ──")
    for step in home.narrative_flow_steps:
        lines.append(f"  {step}")
    lines.append("")
    if home.side_panel.inbox_summary:
        lines.append("── Inbox (optional) ──")
        lines.append(f"  {home.side_panel.inbox_summary}")
    lines.append("")
    lines.append(f"[dim]{home.generated_at_utc[:19]} UTC · mission-control (investor)[/dim]")
    return "\n".join(lines)


def format_investor_mission_control_home_classic(home: MissionControlInvestorHome) -> str:
    """Pre–M52H.1 layout (legacy)."""
    lines: list[str] = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║  OPERATOR HOME  —  local · private · guided                  ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    lines.append("")
    r = home.readiness
    lines.append(f"● Device  {r.headline}")
    lines.append("")
    lines.append("── Role ──")
    lines.append(f"  {home.role.active_role_label}")
    lines.append(f"  Pack: {home.role.vertical_pack_display}")
    if home.role.role_one_liner:
        lines.append(f"  {home.role.role_one_liner[:200]}")
    lines.append("")
    lines.append("── Memory (bounded demo) ──")
    lines.append(f"  {home.memory.headline}")
    for b in home.memory.what_learned_bullets[:4]:
        lines.append(f"    · {b}")
    bn = home.memory.bounded_note
    lines.append(f"  {bn}" if len(bn) <= 130 else f"  {bn[:127]}…")
    lines.append("")
    ra = home.ready_surface
    tag = "✓" if ra.ready else "○"
    lines.append(f"── {tag} {ra.status_headline} ──")
    lines.append(f"  {ra.confirmation_plain}")
    lines.append("")
    lines.append("── Next: first value ──")
    lines.append(f"  » {home.first_value.headline}")
    lines.append(f"    {home.first_value.why_this_matters}")
    lines.append(f"    Run: {home.first_value.command}")
    lines.append(f"    Then: {home.first_value.what_happens_next}")
    lines.append("")
    lines.append("── Trust ──")
    lines.append(f"  {home.trust.headline}")
    lines.append(f"  {home.trust.body}")
    lines.append("")
    lines.append("── Your path ──")
    for it in home.timeline.items:
        sym = "✓" if it.status == "done" else ("→" if it.status == "current" else "·")
        lines.append(f"  {sym} {it.label}")
    lines.append("")
    if home.side_panel.inbox_summary:
        lines.append("── Inbox (optional) ──")
        lines.append(f"  {home.side_panel.inbox_summary}")
    lines.append("")
    lines.append(f"[dim]Generated {home.generated_at_utc[:19]} UTC · investor mission-control view[/dim]")
    return "\n".join(lines)


def format_investor_mission_control_home_degraded(home: MissionControlInvestorHome) -> str:
    """Shorter layout when not ready-to-assist or blocked readiness."""
    if home.readiness.capability == "blocked":
        return (
            format_investor_mission_control_home(home)
            + "\nTip: run `workflow-dataset demo readiness` — copy bundle to disk if read-only USB blocked.\n"
        )
    if not home.ready_surface.ready:
        lines = [
            "══════════════════════════════════════════════════════════════",
            f"  SETUP FIRST  ·  {home.hero_30.eyebrow}",
            "══════════════════════════════════════════════════════════════",
            "",
            home.ready_surface.confirmation_plain,
            "",
            "  $ workflow-dataset demo onboarding sequence",
            "",
            "── After setup, you'll see: hero → first move → role previews ──",
            "",
        ]
        lines.append(format_investor_mission_control_home(home))
        return "\n".join(lines)
    return format_investor_mission_control_home(home)


def format_first_30_only(home: MissionControlInvestorHome) -> str:
    """Ultra-compact for presenter slide or second screen."""
    lines = [
        home.hero_30.headline,
        "",
        f"NEXT: {home.first_value.headline}",
        home.first_value.command,
        "",
        f"THEN: {home.next_step_card.command}",
        "",
        home.hero_30.trust_chip,
    ]
    return "\n".join(lines)
