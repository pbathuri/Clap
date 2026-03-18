"""
M37E–M37H: Signal quality and calmness models.
Phase A: signal quality score, interruption cost, repeat/noise marker,
protected focus, low-value suggestion, suppressed item, resurfacing rule, stale-but-important.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SignalQualityScore(BaseModel):
    """Composite score for one item: urgency vs usefulness, noise, focus impact."""

    urgency: float = Field(default=0.5, ge=0, le=1, description="Must-see-now; never suppress above threshold")
    usefulness: float = Field(default=0.5, ge=0, le=1, description="Value when you have time")
    noise_score: float = Field(default=0.0, ge=0, le=1, description="Higher = more noisy/repetitive")
    interruption_cost: float = Field(default=0.5, ge=0, le=1, description="Cost to focus if shown now")
    is_urgent_tier: bool = Field(default=False, description="True => never suppress (blocked, approval, urgent)")
    reason: str = Field(default="", description="Short reason for score")


class InterruptionCost(BaseModel):
    """Estimated cost of interrupting the operator (context-dependent)."""

    cost: float = Field(default=0.5, ge=0, le=1)
    work_mode: str = Field(default="", description="focused | switching | idle | ...")
    focus_mode_active: bool = Field(default=False)
    reason: str = Field(default="")


class RepeatNoiseMarker(BaseModel):
    """Marks an item as repetitive or low-information (for suppression/grouping)."""

    item_id: str = Field(default="")
    source: str = Field(default="", description="queue | assist")
    pattern_key: str = Field(default="", description="e.g. type + reason_title hash")
    repeat_count: int = Field(default=0)
    last_seen_utc: str = Field(default="")
    suppress_until_utc: str = Field(default="", description="Optional cooldown")


class ProtectedFocusItem(BaseModel):
    """Current focus protection state (do not interrupt for non-urgent)."""

    active: bool = Field(default=False)
    project_id: str = Field(default="")
    work_mode: str = Field(default="")
    focus_mode_id: str = Field(default="", description="Portfolio active_focus_mode_id if any")
    allow_urgent_only: bool = Field(default=True, description="When True, only urgent_tier items pass")


class LowValueSuggestion(BaseModel):
    """Tag for suggestions that are low value in current context (can suppress or group)."""

    item_id: str = Field(default="")
    source: str = Field(default="assist")
    usefulness_below: float = Field(default=0.0)
    reason: str = Field(default="", description="e.g. low usefulness, off-project, repetitive")


class SuppressedQueueItem(BaseModel):
    """Record of a queue or assist item that was suppressed (for visibility/reports)."""

    item_id: str = Field(default="")
    source: str = Field(default="queue", description="queue | assist")
    suppressed_at_utc: str = Field(default="")
    reason: str = Field(default="", description="focus_safe | repeat | rate_cap | low_value | quiet_hours")
    urgency_tier: str = Field(default="", description="urgent | high | medium | low")
    resurfacing_eligible: bool = Field(default=False)
    explanation: str = Field(default="", description="M37H.1: Human-readable why held back, grouped, or resurfaced")


class ResurfacingRule(BaseModel):
    """When to resurface a previously suppressed or deferred item."""

    rule_id: str = Field(default="")
    name: str = Field(default="", description="e.g. stale_blocked_3d")
    condition: str = Field(default="", description="e.g. blocked and created_at older than 3 days")
    min_urgency: float = Field(default=0.0, ge=0, le=1)
    cooldown_hours: float = Field(default=24.0)
    description: str = Field(default="")


class StaleButImportantRule(BaseModel):
    """Stale-but-important: item is old but high impact (e.g. blocked > N days) -> resurface."""

    rule_id: str = Field(default="")
    min_age_hours: float = Field(default=72.0)
    required_section_or_kind: list[str] = Field(default_factory=lambda: ["blocked", "approval"])
    min_urgency_score: float = Field(default=0.5)
    description: str = Field(default="", description="e.g. Blocked/approval items older than 3 days resurface")


# ----- M37H.1 Calm queue profiles -----


class CalmQueueProfile(BaseModel):
    """Named profile: max visible, rate limits, noise ceiling, interruption threshold."""

    profile_id: str = Field(default="", description="e.g. focus | review | operator | default")
    label: str = Field(default="", description="Human-readable label")
    max_visible: int = Field(default=20, ge=1, le=100)
    max_suggestions_per_hour: int = Field(default=10, ge=0, le=60)
    noise_ceiling: float = Field(default=0.5, ge=0, le=1, description="Max noise_score to show; above = group or suppress")
    interrupt_threshold: float = Field(default=0.5, ge=0, le=1, description="Max interruption_cost to show")
    description: str = Field(default="")


# ----- M37H.1 Interruption budgets -----


class InterruptionBudget(BaseModel):
    """Budget of allowable interruptions per period (e.g. per hour or per day)."""

    budget_id: str = Field(default="", description="e.g. per_hour | per_day")
    period_hours: float = Field(default=1.0)
    max_interruptions: int = Field(default=15, ge=0)
    consumed: int = Field(default=0, ge=0)
    window_start_utc: str = Field(default="", description="Start of current window (ISO)")


# ----- M37H.1 Role/mode-based noise ceilings -----


class NoiseCeilingByRoleMode(BaseModel):
    """Noise ceiling and cap for a role or work mode."""

    role_or_mode: str = Field(default="", description="focused | review | operator | wrap_up | default")
    noise_ceiling: float = Field(default=0.5, ge=0, le=1)
    max_visible: int = Field(default=20, ge=1, le=100)
    label: str = Field(default="")


# ----- Config: never suppress these (safety) -----

ALWAYS_SHOW_PRIORITY: list[str] = [
    "urgent",
    "blocked",
    "approval_queue",
    "needs_approval",
]

NEVER_SUPPRESS_SOURCES: list[str] = [
    "approval_queue",
    "blocked_run",
]
