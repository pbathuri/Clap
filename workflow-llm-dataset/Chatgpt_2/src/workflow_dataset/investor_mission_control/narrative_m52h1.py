"""
M52H.1: First-30-seconds hero copy, role previews, memory storytelling, tight CTAs.
"""

from __future__ import annotations

from typing import Any


def hero_eyebrow(ready_assist: bool, device_ok: bool) -> str:
    if ready_assist and device_ok:
        return "LOCAL · PRIVATE · READY"
    if device_ok:
        return "LOCAL · PRIVATE · SETUP"
    return "LOCAL · PRIVATE"


def hero_headline(ready_assist: bool) -> str:
    if ready_assist:
        return "Your operator shell is live — here's the highest-leverage move."
    return "Almost there — one short setup path unlocks the full picture."


def hero_subline(capability: str, role_label: str) -> str:
    base = f"Acting as: {role_label}."
    if capability == "degraded":
        return base + " Lightweight demo mode — no heavy model required."
    if capability == "blocked":
        return "Fix environment first (see tip at bottom), then return here."
    return base


def trust_chip(simulate_first: bool) -> str:
    return "Simulate-first · nothing runs without you" if simulate_first else "Approval-gated actions"


def build_memory_story(
    files_scanned: int,
    memory_units: int,
    context_hints: list[str],
    themes: list[str],
    priorities: list[str],
    bootstrapped: bool,
) -> tuple[str, list[str]]:
    """
    Polished 'what it learned' — sentences, not engineer prefixes.
    """
    if not bootstrapped and files_scanned == 0:
        return (
            "We haven't ingested samples yet.",
            ["Run demo memory bootstrap to show how bounded context works — capped files, stays on-device."],
        )
    intro = (
        f"We read {files_scanned} sample file{'s' if files_scanned != 1 else ''} and distilled "
        f"{memory_units} note{'s' if memory_units != 1 else ''} — enough to tailor the demo, not a full migration."
    )
    lines: list[str] = []
    if themes:
        lines.append(f"The samples keep coming back to: {themes[0]}.")
    elif context_hints:
        lines.append(f"Folder and naming hints suggest: {context_hints[0]}.")
    if priorities:
        lines.append(f"Lines that stood out: “{priorities[0][:90]}{'…' if len(priorities[0]) > 90 else ''}”")
    if len(themes) > 1:
        lines.append(f"Also: {themes[1]}.")
    if not lines:
        lines.append("Context is loaded; the shell can prioritize surfaces to match this role.")
    return intro, lines[:4]


def tight_first_value_subcopy(why: str) -> str:
    w = why.strip()
    if len(w) > 100:
        return w[:97] + "…"
    return w


def next_step_after_first_value(command: str) -> tuple[str, str]:
    """Label + command for the card after primary CTA."""
    low = (command or "").lower()
    if "workspace home" in low:
        return (
            "Then peek at day context",
            "workflow-dataset demo onboarding ready-state",
        )
    if "progress board" in low:
        return (
            "Then confirm assist state",
            "workflow-dataset demo onboarding ready-state",
        )
    return (
        "Then confirm you're ready to assist",
        "workflow-dataset demo onboarding ready-state",
    )


def build_role_switch_previews(active_preset_id: str) -> list[dict[str, Any]]:
    from workflow_dataset.demo_onboarding.presets import ROLE_PRESETS, list_role_preset_ids

    out: list[dict[str, Any]] = []
    for pid in list_role_preset_ids():
        p = ROLE_PRESETS[pid]
        hooks = {
            "founder_operator_demo": "Ops rhythm, inbox, daily priorities.",
            "document_review_demo": "Drafts, calm review, document flow.",
            "analyst_followup_demo": "Projects, follow-ups, structured queue.",
        }
        out.append(
            {
                "preset_id": pid,
                "label": p.label,
                "hook": hooks.get(pid, p.description[:50] + "…" if len(p.description) > 50 else p.description),
                "switch_command": f"workflow-dataset demo onboarding role --id {pid}",
                "is_active": pid == active_preset_id,
            }
        )
    return out


def investor_flow_lines(ready: bool) -> list[str]:
    """Updated narrative flow for doc / secondary panel."""
    if ready:
        return [
            "1. Glance hero + first move (above)",
            "2. Optional: switch role previews",
            "3. Run first-value command → then ready-state",
            "4. Trust stays simulate-first until you approve",
        ]
    return [
        "1. demo onboarding sequence",
        "2. Select role → bootstrap memory",
        "3. Return here for hero + first move",
    ]
