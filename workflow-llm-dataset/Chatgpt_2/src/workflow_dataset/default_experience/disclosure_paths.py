"""
M37D.1: Progressive disclosure paths — default -> advanced -> expert with clear "show me more" steps.
"""

from __future__ import annotations

from workflow_dataset.default_experience.models import (
    TIER_ADVANCED,
    TIER_DEFAULT,
    TIER_EXPERT,
    DisclosureStep,
)

# Tier order for display
TIER_ORDER: list[str] = [TIER_DEFAULT, TIER_ADVANCED, TIER_EXPERT]

# Ordered disclosure steps: default -> advanced -> expert (M37D.1)
PROGRESSIVE_DISCLOSURE_PATH: list[DisclosureStep] = [
    DisclosureStep(
        TIER_DEFAULT,
        TIER_ADVANCED,
        "Full workspace home (all areas)",
        "workflow-dataset workspace home",
    ),
    DisclosureStep(
        TIER_DEFAULT,
        TIER_ADVANCED,
        "See all day modes",
        "workflow-dataset day modes",
    ),
    DisclosureStep(
        TIER_DEFAULT,
        TIER_ADVANCED,
        "Mission control report",
        "workflow-dataset mission-control",
    ),
    DisclosureStep(
        TIER_DEFAULT,
        TIER_ADVANCED,
        "Queue list (all modes)",
        "workflow-dataset queue list",
    ),
    DisclosureStep(
        TIER_ADVANCED,
        TIER_EXPERT,
        "Trust cockpit",
        "workflow-dataset trust cockpit",
    ),
    DisclosureStep(
        TIER_ADVANCED,
        TIER_EXPERT,
        "Policy board",
        "workflow-dataset policy board",
    ),
    DisclosureStep(
        TIER_ADVANCED,
        TIER_EXPERT,
        "Operator mode",
        "workflow-dataset day mode --set operator_mode",
    ),
]


def get_progressive_disclosure_paths() -> list[dict]:
    """Return all disclosure steps as dicts for CLI/reports."""
    return [s.to_dict() for s in PROGRESSIVE_DISCLOSURE_PATH]


def get_show_more_commands(tier: str) -> list[DisclosureStep]:
    """Return steps that start from the given tier (e.g. 'default' -> show steps to advanced)."""
    tier = (tier or "").strip().lower()
    return [s for s in PROGRESSIVE_DISCLOSURE_PATH if s.from_tier == tier]


def get_disclosure_path_by_tier() -> dict[str, list[dict]]:
    """M37D.1: Group disclosure steps by from_tier for clearer display (default -> advanced -> expert)."""
    out: dict[str, list[dict]] = {t: [] for t in TIER_ORDER}
    for s in PROGRESSIVE_DISCLOSURE_PATH:
        ft = s.from_tier
        if ft in out:
            out[ft].append(s.to_dict())
    return out


def format_show_more_footer(profile_id: str = "") -> list[str]:
    """Format a short 'Show me more' footer for calm home. profile_id can tailor message."""
    steps = get_show_more_commands(TIER_DEFAULT)
    lines = ["[Show me more]"]
    if not steps:
        lines.append("  workflow-dataset defaults paths")
        return lines
    for i, s in enumerate(steps[:4], 1):
        lines.append(f"  {i}. {s.label}: {s.command}")
    lines.append("  All paths: workflow-dataset defaults paths")
    return lines
