"""
M32H.1: Quiet hours, focus-safe suppression, interruptibility policy.

Config models for: quiet hours (time windows), focus-safe rules,
interruptibility by work_mode, project_id, trust_level.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QuietHoursWindow(BaseModel):
    """One quiet-hours window (UTC). Times are HH:MM or ISO time."""
    start_utc: str = Field(default="22:00", description="Start time UTC (HH:MM)")
    end_utc: str = Field(default="07:00", description="End time UTC (HH:MM)")
    description: str = Field(default="", description="Optional label, e.g. 'Night quiet'")


class FocusSafeRule(BaseModel):
    """When focus-safe is on: suppress suggestions above interruptiveness or below confidence."""
    enabled: bool = Field(default=False, description="Apply focus-safe suppression")
    max_interruptiveness: float = Field(default=0.3, ge=0.0, le=1.0, description="Hide suggestions with interruptiveness > this")
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Hide suggestions with confidence < this")
    description: str = Field(default="", description="e.g. 'Only high-confidence, low-interrupt suggestions'")


class InterruptibilityRule(BaseModel):
    """One rule: when (work_mode, project_id, trust_level) match, allow level or suppress."""
    work_mode: str = Field(default="", description="focused | switching | interrupted | returning | idle | unknown | *")
    project_id: str = Field(default="", description="Project id or * for any")
    trust_level: str = Field(default="", description="trusted | simulate_only | approval_required | *")
    allow_suggestions: bool = Field(default=True, description="If False, hold back suggestions in this context")
    max_interruptiveness: float = Field(default=1.0, ge=0.0, le=1.0, description="Cap: hide suggestions above this in this context")
    hold_back_reason_template: str = Field(default="", description="e.g. 'Quiet focus mode for project {project_id}'")


class AssistPolicyConfig(BaseModel):
    """Full policy: quiet hours, focus-safe, interruptibility rules."""
    quiet_hours: list[QuietHoursWindow] = Field(default_factory=list)
    focus_safe: FocusSafeRule = Field(default_factory=FocusSafeRule)
    interruptibility_rules: list[InterruptibilityRule] = Field(default_factory=list)
    # If no rule matches, allow suggestion (default_hold_back = False)
    default_hold_back: bool = Field(default=False, description="When True, hold back unless a rule explicitly allows")

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AssistPolicyConfig:
        return cls(**d)
