"""
M51L.1: Degraded demo narrative bridge — keep the 5-minute arc honest without stopping the story.
"""

from __future__ import annotations

from workflow_dataset.investor_demo.models import DegradedDemoWarning


def degraded_narrative_bridge(warnings: list[DegradedDemoWarning]) -> str:
    """
    Single paragraph the presenter can read once at the top of degraded mode.
    Does not pretend green; continues the same staged narrative.
    """
    if not warnings:
        return ""
    parts = [
        "Quick transparency: this machine is in a degraded or thinner state than our best-case demo—",
        "I'll still walk you through the same five-minute arc so you see how the product behaves when honest about limits.",
    ]
    top = warnings[0].message[:120]
    parts.append(f"Main signal: {top}")
    if len(warnings) > 1:
        parts.append(f"Plus {len(warnings) - 1} other note(s)—we'll skip deep dives and stay on script.")
    else:
        parts.append("We'll stay on script and not oversell.")
    return " ".join(parts)


def degraded_beat_override_line(warnings: list[DegradedDemoWarning], beat_if_degraded: str) -> str:
    """Prefer beat's if_degraded_say; else append short acknowledgment."""
    if not warnings:
        return ""
    if beat_if_degraded.strip():
        return beat_if_degraded
    return "Acknowledge we're in degraded mode here, then continue with the same command—narrative stays intact."
