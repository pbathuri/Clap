"""
M37H.1: Calm queue profiles and role/mode-based noise ceilings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.signal_quality.models import (
    CalmQueueProfile,
    NoiseCeilingByRoleMode,
)


def get_default_profiles() -> list[CalmQueueProfile]:
    """Built-in calm queue profiles: focus, review, operator, wrap_up, default."""
    return [
        CalmQueueProfile(
            profile_id="focus",
            label="Focus",
            max_visible=10,
            max_suggestions_per_hour=4,
            noise_ceiling=0.3,
            interrupt_threshold=0.3,
            description="Minimal interruptions; only high-signal items.",
        ),
        CalmQueueProfile(
            profile_id="review",
            label="Review",
            max_visible=25,
            max_suggestions_per_hour=12,
            noise_ceiling=0.5,
            interrupt_threshold=0.5,
            description="Review mode: blocked and approval first, then rest.",
        ),
        CalmQueueProfile(
            profile_id="operator",
            label="Operator",
            max_visible=30,
            max_suggestions_per_hour=15,
            noise_ceiling=0.6,
            interrupt_threshold=0.6,
            description="Operator mode: grouped review, more items visible.",
        ),
        CalmQueueProfile(
            profile_id="wrap_up",
            label="Wrap-up",
            max_visible=20,
            max_suggestions_per_hour=10,
            noise_ceiling=0.5,
            interrupt_threshold=0.5,
            description="End-of-session: lower-urgency items allowed.",
        ),
        CalmQueueProfile(
            profile_id="default",
            label="Default",
            max_visible=20,
            max_suggestions_per_hour=10,
            noise_ceiling=0.5,
            interrupt_threshold=0.5,
            description="Default calm profile.",
        ),
    ]


def get_noise_ceilings_by_role_mode() -> list[NoiseCeilingByRoleMode]:
    """Role/mode-based noise ceilings for matching work_mode or queue view mode."""
    return [
        NoiseCeilingByRoleMode(role_or_mode="focused", noise_ceiling=0.3, max_visible=10, label="Focus"),
        NoiseCeilingByRoleMode(role_or_mode="review", noise_ceiling=0.5, max_visible=25, label="Review"),
        NoiseCeilingByRoleMode(role_or_mode="operator", noise_ceiling=0.6, max_visible=30, label="Operator"),
        NoiseCeilingByRoleMode(role_or_mode="wrap_up", noise_ceiling=0.5, max_visible=20, label="Wrap-up"),
        NoiseCeilingByRoleMode(role_or_mode="idle", noise_ceiling=0.7, max_visible=30, label="Idle"),
        NoiseCeilingByRoleMode(role_or_mode="default", noise_ceiling=0.5, max_visible=20, label="Default"),
    ]


def get_profile_for_role_mode(work_mode: str, profile_id_override: str = "") -> CalmQueueProfile:
    """Resolve the calm queue profile for the given work_mode (or explicit profile_id)."""
    profiles = {p.profile_id: p for p in get_default_profiles()}
    if profile_id_override and profile_id_override in profiles:
        return profiles[profile_id_override]
    w = (work_mode or "default").lower()
    if w in ("focused", "focus"):
        return profiles.get("focus", profiles["default"])
    if w == "review":
        return profiles.get("review", profiles["default"])
    if w == "operator":
        return profiles.get("operator", profiles["default"])
    if w in ("wrap_up", "wrap-up"):
        return profiles.get("wrap_up", profiles["default"])
    return profiles.get("default", get_default_profiles()[-1])


def get_noise_ceiling_for(work_mode: str, role: str = "") -> tuple[float, int]:
    """Return (noise_ceiling, max_visible) for the given work_mode or role."""
    ceilings = get_noise_ceilings_by_role_mode()
    key = (role or work_mode or "default").lower()
    for c in ceilings:
        if c.role_or_mode == key:
            return c.noise_ceiling, c.max_visible
    for c in ceilings:
        if c.role_or_mode == "default":
            return c.noise_ceiling, c.max_visible
    return 0.5, 20


def apply_profile_limits(
    max_visible: int,
    noise_ceiling: float,
    interrupt_threshold: float,
    profile: CalmQueueProfile | None = None,
) -> tuple[int, float, float]:
    """Apply profile limits; if profile given, use it; else use passed values."""
    if profile:
        return profile.max_visible, profile.noise_ceiling, profile.interrupt_threshold
    return max_visible, noise_ceiling, interrupt_threshold
